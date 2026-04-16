import os
import time
from src.collectors.link_collector import LinkCollector
from src.db.source_handler import SourceHandler
from src.db.duplicate_checker import DuplicateChecker
from src.parsers.article_parser import ArticleParser
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.db.postgres_handler import PostgresHandler
from src.config.logging import logger
from dotenv import load_dotenv


def ensure_tables_exist(postgres_handler):
    """Проверяет и создаёт таблицы, если их нет."""
    conn = postgres_handler.conn
    cursor = conn.cursor()

    # Проверяем существование таблиц
    cursor.execute("""
        SELECT to_regclass('public.data_sources') IS NOT NULL AS data_sources_exists,
               to_regclass('public.articles') IS NOT NULL AS articles_exists
    """)
    exists = cursor.fetchone()

    if not exists[0]:  # data_sources не существует
        logger.info("Создаём таблицу data_sources...")
        cursor.execute("""
            CREATE TABLE data_sources (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                url TEXT NOT NULL,
                source_type VARCHAR(20) NOT NULL
            CHECK (source_type IN ('website', 'rss')),
                is_active BOOLEAN DEFAULT TRUE,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()

    if not exists[1]:  # articles не существует
        logger.info("Создаём таблицу articles...")
        cursor.execute("""
            CREATE TABLE articles (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                normalized_url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                publish_date TIMESTAMP,
                embedding REAL[],
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(50) DEFAULT 'processed'
            )
        """)
        conn.commit()

    cursor.close()
    logger.info("Проверка таблиц завершена")

def populate_empty_data_sources(postgres_handler):
    """Заполняет таблицу data_sources тестовыми данными, если она пуста.

    Args:
        postgres_handler (PostgresHandler): экземпляр обработчика БД
    """
    conn = postgres_handler.conn
    cursor = conn.cursor()

    try:
        # Проверяем, пуста ли таблица data_sources
        cursor.execute("SELECT COUNT(*) FROM data_sources")
        count_sources = cursor.fetchone()[0]

        if count_sources == 0:
            logger.info("Таблица data_sources пуста. Заполняем тестовыми источниками...")

            # Тестовые источники данных: (name, url, source_type, priority)
            test_sources = [
                ('TechCrunch RSS', 'https://techcrunch.com/feed/', 'rss', 1),
                ('Habr RSS', 'https://habr.com/ru/rss/all/', 'rss', 2),
                ('BBC News', 'https://www.bbc.com/news', 'website', 3),
                ('The Guardian', 'https://www.theguardian.com', 'website', 4),
                ('Medium Tech', 'https://medium.com/tag/technology/feed', 'rss', 5),
                ('Wired RSS', 'https://www.wired.com/feed/rss', 'rss', 6),
                ('New York Times', 'https://www.nytimes.com', 'website', 7)
            ]

            inserted_count = 0
            for name, url, source_type, priority in test_sources:
                cursor.execute(
                    "INSERT INTO data_sources (name, url, source_type, priority) "
            "VALUES (%s, %s, %s, %s)",
            (name, url, source_type, priority)
        )
                inserted_count += 1

            conn.commit()
            logger.info(f"Добавлено {inserted_count} тестовых источников данных в таблицу data_sources")
        else:
            logger.info(f"Таблица data_sources уже содержит {count_sources} записей. Пропускаем заполнение тестовыми данными.")

    except psycopg2.Error as e:
        logger.error(f"Ошибка PostgreSQL при заполнении таблицы data_sources: {e}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при заполнении таблицы data_sources: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main_pipeline():
    """Основной пайплайн: берёт источники из БД, собирает ссылки, парсит, сохраняет."""
    load_dotenv()

    db_url = os.environ.get('DB_URL')
    postgres_handler = PostgresHandler(db_url)
    source_handler = SourceHandler(postgres_handler.conn)
    duplicate_checker = DuplicateChecker(postgres_handler)
    collector = LinkCollector()
    parser = ArticleParser()
    embedder = EmbeddingGenerator()

    try:
        # 0. Проверяем и создаём таблицы при необходимости
        ensure_tables_exist(postgres_handler)
        populate_empty_data_sources(postgres_handler)

        # 1. Получаем источники данных из БД
        logger.info("Получаем активные источники данных из БД...")
        sources = source_handler.get_active_sources()

        if not sources:
            logger.warning("Нет активных источников данных. Завершаем работу.")
            return

        # 2. Собираем ссылки из всех источников
        logger.info("Собираем ссылки из источников...")
        all_links = []

        for source in sources:
            source_name = source['name']
            source_url = source['url']
            source_type = source['source_type']

            logger.info(f"Обрабатываем источник: {source_name} ({source_type})")

            if source_type == 'rss':
                links = collector.collect_from_rss(source_url)
                all_links.extend(links)
            elif source_type == 'website':
                links = collector.collect_from_website(source_url)
                all_links.extend(links)

        logger.info(f"Всего собрано {len(all_links)} ссылок из {len(sources)} источников")

        # 3. Фильтрация дубликатов (уже существующих статей)
        logger.info("Фильтруем дубликаты...")
        new_links = [
            link for link in all_links
            if not duplicate_checker.is_duplicate(link['url'])
        ]
        logger.info(f"После фильтрации осталось {len(new_links)} новых ссылок")

        # 4. Парсинг новых статей
        parsed_articles = []
        for link in new_links:
            url = link['url']
            logger.info(f"Парсим статью: {url}")

            article_data = parser.parse_article(url)
            if article_data:
                # 5. Генерация эмбеддинга
                embedding = embedder.generate_embedding(
                    article_data['content'],
            article_data['title']
        )
                if embedding:
                    article_data['embedding'] = embedding
                    parsed_articles.append(article_data)
                else:
                    logger.warning(f"Не удалось сгенерировать эмбеддинг для: {url}")
            else:
                logger.warning(f"Ошибка парсинга: {url}")

        # 6. Сохранение в основную таблицу БД
        if parsed_articles:
            logger.info("Сохраняем новые статьи в основную таблицу БД...")
            postgres_handler.save_articles(parsed_articles)
            logger.info(f"Успешно сохранено {len(parsed_articles)} новых статей в БД")
        else:
            logger.info("Нет новых статей для сохранения в БД")

    except Exception as e:
        logger.error(f"Критическая ошибка в пайплайне: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        postgres_handler.close()

if __name__ == "__main__":
    while True:
        logger.info("Запуск пайплайна...")
        main_pipeline()
        logger.info("Ожидание 1 часа до следующего запуска...")
        time.sleep(3600)  # 3600 секунд = 1 час

import psycopg2
from src.config.logging import logger
from urllib.parse import urlparse, urlunparse

class PostgresHandler:
    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None
        self._connect()

    def _connect(self):
        """Устанавливает соединение с БД."""
        try:
            self.conn = psycopg2.connect(self.db_url)
            logger.info("Успешное подключение к PostgreSQL")
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    def normalize_url(self, url):
        """Нормализация URL для проверки дубликатов."""
        parsed = urlparse(url)
        normalized = parsed._replace(query='', fragment='')
        return urlunparse(normalized)

    def save_articles(self, articles_data, batch_size=100):
        """Сохраняет статьи с эмбеддингами в БД пакетами."""
        if not articles_data:
            logger.info("Нет статей для сохранения")
            return

        for i in range(0, len(articles_data), batch_size):
            batch = articles_data[i:i + batch_size]
            try:
                with self.conn.cursor() as cur:
                    for article in batch:
                        normalized_url = self.normalize_url(article['url'])
                        cur.execute("""
            INSERT INTO articles (
                url, normalized_url, title, content,
                publish_date, embedding, created_at, status
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            ON CONFLICT (normalized_url) DO UPDATE
            SET content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                status = EXCLUDED.status,
                updated_at = NOW()
        """, (
            article['url'],
            normalized_url,
            article['title'],
            article['content'],
            article.get('publish_date'),
            article['embedding'],
            article['status']
        ))
                self.conn.commit()
                logger.info(f"Сохранён пакет {i//batch_size + 1} ({len(batch)} статей")
            except Exception as e:
                logger.error(f"Ошибка сохранения пакета {i//batch_size + 1}: {e}")
                self.conn.rollback()

    def check_article_exists(self, url):
        """Проверяет, существует ли статья в основной таблице."""
        normalized_url = self.normalize_url(url)
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM articles WHERE normalized_url = %s",
                    (normalized_url,)
                )
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки существования статьи {url}: {e}")
            return False

    def close(self):
        """Закрывает соединение с БД."""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с БД закрыто")

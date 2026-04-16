from src.generation.article_generator import RAGArticleGenerator
from src.config.logging import logger
from src.database.init_db import SessionLocal

def main():
    # Инициализация
    db_session = SessionLocal()
    generator = RAGArticleGenerator(db_session)

    # Генерируем статью на основе топ‑тренда
    new_article = generator.generate_trend_based_article()

    if new_article:
        logger.info(f"Успешно сгенерирована статья:")
        logger.info(f"Заголовок: {new_article.title}")
        logger.info(f"Содержание: {new_article.content[:200]}...")
        logger.info(f"ID: {new_article.id}")
    else:
        logger.info("Не удалось сгенерировать статью")

if __name__ == "__main__":
    while True:
        logger.info("Запуск пайплайна...")
        main()
        logger.info("Ожидание 1 часа до следующего запуска...")
        time.sleep(3600)  # 3600 секунд = 1 час

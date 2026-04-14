from src.db.postgres_handler import PostgresHandler
from src.config.logging import logger

class DuplicateChecker:
    def __init__(self, postgres_handler: PostgresHandler):
        self.postgres_handler = postgres_handler

    def is_duplicate(self, url):
        """Проверяет, есть ли URL в основной таблице статей."""
        return self.postgres_handler.check_article_exists(url)

    def get_existing_urls(self, urls):
        """Возвращает список URL, которые уже есть в основной таблице."""
        existing = []
        for url in urls:
            if self.is_duplicate(url):
                existing.append(url)
        logger.info(f"Найдено {len(existing)} дубликатов из {len(urls)} URL")
        return existing

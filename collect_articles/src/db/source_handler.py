import psycopg2
from src.config.logging import logger

class SourceHandler:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_active_sources(self):
        """Получает активные источники данных."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT name, url, source_type
            FROM data_sources
            WHERE is_active = TRUE
            ORDER BY priority DESC, created_at ASC
        """)
                results = cur.fetchall()
                logger.info(f"Получено {len(results)} активных источников")
                return [
                    {'name': row[0], 'url': row[1], 'source_type': row[2]}
            for row in results
        ]
        except Exception as e:
            logger.error(f"Ошибка получения источников данных: {e}")
            return []

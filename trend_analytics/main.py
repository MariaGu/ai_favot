import time
from src.analysis.trend_cluster_analyzer import TrendClusterAnalyzer
from src.config.logging import logger
from dotenv import load_dotenv

def main():
    load_dotenv()
    logger.info("Запуск приложения анализа трендов с PostgreSQL")

    logger.info("Инициализация анализатора трендов...")
    analyzer = TrendClusterAnalyzer()
    logger.info("Модель sentence-transformers загружена")

    # Запускаем анализ за последние 24 часа
    trends = analyzer.analyze_trends(hours=124)

    logger.info(f"Анализ завершён. Найдено {len(trends)} трендов")

if __name__ == "__main__":
    while True:
        logger.info("Запуск пайплайна...")
        main()
        logger.info("Ожидание 1 часа до следующего запуска...")
        time.sleep(3600)  # 3600 секунд = 1 час


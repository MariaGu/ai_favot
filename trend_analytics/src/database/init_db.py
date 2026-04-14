from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from dotenv import load_dotenv
import os
from src.config.logging import logger 

# Загружаем переменные из .env файла
load_dotenv()

def get_database_url():
    """Получает URL базы данных из переменных окружения."""
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError("DATABASE_URL не установлен в переменных окружения")
    return db_url

def create_tables(engine):
    """Создаёт все таблицы в базе данных."""
    Base.metadata.create_all(engine)
    logger.info("Все таблицы успешно созданы в PostgreSQL!")

def init_database():
    """Инициализирует базу данных: создаёт движок и таблицы."""
    database_url = get_database_url()
    logger.info(f"Подключение к PostgreSQL: {database_url}")

    # Создаём движок SQLAlchemy
    engine = create_engine(database_url)

    # Создаём все таблицы
    create_tables(engine)

    # Создаём фабрику сессий
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, SessionLocal

# Глобальные переменные для использования в приложении
engine, SessionLocal = init_database()

from app.database import engine, Base
from app.models import User
from passlib.context import CryptContext
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_tables():
    Base.metadata.create_all(bind=engine)

def create_test_user():
    session = Session(bind=engine)
    # Проверяем, есть ли уже пользователь admin
    existing_user = session.query(User).filter(User.username == "admin").first()
    if not existing_user:
        hashed_password = pwd_context.hash("admin123")
        test_user = User(username="admin", hashed_password=hashed_password)
        session.add(test_user)
        session.commit()
        print("Тестовый пользователь создан: admin / admin123")
    else:
        print("Пользователь admin уже существует")
    session.close()

if __name__ == "__main__":
    create_tables()
    create_test_user()

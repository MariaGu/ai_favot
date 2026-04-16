from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router
from app.database import Base, engine
from app import models
from dotenv import load_dotenv

load_dotenv()
# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)

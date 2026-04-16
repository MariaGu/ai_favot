FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . /app

# Экспонируем порт (порт подберите под ваш модуль)
EXPOSE 5000

# Команда для запуска приложения (адаптируйте под точку входа вашего модуля)
CMD ["python", "main.py"]

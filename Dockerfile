# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /usr/src/app

# Устанавливаем переменные окружения, чтобы Python не создавал .pyc файлы
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем системные зависимости, если они нужны
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения в рабочую директорию
COPY . .

# Указываем команду для запуска приложения
CMD ["python", "-m", "app.main"]


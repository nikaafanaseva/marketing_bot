# Используем стабильную версию Python 3.12
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY bot.py .

# Открываем порт (Render сам передаст PORT)
EXPOSE 8000

# Команда запуска
CMD ["python", "bot.py"]

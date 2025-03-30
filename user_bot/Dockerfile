FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
COPY main.py ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуска бота
CMD ["python", "main.py"]

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Створення директорій для оновлень
RUN mkdir -p static/updates/android static/updates/windows static/updates/linux

# Відкриття порту
EXPOSE 8000

# Запуск сервера
CMD ["python", "run_server.py"]

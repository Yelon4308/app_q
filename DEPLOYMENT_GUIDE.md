# 🌐 Развертывание Drawing Sync Server

## 🚀 Варианты хостинга

### 1. **DigitalOcean Droplet (Рекомендуется)**

#### Создание сервера:
1. Зарегистрируйтесь на DigitalOcean
2. Создайте Droplet:
   - Ubuntu 22.04 LTS
   - Basic план - $6/месяц (1GB RAM)
   - Выберите регион ближе к пользователям

#### Настройка сервера:
```bash
# Подключение к серверу
ssh root@your-server-ip

# Обновление системы
apt update && apt upgrade -y

# Установка Python и зависимостей
apt install python3 python3-pip nginx supervisor git -y

# Клонирование проекта
git clone https://github.com/your-username/drawing-sync-server.git
cd drawing-sync-server

# Установка зависимостей
pip3 install -r requirements.txt

# Создание пользователя для приложения
useradd --system --shell /bin/false drawingapp
chown -R drawingapp:drawingapp /root/drawing-sync-server
```

#### Настройка Supervisor:
```bash
# Создаем конфиг для автозапуска
nano /etc/supervisor/conf.d/drawingapp.conf
```

Содержимое файла:
```ini
[program:drawingapp]
command=/usr/bin/python3 main.py
directory=/root/drawing-sync-server
user=drawingapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/drawingapp.log
```

#### Настройка Nginx:
```bash
nano /etc/nginx/sites-available/drawingapp
```

Содержимое:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Или IP адрес

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Активация:
```bash
ln -s /etc/nginx/sites-available/drawingapp /etc/nginx/sites-enabled/
nginx -t  # Проверка конфигурации
systemctl restart nginx
systemctl restart supervisor
```

### 2. **Heroku (Простой вариант)**

#### Подготовка для Heroku:
Создайте файл `Procfile`:
```
web: python main.py --host 0.0.0.0 --port $PORT
```

Создайте `runtime.txt`:
```
python-3.9.22
```

Обновите `main.py` для Heroku:
```python
import os
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
```

Деплой:
```bash
# Установка Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

heroku create your-app-name
git add .
git commit -m "Deploy drawing sync server"
git push heroku main
```

### 3. **Railway.app (Современный вариант)**

1. Зарегистрируйтесь на Railway.app
2. Подключите GitHub репозиторий
3. Railway автоматически определит Python проект
4. Настройте переменные окружения при необходимости

### 4. **VPS с панелью управления**

Провайдеры:
- **Timeweb** (русский)
- **reg.ru** 
- **Beget**

## 🔒 Настройка домена и SSL

### Получение бесплатного SSL:
```bash
# Установка Certbot
apt install certbot python3-certbot-nginx -y

# Получение сертификата
certbot --nginx -d your-domain.com

# Автообновление
crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📱 Обновление клиентских приложений

### Изменение URL в клиентах:
```python
# Вместо localhost используйте ваш домен
sync_client = DrawingSyncClient(
    server_url="wss://your-domain.com",  # wss для HTTPS
    room_id="my_room"
)

update_checker = UpdateChecker(
    server_url="https://your-domain.com",
    platform="android"
)
```

## 🧪 Тестирование продакшен сервера

```python
import requests
import websockets
import asyncio

# Тест API
def test_production_api():
    base_url = "https://your-domain.com"
    
    response = requests.get(f"{base_url}/api/status")
    print("API Status:", response.json())
    
    response = requests.get(f"{base_url}/api/rooms/")
    print("Rooms:", response.json())

# Тест WebSocket
async def test_production_websocket():
    uri = "wss://your-domain.com/ws/test_room"
    
    async with websockets.connect(uri) as websocket:
        await websocket.send('{"type": "drawing", "x": 100, "y": 200}')
        response = await websocket.recv()
        print("WebSocket response:", response)

# Запуск тестов
test_production_api()
asyncio.run(test_production_websocket())
```

## 💡 Рекомендации по безопасности

1. **Ограничение загрузки файлов**:
```python
# Добавьте в api/updates.py
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.apk', '.exe', '.appimage'}
```

2. **Rate limiting**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/status")
@limiter.limit("10/minute")
async def get_status(request: Request):
    # ... код
```

3. **Логирование**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
```

## 📊 Мониторинг

### Простая система мониторинга:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### Внешний мониторинг:
- **UptimeRobot** - бесплатный мониторинг доступности
- **Pingdom** - мониторинг производительности

## 🚀 Следующие шаги после деплоя

1. Обновите URL в ваших Kivy приложениях
2. Протестируйте синхронизацию между устройствами
3. Загрузите первые версии приложений через API
4. Настройте автоматическую сборку и деплой
5. Добавьте аналитику использования

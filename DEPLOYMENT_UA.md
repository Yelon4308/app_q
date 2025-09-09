"""
Інструкції з розгортання сервера синхронізації
для додатку "Штаб на пожежі"
"""

## Розгортання на VPS (Ubuntu)

### 1. Встановлення необхідних пакетів
```bash
sudo apt update
sudo apt install -y python3 python3-pip nginx certbot python3-certbot-nginx git ufw
```

### 2. Клонування репозиторію
```bash
cd /opt
sudo git clone https://github.com/your-username/drawing-sync-server.git
cd drawing-sync-server
sudo chown -R $USER:$USER .
```

### 3. Встановлення залежностей Python
```bash
pip3 install -r requirements.txt
```

### 4. Налаштування Firewall
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

### 5. Створення systemd сервісу

Створіть файл `/etc/systemd/system/drawing-sync.service`:
```ini
[Unit]
Description=Drawing Sync Server
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/drawing-sync-server
ExecStart=/usr/bin/python3 run_server.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/drawing-sync-server

[Install]
WantedBy=multi-user.target
```

### 6. Налаштування Nginx як проксі

Створіть файл `/etc/nginx/sites-available/drawing-sync.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket підтримка
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Створіть символічне посилання і перезапустіть Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/drawing-sync.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Налаштування SSL з Let's Encrypt
```bash
sudo certbot --nginx -d your-domain.com
```

### 8. Запуск сервісу
```bash
sudo systemctl start drawing-sync
sudo systemctl enable drawing-sync
sudo systemctl status drawing-sync
```

### 9. Перевірка роботи
Відкрийте у браузері: `https://your-domain.com`

## Розгортання через Docker (альтернативний варіант)

### 1. Підготовка Docker і Docker Compose
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Клонування репозиторію
```bash
git clone https://github.com/your-username/drawing-sync-server.git
cd drawing-sync-server
```

### 3. Запуск через Docker Compose
```bash
docker-compose up -d
```

### 4. Перевірка статусу
```bash
docker-compose ps
docker-compose logs -f
```

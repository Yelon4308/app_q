# 📱 Интеграция Drawing Sync Server с Kivy приложением

## 🎯 Общая архитектура

```
┌─────────────────┐    WebSocket     ┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Android App   │◄─────────────────┤  Drawing Sync   ├─────────────────►│    PC App       │
│    (Kivy)       │                  │     Server      │                  │   (Kivy)        │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
        │                                     │                                     │
        │ HTTP API                           │                            HTTP API │
        │ (Updates)                          │                           (Updates) │
        └────────────────────────────────────┼─────────────────────────────────────┘
                                            │
                                    ┌─────────────────┐
                                    │   SQLite DB     │
                                    │  + File Storage │
                                    └─────────────────┘
```

## 🔧 Шаги интеграции

### 1. Добавьте зависимости в ваш проект

```python
# requirements.txt
websockets==12.0
requests==2.31.0
asyncio==3.4.3  # для старых версий Python
aiohttp==3.8.5  # альтернатива requests для async
```

### 2. Создайте класс синхронизации

Скопируйте файл `kivy_integration.py` в ваш проект и адаптируйте под ваше приложение.

### 3. Интеграция с Kivy Widget

```python
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
import asyncio
import threading

from kivy_integration import DrawingSyncClient, UpdateChecker

class DrawingWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Инициализация синхронизации
        self.sync_client = DrawingSyncClient(
            server_url="ws://your-server-ip:8000",  # Замените на ваш IP
            room_id="drawing_room"
        )
        
        # Настройка callbacks
        self.sync_client.set_callback('on_drawing', self.on_remote_drawing)
        self.sync_client.set_callback('on_clear', self.on_remote_clear)
        
        # Переменные для рисования
        self.current_line = None
        self.is_drawing = False
        
        # Запуск синхронизации
        self.start_sync()
        
        # Привязка событий
        self.bind(on_touch_down=self.on_touch_down)
        self.bind(on_touch_move=self.on_touch_move)
        self.bind(on_touch_up=self.on_touch_up)
    
    def start_sync(self):
        """Запуск синхронизации в отдельном потоке"""
        def run_sync():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.sync_client.connect())
        
        sync_thread = threading.Thread(target=run_sync, daemon=True)
        sync_thread.start()
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_drawing = True
            with self.canvas:
                Color(1, 0, 0)  # Красный цвет
                self.current_line = Line(points=[touch.x, touch.y], width=3)
            
            # Отправляем команду на сервер
            asyncio.run_coroutine_threadsafe(
                self.sync_client.send_drawing_command(
                    touch.x, touch.y, "down", "#FF0000", 3, "brush"
                ),
                self.sync_client.loop if hasattr(self.sync_client, 'loop') else asyncio.get_event_loop()
            )
            
            return True
        return False
    
    def on_touch_move(self, touch):
        if self.is_drawing and self.collide_point(*touch.pos):
            if self.current_line:
                self.current_line.points += [touch.x, touch.y]
            
            # Отправляем команду на сервер
            asyncio.run_coroutine_threadsafe(
                self.sync_client.send_drawing_command(
                    touch.x, touch.y, "draw", "#FF0000", 3, "brush"
                ),
                self.sync_client.loop if hasattr(self.sync_client, 'loop') else asyncio.get_event_loop()
            )
            
            return True
        return False
    
    def on_touch_up(self, touch):
        if self.is_drawing:
            self.is_drawing = False
            self.current_line = None
            
            # Отправляем команду завершения
            asyncio.run_coroutine_threadsafe(
                self.sync_client.send_drawing_command(
                    touch.x, touch.y, "up", "#FF0000", 3, "brush"
                ),
                self.sync_client.loop if hasattr(self.sync_client, 'loop') else asyncio.get_event_loop()
            )
            
            return True
        return False
    
    def on_remote_drawing(self, drawing_data):
        """Обработка рисования от других пользователей"""
        def apply_drawing():
            with self.canvas:
                Color(*self.hex_to_rgb(drawing_data.get('color', '#000000')))
                
                if drawing_data['action'] == 'down':
                    self.remote_line = Line(
                        points=[drawing_data['x'], drawing_data['y']], 
                        width=drawing_data.get('size', 3)
                    )
                elif drawing_data['action'] == 'draw' and hasattr(self, 'remote_line'):
                    self.remote_line.points += [drawing_data['x'], drawing_data['y']]
                elif drawing_data['action'] == 'up':
                    self.remote_line = None
        
        # Выполняем в главном потоке
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: apply_drawing(), 0)
    
    def on_remote_clear(self):
        """Очистка холста от сервера"""
        def clear_canvas():
            self.canvas.clear()
        
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: clear_canvas(), 0)
    
    def clear_canvas(self):
        """Локальная очистка холста"""
        self.canvas.clear()
        asyncio.run_coroutine_threadsafe(
            self.sync_client.clear_canvas(),
            self.sync_client.loop if hasattr(self.sync_client, 'loop') else asyncio.get_event_loop()
        )
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """Конвертация HEX в RGB для Kivy"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

class DrawingApp(App):
    def build(self):
        # Основной layout
        root = BoxLayout(orientation='vertical')
        
        # Виджет для рисования
        drawing_widget = DrawingWidget(size_hint=(1, 0.9))
        
        # Панель управления
        controls = BoxLayout(size_hint=(1, 0.1), orientation='horizontal')
        
        clear_btn = Button(text='Очистить', size_hint=(0.3, 1))
        clear_btn.bind(on_press=lambda x: drawing_widget.clear_canvas())
        
        update_btn = Button(text='Проверить обновления', size_hint=(0.4, 1))
        update_btn.bind(on_press=self.check_updates)
        
        controls.add_widget(clear_btn)
        controls.add_widget(update_btn)
        
        root.add_widget(drawing_widget)
        root.add_widget(controls)
        
        # Сохраняем ссылку для проверки обновлений
        self.drawing_widget = drawing_widget
        
        return root
    
    def check_updates(self, instance):
        """Проверка обновлений"""
        platform = "android"  # или определите автоматически
        update_checker = UpdateChecker(
            server_url="http://your-server-ip:8000",
            platform=platform
        )
        
        def check_in_thread():
            update_info = update_checker.check_for_updates("1.0.0")  # Ваша текущая версия
            
            if update_info and update_info.get("has_update"):
                # Показать диалог обновления
                print(f"Доступно обновление: {update_info['latest_version']}")
                
                # Здесь можно показать Popup с предложением обновиться
                # self.show_update_dialog(update_info)
            else:
                print("У вас последняя версия")
        
        threading.Thread(target=check_in_thread, daemon=True).start()

if __name__ == '__main__':
    DrawingApp().run()
```

## 🚀 Настройка сервера

### 1. Запуск сервера на VPS/облаке

```bash
# На сервере
git clone your-repo
cd drawing-sync-server
pip install -r requirements.txt
python run_server.py --host 0.0.0.0 --port 8000
```

### 2. Настройка Nginx (рекомендуется)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 📦 Система обновлений

### 1. Загрузка новой версии на сервер

```bash
# Через API (нужна авторизация в реальном проекте)
curl -X POST "http://your-server:8000/api/updates/upload/android" \
  -F "version=1.1.0" \
  -F "release_notes=Исправлены ошибки и добавлены новые функции" \
  -F "is_required=false" \
  -F "file=@app-release-1.1.0.apk"
```

### 2. Автопроверка обновлений в приложении

```python
class UpdateManager:
    def __init__(self, app_version, platform, server_url):
        self.app_version = app_version
        self.platform = platform
        self.server_url = server_url
    
    def auto_check_updates(self):
        """Автоматическая проверка обновлений при запуске"""
        try:
            response = requests.get(
                f"{self.server_url}/api/updates/check/{self.platform}",
                params={"current_version": self.app_version},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("has_update"):
                    self.show_update_notification(data)
                    
        except Exception as e:
            print(f"Ошибка проверки обновлений: {e}")
    
    def show_update_notification(self, update_info):
        """Показать уведомление об обновлении"""
        # Реализуйте Popup или уведомление в Kivy
        pass
```

## 🔒 Безопасность

### 1. Ограничение доступа к загрузке обновлений

```python
# В api/updates.py добавьте авторизацию
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/upload/{platform}")
async def upload_update(
    platform: str,
    token: str = Depends(security),
    # ... остальные параметры
):
    # Проверка токена
    if not verify_admin_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недостаточно прав"
        )
    # ... остальная логика
```

### 2. Валидация размера файлов

```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

@router.post("/upload/{platform}")
async def upload_update(file: UploadFile = File(...)):
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Файл слишком большой"
        )
```

## 📊 Мониторинг

### 1. Логирование

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('drawing_sync.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Метрики

```python
# Добавьте счетчики
connected_users = 0
total_drawings = 0
total_updates_downloaded = 0

@app.get("/api/metrics")
async def get_metrics():
    return {
        "connected_users": connected_users,
        "total_drawings": total_drawings,
        "total_updates_downloaded": total_updates_downloaded,
        "uptime": time.time() - start_time
    }
```

## 🔄 Запуск в продакшене

```bash
# Используйте systemd для автозапуска
sudo systemctl create /etc/systemd/system/drawing-sync.service

[Unit]
Description=Drawing Sync Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/server
ExecStart=/usr/bin/python3 run_server.py
Restart=always

[Install]
WantedBy=multi-user.target

# Активация
sudo systemctl enable drawing-sync
sudo systemctl start drawing-sync
```

## 🧪 Тестирование

1. Откройте `demo/drawing_demo.html` в браузере
2. Подключитесь к тестовой комнате
3. Откройте вторую вкладку для тестирования синхронизации
4. Рисуйте и наблюдайте синхронизацию

Это базовая интеграция, которую можно расширить под ваши конкретные потребности!

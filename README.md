# Drawing Sync Server

Сервер для синхронизации рисования в реальном времени между Android (Kivy) и PC версиями приложения.

## 🚀 Возможности

- **Real-time синхронизация** рисования через WebSocket
- **Географические координаты** для точной синхронизации между устройствами с разными экранами
- **Система обновлений** для Android APK, Windows EXE и Linux AppImage
- **Комнаты** для группировки пользователей
- **Шаблоны** для быстрого добавления элементов
- **REST API** для управления и мониторинга
- **SQLite база данных** для хранения данных

## 📋 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск сервера
```bash
python main.py
```
Сервер будет доступен по адресу: `http://localhost:8000`

### 3. Тестирование
- Откройте `demo/drawing_demo.html` в браузере
- Подключитесь к комнате и попробуйте рисовать
- Откройте вторую вкладку для тестирования синхронизации

## 🔌 Интеграция с Kivy приложением

Используйте файл `kivy_integration.py` как основу:

```python
from kivy_integration import DrawingSyncClient, UpdateChecker

# В вашем Kivy приложении
sync_client = DrawingSyncClient(
    server_url="ws://your-server:8000",
    room_id="drawing_room"
)

# Настройка callbacks
sync_client.set_callback('on_drawing', self.on_remote_drawing)
sync_client.run_in_thread()

# Отправка команд рисования
sync_client.send_drawing_command(x, y, "draw", "#FF0000", 5, "brush")
```

## 🌐 Развертывание в продакшене

Смотрите подробную инструкцию в `DEPLOYMENT_GUIDE.md`:
- DigitalOcean Droplet
- Heroku
- Railway.app
- Настройка домена и SSL

## 📦 Загрузка обновлений приложений

```bash
# Загрузка новой версии Android
python upload_app.py upload --platform android --version 1.1.0 --file app.apk --notes "Исправления ошибок"

# Проверка последних версий
python upload_app.py check
```

## 🔄 API Endpoints

### WebSocket
- `ws://localhost:8000/ws/{room_id}` - Подключение к комнате

### REST API
- `GET /api/status` - Статус сервера
- `GET /api/updates/check/{platform}?current_version=1.0.0` - Проверка обновлений
- `GET /api/updates/download/{platform}` - Скачивание обновления
- `POST /api/updates/upload/{platform}` - Загрузка нового обновления
- `GET /api/rooms/` - Список всех комнат
- `GET /api/rooms/{room_id}` - Информация о комнате

## 📊 Мониторинг

Статистика сервера: `GET /api/status`
```json
{
  "status": "online",
  "connected_clients": 15,
  "active_rooms": 3,
  "timestamp": "2025-08-23T10:30:00"
}
```

## 🧪 Файлы для изучения

- `main.py` - Основной сервер FastAPI
- `websocket_handler.py` - Управление WebSocket соединениями  
- `database.py` - Работа с SQLite базой данных
- `kivy_integration.py` - Готовый код для интеграции с Kivy
- `demo/drawing_demo.html` - Веб-демо для тестирования
- `INTEGRATION_GUIDE.md` - Подробное руководство по интеграции
- `DEPLOYMENT_GUIDE.md` - Инструкции по развертыванию

## � Безопасность

⚠️ **Важно для продакшена:**
- Добавьте аутентификацию для upload endpoints
- Ограничьте размер загружаемых файлов
- Используйте HTTPS/WSS
- Настройте rate limiting
- Валидируйте типы файлов

## � Следующие шаги

1. ✅ **Сервер создан и работает локально**
2. 🔄 **Интегрируйте с вашим Kivy приложением**
3. 🌐 **Разверните сервер в облаке** 
4. 📱 **Обновите URL в клиентских приложениях**
5. 📦 **Загрузите первые версии для обновления**
6. 🧪 **Протестируйте синхронизацию между устройствами**

Удачи с вашим проектом! 🎨

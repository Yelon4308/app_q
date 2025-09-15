# Оновлення серверу для підтримки подій малювання

## Виконані зміни

1. **Додано модель для подій малювання**:
   - `models/drawing_event.py` - модель для стандартизованих подій

2. **Оновлено базу даних**:
   - Додано таблицю `drawing_events` для зберігання подій малювання
   - Створено методи для роботи з подіями у `database.py`
   - Оновлено скрипт ініціалізації бази даних в `init_db()`
   - Створено скрипт міграції `migrate_db.py`

3. **Додано API для роботи з подіями**:
   - `api/events.py` - ендпоінти для CRUD-операцій з подіями
   - Інтеграція API в `main.py`

4. **Оновлено WebSocket-обробник**:
   - Додано підтримку повідомлень типу `drawing_event` в `main.py`

5. **Додано документацію**:
   - `SERVER_UPDATE_GUIDE.md` - інструкція з оновлення сервера
   - `DRAWING_EVENT_PROTOCOL.md` - опис протоколу подій малювання

6. **Підготовка до розгортання**:
   - Оновлено `run_server.py` для виконання міграції бази даних

7. **Створено тестовий скрипт**:
   - `test_drawing_events.py` - скрипт для тестування нової функціональності

## Запуск оновленого сервера

1. Міграція бази даних:
   ```
   python migrate_db.py
   ```

2. Запуск сервера:
   ```
   python run_server.py
   ```

3. Тестування функціональності:
   ```
   python test_drawing_events.py
   ```

## Перевірка API

Для перевірки API можна використовувати curl або інструмент типу Postman:

```bash
# Отримання всіх подій в кімнаті
curl -X GET http://localhost:8000/api/events/test-room

# Створення нової події
curl -X POST http://localhost:8000/api/events/test-room \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-event-001",
    "event_name": "Тестова подія",
    "drawing_type": "polygon",
    "action": "add_point",
    "platform": "test",
    "timestamp": "2023-09-15T12:34:56Z",
    "style": {
      "color": "#FF0000",
      "width": 2.0,
      "fill": true,
      "opacity": 0.5
    },
    "data": {
      "lat": 48.12345,
      "lon": 30.67890
    }
  }'

# Отримання конкретної події
curl -X GET http://localhost:8000/api/events/test-room/test-event-001

# Видалення події
curl -X DELETE http://localhost:8000/api/events/test-room/test-event-001
```

## Наступні кроки

1. Оновити клієнтську частину для роботи з подіями малювання
2. Протестувати взаємодію між клієнтами Android і Windows
3. Додати підтримку групування подій за назвою
4. Впровадити механізм вирішення конфліктів для офлайн-режиму

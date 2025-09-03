# Інтеграція з географічними координатами для Drawing Sync

## Огляд оновленого протоколу

З цим оновленням протоколу синхронізації малювання, ми додали підтримку географічних координат для більш точної синхронізації між пристроями з різними екранами та налаштуваннями карти.

## Структура повідомлень

### Надсилання команд малювання з географічними координатами

```json
{
  "type": "drawing_event",
  "data": {
    "event_type": "draw", // "down", "move", "up"
    "lat": 50.4501,       // широта
    "lon": 30.5234,       // довгота
    "is_geographical": true,
    "x": 0.0,             // не використовується при is_geographical=true
    "y": 0.0,             // не використовується при is_geographical=true
    "color": "#FF0000",
    "brush_size": 5,
    "tool": "pencil"
  }
}
```

### Назад-сумісна підтримка

Для забезпечення назад-сумісності, сервер продовжує обробляти повідомлення у старому форматі:

```json
{
  "type": "drawing",
  "x": 100,
  "y": 100,
  "action": "draw",
  "color": "#000000",
  "size": 5,
  "tool": "brush"
}
```

## Оновлення бази даних

Для підтримки географічних координат додано нові поля в таблиці `drawing_commands`:

- `lat` - широта (від -90 до 90)
- `lon` - довгота (від -180 до 180)
- `is_geographical` - прапорець, що вказує на тип координат (географічні чи екранні)

Запустіть скрипт міграції, щоб оновити структуру бази даних:

```bash
python migrate_db.py
```

## Інтеграція в клієнтські додатки

### 1. Відправка координат з клієнта

```python
def send_drawing(lat, lon, event_type, color="#000000", brush_size=5, tool="pencil"):
    """
    Відправка команди малювання з географічними координатами
    
    Args:
        lat (float): Широта
        lon (float): Довгота
        event_type (str): Тип події ('draw', 'down', 'up')
        color (str): Колір у форматі HEX
        brush_size (int): Розмір пензля
        tool (str): Тип інструменту
    """
    # Перевірка валідності географічних координат
    is_geographical = (-90 <= lat <= 90) and (-180 <= lon <= 180)
    
    if is_geographical:
        message = {
            "type": "drawing_event",
            "data": {
                "event_type": event_type,
                "lat": lat,
                "lon": lon,
                "is_geographical": True,
                "x": 0.0,
                "y": 0.0,
                "color": color,
                "brush_size": brush_size,
                "tool": tool
            }
        }
    else:
        # Запасний варіант для неправильних координат
        message = {
            "type": "drawing_event",
            "data": {
                "event_type": event_type,
                "x": lat,  # використовуємо як x-координату
                "y": lon,  # використовуємо як y-координату
                "is_geographical": False,
                "color": color,
                "brush_size": brush_size,
                "tool": tool
            }
        }
    
    # Відправка повідомлення
    websocket.send_json(message)
```

### 2. Обробка координат на клієнті

```python
def handle_drawing_event(data):
    """
    Обробка події малювання
    
    Args:
        data (dict): Дані події малювання
    """
    # Перевіряємо наявність географічних координат
    if "lat" in data and "lon" in data and data.get("is_geographical", False):
        lat = data["lat"]
        lon = data["lon"]
        
        # Перевіряємо валідність координат
        if lat is not None and lon is not None and (-90 <= lat <= 90) and (-180 <= lon <= 180):
            # Конвертуємо географічні координати в екранні для відображення
            x, y = mapview.get_window_xy_from(lat, lon, mapview.zoom)
        else:
            # Запасний варіант для некоректних координат
            x, y = data.get("x", 0), data.get("y", 0)
    else:
        # Використовуємо екранні координати
        x, y = data.get("x", 0), data.get("y", 0)
    
    # Отримуємо інші параметри
    event_type = data.get("event_type", "draw")
    color = data.get("color", "#000000")
    brush_size = data.get("brush_size", data.get("size", 5))
    tool = data.get("tool", "brush")
    
    # Малюємо на екрані
    draw_on_screen(x, y, event_type, color, brush_size, tool)
```

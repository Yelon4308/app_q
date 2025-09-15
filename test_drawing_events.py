#!/usr/bin/env python3
"""
Тестування функціональності подій малювання
"""
import asyncio
import json
import uuid
import websockets
import aiohttp
from datetime import datetime
import sys
import random

# Налаштування
SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
ROOM_ID = "test-room"

# Кольори для тестування
COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FF00FF", "#FFFF00", "#00FFFF"]

# Платформи для тестування
PLATFORMS = ["android", "windows"]

async def test_rest_api():
    """Тестування REST API для подій малювання"""
    print(f"📡 Тестування REST API для подій малювання в кімнаті {ROOM_ID}")
    
    async with aiohttp.ClientSession() as session:
        # Створюємо декілька подій
        for i in range(3):
            event_id = f"test-event-{uuid.uuid4().hex[:8]}"
            event_data = {
                "event_id": event_id,
                "event_name": f"Тестова подія {i+1}",
                "drawing_type": "polygon",
                "action": "add_point",
                "platform": random.choice(PLATFORMS),
                "timestamp": datetime.now().isoformat(),
                "style": {
                    "color": random.choice(COLORS),
                    "width": random.uniform(1.0, 5.0),
                    "fill": random.choice([True, False]),
                    "opacity": random.uniform(0.3, 1.0)
                },
                "data": {
                    "lat": random.uniform(48.0, 49.0),
                    "lon": random.uniform(30.0, 31.0)
                }
            }
            
            print(f"📤 Створення події {event_id}...")
            async with session.post(
                f"{SERVER_URL}/api/events/{ROOM_ID}",
                json=event_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Подія створена: {result}")
                else:
                    print(f"❌ Помилка створення події: {response.status}")
                    text = await response.text()
                    print(f"   Відповідь: {text}")
        
        # Отримуємо всі події
        print(f"\n📥 Отримання списку подій для кімнати {ROOM_ID}...")
        async with session.get(f"{SERVER_URL}/api/events/{ROOM_ID}") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Отримано {len(result['events'])} подій:")
                for event in result["events"]:
                    print(f"   - {event['event_id']}: {event.get('event_name')} ({event['drawing_type']})")
            else:
                print(f"❌ Помилка отримання подій: {response.status}")
        
        # Спроба отримати конкретну подію
        if len(result["events"]) > 0:
            event_id = result["events"][0]["event_id"]
            print(f"\n📥 Отримання події {event_id}...")
            async with session.get(f"{SERVER_URL}/api/events/{ROOM_ID}/{event_id}") as response:
                if response.status == 200:
                    event = await response.json()
                    print(f"✅ Отримано подію {event_id}:")
                    print(f"   Назва: {event.get('event_name')}")
                    print(f"   Тип: {event['drawing_type']}")
                    print(f"   Дія: {event['action']}")
                    print(f"   Платформа: {event['platform']}")
                else:
                    print(f"❌ Помилка отримання події: {response.status}")
        
        # Видалення події
        if len(result["events"]) > 1:
            event_id = result["events"][1]["event_id"]
            print(f"\n🗑️ Видалення події {event_id}...")
            async with session.delete(f"{SERVER_URL}/api/events/{ROOM_ID}/{event_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Подію видалено: {result}")
                else:
                    print(f"❌ Помилка видалення події: {response.status}")
        
        # Перевірка після видалення
        print(f"\n📥 Перевірка списку подій після видалення...")
        async with session.get(f"{SERVER_URL}/api/events/{ROOM_ID}") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Залишилось {len(result['events'])} подій")
            else:
                print(f"❌ Помилка отримання подій: {response.status}")

async def test_websocket():
    """Тестування WebSocket для подій малювання"""
    print(f"\n📡 Тестування WebSocket для подій малювання в кімнаті {ROOM_ID}")
    
    # Підключаємось до WebSocket
    print(f"🔌 Підключення до WebSocket...")
    try:
        async with websockets.connect(f"{WS_URL}/ws/{ROOM_ID}") as websocket:
            print("✅ Підключено до WebSocket")
            
            # Відправляємо повідомлення про підключення
            await websocket.send(json.dumps({
                "type": "join",
                "platform": "test_client",
                "version": "1.0.0"
            }))
            
            # Очікуємо підтвердження
            response = await websocket.recv()
            print(f"📥 Отримано: {response}")
            
            # Створюємо подію через WebSocket
            event_id = f"ws-event-{uuid.uuid4().hex[:8]}"
            print(f"\n📤 Надсилання події {event_id} через WebSocket...")
            await websocket.send(json.dumps({
                "type": "drawing_event",
                "event_id": event_id,
                "event_name": "Подія через WebSocket",
                "drawing_type": "marker",
                "action": "add",
                "platform": "test_client",
                "data": {
                    "lat": 48.5,
                    "lon": 30.5
                },
                "style": {
                    "color": "#FF0000",
                    "width": 3.0,
                    "fill": True,
                    "opacity": 0.7
                }
            }))
            
            # Очікуємо на відповідь
            print("⏳ Очікування відповіді...")
            for _ in range(3):  # Очікуємо кілька повідомлень
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"📥 Отримано: {response}")
                except asyncio.TimeoutError:
                    break
            
            print("✅ Тестування WebSocket завершено")
    except Exception as e:
        print(f"❌ Помилка WebSocket: {e}")

async def main():
    """Головна функція"""
    print("🧪 Запуск тестів для подій малювання")
    
    try:
        # Тестуємо REST API
        await test_rest_api()
        
        # Тестуємо WebSocket
        await test_websocket()
        
        print("\n✅ Всі тести успішно завершені")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

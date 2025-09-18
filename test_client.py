"""
Простой тест клиент для WebSocket соединения
"""
import asyncio
import websockets
import json
from datetime import datetime

async def test_drawing_sync():
    """Тест синхронизации рисования"""
    uri = "wss://app-q.onrender.com/ws/default-room"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Подключено к серверу")
            
            # Отправляем команду рисования
            drawing_command = {
                "type": "drawing",
                "x": 100,
                "y": 200,
                "action": "draw",
                "color": "#FF0000",
                "size": 5,
                "tool": "brush"
            }
            
            await websocket.send(json.dumps(drawing_command))
            print("📤 Отправлена команда рисования")
            
            # Слушаем ответы
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📥 Получен ответ: {data}")
            except asyncio.TimeoutError:
                print("⏰ Таймаут ожидания ответа")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

def test_api():
    """Тест REST API"""
    import requests
    
    base_url = "https://app-q.onrender.com"
    
    try:
        # Тест статуса
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            print("✅ API статус работает")
            print(f"📊 Статус сервера: {response.json()}")
        else:
            print(f"❌ Ошибка API статус: {response.status_code}")
        
        # Тест комнат
        response = requests.get(f"{base_url}/api/rooms/")
        if response.status_code == 200:
            print("✅ API комнат работает")
            print(f"🏠 Комнаты: {response.json()}")
        else:
            print(f"❌ Ошибка API комнат: {response.status_code}")
            
        # Тест проверки обновлений
        response = requests.get(f"{base_url}/api/updates/check/android?current_version=1.0.0")
        if response.status_code == 200:
            print("✅ API обновлений работает")
            print(f"🔄 Обновления: {response.json()}")
        else:
            print(f"❌ Ошибка API обновлений: {response.status_code}")
            
    except requests.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"❌ Ошибка тестирования API: {e}")

if __name__ == "__main__":
    print("🧪 Тестирование Drawing Sync Server\n")
    
    print("1. Тестирование REST API:")
    test_api()
    
    print("\n2. Тестирование WebSocket:")
    asyncio.run(test_drawing_sync())

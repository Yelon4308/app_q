import asyncio
import websockets
import json

async def test_websocket():
    try:
        print("🔌 Подключаемся к WebSocket...")
        async with websockets.connect("ws://127.0.0.1:8000/ws/test_room") as websocket:
            print("✅ Подключение успешно!")
            
            # Отправляем тестовое сообщение
            test_message = {
                "type": "drawing",
                "x": 100,
                "y": 200,
                "action": "draw",
                "color": "#FF0000",
                "size": 5,
                "tool": "brush"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Отправлено тестовое сообщение")
            
            # Ждем ответ
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Получен ответ: {response}")
            except asyncio.TimeoutError:
                print("⏰ Таймаут - ответ не получен")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())

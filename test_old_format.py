import asyncio
import websockets
import json

async def test_old_format():
    try:
        print("🔌 Тестуємо старий формат...")
        uri = "wss://app-q.onrender.com/ws/test_room"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Підключення успішне!")
            
            # Тестуємо старий формат
            old_message = {
                "type": "drawing",
                "x": 100,
                "y": 200,
                "action": "draw",
                "color": "#FF0000",
                "size": 5,
                "tool": "brush"
            }
            
            print(f"📤 Надсилаємо старе повідомлення:")
            print(f"   {json.dumps(old_message, indent=2)}")
            
            await websocket.send(json.dumps(old_message))
            
            # Чекаємо відповідь
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Отримано відповідь:")
                print(f"   {response}")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout - відповідь не отримана")
                
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_old_format())

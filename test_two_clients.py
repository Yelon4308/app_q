import asyncio
import websockets
import json

async def client_sender():
    """Клієнт який надсилає повідомлення"""
    try:
        uri = "wss://app-q.onrender.com/ws/test_room"
        async with websockets.connect(uri) as websocket:
            print("📤 Sender підключився!")
            
            await asyncio.sleep(2)  # Даємо час другому клієнту підключитися
            
            test_message = {
                "type": "drawing",
                "x": 100,
                "y": 200,
                "action": "draw",
                "color": "#FF0000",
                "size": 5,
                "tool": "brush"
            }
            
            print(f"📤 Надсилаємо: {json.dumps(test_message)}")
            await websocket.send(json.dumps(test_message))
            
            await asyncio.sleep(5)  # Тримаємо з'єднання
            
    except Exception as e:
        print(f"❌ Sender помилка: {e}")

async def client_receiver():
    """Клієнт який слухає повідомлення"""
    try:
        uri = "wss://app-q.onrender.com/ws/test_room"
        async with websockets.connect(uri) as websocket:
            print("📥 Receiver підключився!")
            
            # Слухаємо повідомлення
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    print(f"📥 Receiver отримав: {message}")
                except asyncio.TimeoutError:
                    print("⏰ Receiver timeout")
                    break
                    
    except Exception as e:
        print(f"❌ Receiver помилка: {e}")

async def test_two_clients():
    """Тест з двома клієнтами"""
    print("🔌 Запускаємо тест з двома клієнтами...")
    
    # Запускаємо обох клієнтів одночасно
    await asyncio.gather(
        client_receiver(),
        client_sender()
    )

if __name__ == "__main__":
    asyncio.run(test_two_clients())

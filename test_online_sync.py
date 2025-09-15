import asyncio
import websockets
import json
import uuid

async def test_online_sync():
    try:
        print("🔌 Підключаємося до онлайн WebSocket...")
        uri = "wss://app-q.onrender.com/ws/test_room"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Підключення успішне!")
            
            # Тестуємо новий формат полігону
            test_polygon_message = {
                "type": "drawing",
                "action_type": "polygon_point",
                "action_id": str(uuid.uuid4()),
                "data": {
                    "lat": 50.5240511769708,
                    "lon": 30.377864379882823,
                    "is_first": True
                }
            }
            
            print(f"📤 Надсилаємо тестове повідомлення полігону:")
            print(f"   {json.dumps(test_polygon_message, indent=2)}")
            
            await websocket.send(json.dumps(test_polygon_message))
            
            # Чекаємо відповідь
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Отримано відповідь:")
                print(f"   {response}")
                
                # Тестуємо закриття полігону
                close_message = {
                    "type": "drawing",
                    "action_type": "close_polygon",
                    "action_id": str(uuid.uuid4()),
                    "data": {}
                }
                
                print(f"📤 Надсилаємо закриття полігону:")
                print(f"   {json.dumps(close_message, indent=2)}")
                
                await websocket.send(json.dumps(close_message))
                
                # Чекаємо відповідь
                response2 = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Отримано відповідь 2:")
                print(f"   {response2}")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout - відповідь не отримана")
                
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_online_sync())

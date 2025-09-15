from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
from typing import Dict, List, Set
from datetime import datetime
import os

from websocket_handler import ConnectionManager, handle_websocket_connection, UKRAINE_REGIONS, active_rooms
from database import Database, init_db
from api.updates import router as updates_router
from api.rooms import router as rooms_router
from api.events import router as events_router
from models.drawing import DrawingCommand, Room
from models.drawing_event import DrawingEvent

app = FastAPI(title="Drawing Sync Server", version="1.0.0")

# CORS middleware для поддержки клиентов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы для обновлений
os.makedirs("static/updates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация менеджера соединений и базы данных
manager = ConnectionManager()
db = Database()

# Подключение роутеров
app.include_router(updates_router, prefix="/api/updates", tags=["updates"])
app.include_router(rooms_router, prefix="/api/rooms", tags=["rooms"])
app.include_router(events_router, prefix="/api/events", tags=["events"])

# Настройка менеджера соединений для API
from api.rooms import set_connection_manager as set_rooms_manager
from api.events import set_connection_manager as set_events_manager

set_rooms_manager(manager)
set_events_manager(manager)
from api.rooms import set_connection_manager

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервера"""
    await init_db()
    set_connection_manager(manager)
    print("🚀 Drawing Sync Server запущен!")

@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "Drawing Sync Server",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/{room_id}",
            "updates": "/api/updates/",
            "rooms": "/api/rooms/"
        }
    }

@app.get("/api/status")
async def get_status():
    """Статус сервера"""
    return {
        "status": "online",
        "connected_clients": len(manager.active_connections),
        "active_rooms": len(manager.rooms),
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint для синхронизации рисования"""
    await manager.connect(websocket, room_id)
    try:
        while True:
            # Получаем данные от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Обрабатываем команду рисования
            if message.get("type") == "drawing":
                # Поддержка нового формата с географическими координатами
                data = message.get("data", {})
                action_type = message.get("action_type", "unknown")
                
                print(f"📝 Получено сообщение рисования: {action_type}")
                print(f"📊 Данные: {data}")
                
                drawing_command = DrawingCommand(
                    x=data.get("lat", 0),  # Используем lat как x
                    y=data.get("lon", 0),  # Используем lon как y
                    action=action_type,
                    color=data.get("color", "#000000"),
                    size=data.get("size", 5),
                    tool=data.get("tool", action_type.split("_")[0] if "_" in action_type else "brush"),
                    timestamp=datetime.now().isoformat()
                )
                
            # Обработка стандартизированных событий рисования через JSON
            elif message.get("type") == "drawing_event":
                try:
                    # Проверяем обязательные поля
                    if not all(k in message for k in ["event_id", "drawing_type", "action", "platform", "data"]):
                        await manager.send_personal_message(
                            {"type": "error", "message": "Неполные данные события рисования"}, 
                            websocket
                        )
                        continue
                    
                    print(f"🎨 Получено событие рисования: {message['drawing_type']} - {message['action']}")
                    print(f"📊 ID события: {message['event_id']}, платформа: {message['platform']}")
                    
                    # Просто пересылаем сообщение всем в комнате как есть - стандартизированный формат
                    await manager.broadcast_to_room(room_id, message)
                except Exception as e:
                    print(f"❌ Ошибка обработки события рисования: {e}")
                    await manager.send_personal_message(
                        {"type": "error", "message": f"Ошибка обработки события: {str(e)}"}, 
                        websocket
                    )
                
                # Сохраняем в базу данных
                await db.save_drawing_command(room_id, drawing_command)
                
                # Транслируем всем клиентам в комнате (передаем полное сообщение)
                broadcast_message = {
                    "type": "drawing",
                    "action_type": action_type,
                    "action_id": message.get("action_id"),
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"📡 Транслируем сообщение: {broadcast_message}")
                
                await manager.broadcast_to_room(room_id, broadcast_message, exclude=websocket)
            
            elif message.get("type") == "clear":
                # Очистка холста
                await db.clear_room_drawings(room_id)
                await manager.broadcast_to_room(room_id, {
                    "type": "clear",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message.get("type") == "template":
                # Добавление шаблона
                template_data = message.get("data")
                await db.save_template(room_id, template_data)
                await manager.broadcast_to_room(room_id, {
                    "type": "template",
                    "data": template_data,
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
        await manager.disconnect(websocket, room_id)

@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    """WebSocket endpoint для підключення до кімнати"""
    await handle_websocket_connection(websocket, room)

@app.get("/api/rooms")
async def get_rooms():
    """Отримання списку доступних кімнат"""
    rooms_info = []
    for room in UKRAINE_REGIONS:
        rooms_info.append({
            "name": room,
            "users_count": len(active_rooms[room])
        })
    return {"rooms": rooms_info}

@app.get("/api/rooms/{room}/status")
async def get_room_status(room: str):
    """Отримання статусу конкретної кімнати"""
    if room not in UKRAINE_REGIONS:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {
        "room": room,
        "users_count": len(active_rooms[room]),
        "is_active": len(active_rooms[room]) > 0
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

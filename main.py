from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
from typing import Dict, List, Set
from datetime import datetime
import os

from websocket_handler import ConnectionManager
from database import Database, init_db
from api.updates import router as updates_router
from api.rooms import router as rooms_router
from models.drawing import DrawingCommand, Room

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

# Настройка менеджера соединений для API комнат
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
            if message.get("type") == "drawing" or message.get("type") == "drawing_event":
                data = message.get("data", {}) if message.get("type") == "drawing_event" else message
                
                # Проверяем наличие географических координат
                is_geographical = data.get("is_geographical", False)
                lat = data.get("lat")
                lon = data.get("lon")
                x = data.get("x", 0)
                y = data.get("y", 0)
                
                # Если lat/lon отсутствуют, но x/y находятся в диапазоне географических координат
                if (lat is None or lon is None) and (-90 <= x <= 90) and (-180 <= y <= 180):
                    print(f"Конвертируем x,y в lat,lon: x={x}, y={y}")
                    lat = x
                    lon = y
                    is_geographical = True
                
                drawing_command = DrawingCommand(
                    x=x,
                    y=y,
                    lat=lat,
                    lon=lon,
                    is_geographical=is_geographical,
                    action=data.get("action", data.get("event_type", "draw")),
                    color=data.get("color", "#000000"),
                    size=data.get("size", data.get("brush_size", 5)),
                    tool=data.get("tool", "brush"),
                    timestamp=datetime.now().isoformat()
                )
                
                # Сохраняем в базу данных
                await db.save_drawing_command(room_id, drawing_command)
                
                # Транслируем всем клиентам в комнате
                await manager.broadcast_to_room(room_id, {
                    "type": "drawing",
                    "data": drawing_command.dict()
                }, exclude=websocket)
            
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

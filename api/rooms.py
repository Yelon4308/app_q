from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime

from database import Database
from websocket_handler import ConnectionManager

router = APIRouter()
db = Database()

# Тут будет передаваться менеджер соединений из main.py
manager: ConnectionManager = None

def set_connection_manager(connection_manager: ConnectionManager):
    """Установка менеджера соединений"""
    global manager
    manager = connection_manager

@router.get("/")
async def get_all_rooms():
    """Получение списка всех активных комнат"""
    if not manager:
        return {"rooms": []}
    
    rooms_info = []
    for room_id, user_count in manager.rooms.items():
        rooms_info.append({
            "room_id": room_id,
            "users_count": user_count,
            "status": "active"
        })
    
    return {"rooms": rooms_info}

@router.get("/{room_id}")
async def get_room_info(room_id: str):
    """Получение информации о конкретной комнате"""
    if not manager:
        raise HTTPException(status_code=503, detail="Сервис недоступен")
    
    room_info = manager.get_room_info(room_id)
    
    return {
        "room": room_info,
        "drawings_count": len(await db.get_room_drawings(room_id)),
        "templates_count": len(await db.get_room_templates(room_id))
    }

@router.get("/{room_id}/drawings")
async def get_room_drawings(room_id: str):
    """Получение всех рисунков в комнате"""
    drawings = await db.get_room_drawings(room_id)
    return {
        "room_id": room_id,
        "drawings": drawings,
        "count": len(drawings)
    }

@router.get("/{room_id}/templates")
async def get_room_templates(room_id: str):
    """Получение всех шаблонов в комнате"""
    templates = await db.get_room_templates(room_id)
    return {
        "room_id": room_id,
        "templates": templates,
        "count": len(templates)
    }

@router.delete("/{room_id}/drawings")
async def clear_room_drawings(room_id: str):
    """Очистка всех рисунков в комнате"""
    await db.clear_room_drawings(room_id)
    
    # Уведомляем всех участников комнаты
    if manager:
        await manager.broadcast_to_room(room_id, {
            "type": "clear",
            "timestamp": datetime.now().isoformat(),
            "source": "api"
        })
    
    return {"message": f"Рисунки в комнате {room_id} очищены"}

@router.post("/{room_id}/join")
async def join_room(room_id: str):
    """Информация для подключения к комнате"""
    return {
        "room_id": room_id,
        "websocket_url": f"/ws/{room_id}",
        "message": f"Подключитесь к WebSocket по адресу ws://your-server/ws/{room_id}"
    }

@router.get("/{room_id}/export")
async def export_room_data(room_id: str):
    """Экспорт данных комнаты"""
    drawings = await db.get_room_drawings(room_id)
    templates = await db.get_room_templates(room_id)
    
    room_info = None
    if manager:
        room_info = manager.get_room_info(room_id)
    
    return {
        "room_id": room_id,
        "exported_at": datetime.now().isoformat(),
        "room_info": room_info,
        "drawings": drawings,
        "templates": templates,
        "stats": {
            "drawings_count": len(drawings),
            "templates_count": len(templates)
        }
    }

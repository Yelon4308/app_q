from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import json
from datetime import datetime

from database import Database
from models.drawing_event import DrawingEvent
from websocket_handler import ConnectionManager

router = APIRouter()
db = Database()

# Тут буде передаватися менеджер з'єднань з main.py
manager: ConnectionManager = None

def set_connection_manager(connection_manager: ConnectionManager):
    """Встановлення менеджера з'єднань"""
    global manager
    manager = connection_manager

@router.post("/{room_id}")
async def create_drawing_event(room_id: str, event: DrawingEvent):
    """Створення нової події малювання"""
    # Зберігаємо подію в базі даних
    result = await db.save_drawing_event(room_id, event)
    
    if not result:
        raise HTTPException(status_code=409, detail=f"Подія з ID {event.event_id} вже існує")
    
    # Відправляємо подію всім учасникам кімнати через WebSocket
    if manager:
        await manager.broadcast_to_room(room_id, {
            "type": "drawing_event",
            "event_id": event.event_id,
            "event_name": event.event_name,
            "drawing_type": event.drawing_type,
            "action": event.action,
            "platform": event.platform,
            "timestamp": event.timestamp.isoformat(),
            "style": event.style.dict(),
            "data": event.data if isinstance(event.data, dict) else event.data.dict()
        })
    
    return {
        "success": True,
        "message": f"Подія малювання {event.event_id} створена",
        "event_id": event.event_id
    }

@router.get("/{room_id}")
async def get_room_events(room_id: str):
    """Отримання всіх подій малювання в кімнаті"""
    events = await db.get_room_events(room_id)
    
    return {
        "room_id": room_id,
        "events": events,
        "count": len(events)
    }

@router.get("/{room_id}/{event_id}")
async def get_event(room_id: str, event_id: str):
    """Отримання конкретної події за ID"""
    event = await db.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail=f"Подія з ID {event_id} не знайдена")
    
    if event["room_id"] != room_id:
        raise HTTPException(status_code=403, detail="Подія належить іншій кімнаті")
    
    return event

@router.delete("/{room_id}/{event_id}")
async def delete_event(room_id: str, event_id: str):
    """Видалення події малювання"""
    event = await db.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail=f"Подія з ID {event_id} не знайдена")
    
    if event["room_id"] != room_id:
        raise HTTPException(status_code=403, detail="Подія належить іншій кімнаті")
    
    result = await db.delete_event(event_id)
    
    if not result:
        raise HTTPException(status_code=500, detail="Помилка видалення події")
    
    # Повідомляємо всім учасникам кімнати про видалення
    if manager:
        await manager.broadcast_to_room(room_id, {
            "type": "drawing_event_deleted",
            "event_id": event_id
        })
    
    return {
        "success": True,
        "message": f"Подія {event_id} видалена"
    }

@router.delete("/{room_id}")
async def clear_room_events(room_id: str):
    """Очищення всіх подій малювання в кімнаті"""
    await db.clear_room_events(room_id)
    
    # Повідомляємо всім учасникам кімнати
    if manager:
        await manager.broadcast_to_room(room_id, {
            "type": "clear_events",
            "timestamp": datetime.now().isoformat(),
            "source": "api"
        })
    
    return {
        "success": True,
        "message": f"Всі події малювання в кімнаті {room_id} видалені"
    }

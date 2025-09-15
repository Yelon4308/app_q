from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class DrawingCommand(BaseModel):
    """Команда рисования"""
    x: float
    y: float
    action: str  # "draw", "move", "up", "down"
    color: str = "#000000"
    size: int = 5
    tool: str = "brush"  # "brush", "eraser", "line", "rectangle", "circle"
    timestamp: str

class Room(BaseModel):
    """Модель комнаты"""
    id: str
    name: Optional[str] = None
    created_at: datetime
    max_users: int = 50
    is_private: bool = False
    password: Optional[str] = None

class Template(BaseModel):
    """Шаблон для рисования"""
    id: Optional[str] = None
    name: str
    data: Dict[str, Any]  # JSON данные шаблона
    room_id: str
    created_at: datetime

class AppVersion(BaseModel):
    """Версия приложения"""
    platform: str  # "android", "windows", "linux"
    version: str
    download_url: str
    file_size: int
    release_notes: str
    is_required: bool = False  # Обязательное обновление
    created_at: datetime

class UserSession(BaseModel):
    """Сессия пользователя"""
    session_id: str
    room_id: str
    platform: str
    app_version: str
    connected_at: datetime
    last_activity: datetime

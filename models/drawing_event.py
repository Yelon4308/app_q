"""
Модель для стандартизованої події малювання
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

class DrawingStyle(BaseModel):
    """Стиль елементу малювання"""
    color: str = Field(default="#FF0000", description="Колір у форматі HEX")
    width: float = Field(default=2.0, description="Товщина лінії")
    fill: bool = Field(default=False, description="Заповнення для полігонів")
    opacity: float = Field(default=1.0, description="Прозорість (0.0 - 1.0)")
    
class DrawingPointData(BaseModel):
    """Дані для точки малювання"""
    lat: float = Field(..., description="Широта")
    lon: float = Field(..., description="Довгота")
    
class DrawingEvent(BaseModel):
    """Подія малювання для синхронізації"""
    event_id: str = Field(..., description="Унікальний ідентифікатор події")
    event_name: Optional[str] = Field(None, description="Назва події (опційно)")
    drawing_type: str = Field(..., description="Тип малювання (polygon, line, marker, тощо)")
    action: str = Field(..., description="Дія (add_point, finish_drawing, clear, тощо)")
    platform: str = Field(..., description="Платформа, з якої надіслано (android, windows)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Час створення події")
    style: DrawingStyle = Field(default_factory=DrawingStyle, description="Стиль малювання")
    data: Union[DrawingPointData, Dict[str, Any]] = Field(..., description="Дані малювання")
    
    class Config:
        schema_extra = {
            "example": {
                "event_id": "fire-2025-09-09-001",
                "event_name": "Пожежа на вул. Шевченка 10",
                "drawing_type": "polygon",
                "action": "add_point",
                "platform": "android",
                "timestamp": "2025-09-09T12:34:56Z",
                "style": {
                    "color": "#FF0000",
                    "width": 3,
                    "fill": True,
                    "opacity": 0.5
                },
                "data": {
                    "lat": 48.12345,
                    "lon": 30.67890
                }
            }
        }

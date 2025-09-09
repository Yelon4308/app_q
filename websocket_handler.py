from fastapi import WebSocket
from typing import Dict, List, Set
from datetime import datetime
import json

class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        # Активные соединения по комнатам
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Мета информация о соединениях
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        """Подключение клиента к комнате"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(websocket)
        self.connection_info[websocket] = {
            "room_id": room_id,
            "connected_at": str(datetime.now())
        }
        
        print(f"✅ Клиент подключился к комнате {room_id}. Всего в комнате: {len(self.active_connections[room_id])}")
        
        # Отправляем информацию о подключении другим участникам
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "room_id": room_id,
            "total_users": len(self.active_connections[room_id])
        }, exclude=websocket)
    
    async def disconnect(self, websocket: WebSocket, room_id: str):
        """Отключение клиента от комнаты"""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            
            # Удаляем пустые комнаты
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        print(f"❌ Клиент отключился от комнаты {room_id}")
        
        # Уведомляем остальных участников
        if room_id in self.active_connections:
            await self.broadcast_to_room(room_id, {
                "type": "user_left",
                "room_id": room_id,
                "total_users": len(self.active_connections[room_id])
            })
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Отправка личного сообщения"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude: WebSocket = None):
        """Рассылка сообщения всем участникам комнаты"""
        if room_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[room_id].copy():
            if connection == exclude:
                continue
                
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Ошибка рассылки сообщения: {e}")
                disconnected.add(connection)
        
        # Удаляем отключенные соединения
        for connection in disconnected:
            await self.disconnect(connection, room_id)
    
    def get_room_info(self, room_id: str) -> dict:
        """Информация о комнате"""
        if room_id not in self.active_connections:
            return {"room_id": room_id, "users_count": 0, "users": []}
        
        return {
            "room_id": room_id,
            "users_count": len(self.active_connections[room_id]),
            "users": [
                self.connection_info.get(conn, {}) 
                for conn in self.active_connections[room_id]
            ]
        }
    
    @property
    def rooms(self) -> Dict[str, int]:
        """Список всех активных комнат"""
        return {
            room_id: len(connections) 
            for room_id, connections in self.active_connections.items()
        }

import sqlite3
import aiosqlite
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from models.drawing import DrawingCommand, Room, Template, AppVersion
from models.drawing_event import DrawingEvent

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = "drawing_sync.db"):
        self.db_path = db_path
    
    async def execute_query(self, query: str, params: tuple = ()):
        """Выполнение запроса к базе данных"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()
    
    async def fetch_one(self, query: str, params: tuple = ()):
        """Получение одной записи"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                return await cursor.fetchone()
    
    async def fetch_all(self, query: str, params: tuple = ()):
        """Получение всех записей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                return await cursor.fetchall()
    
    async def save_drawing_command(self, room_id: str, command: DrawingCommand):
        """Сохранение команды рисования"""
        query = """
        INSERT INTO drawing_commands (room_id, x, y, action, color, size, tool, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            room_id, command.x, command.y, command.action,
            command.color, command.size, command.tool, command.timestamp
        )
        await self.execute_query(query, params)
    
    async def get_room_drawings(self, room_id: str) -> List[Dict]:
        """Получение всех команд рисования для комнаты"""
        query = """
        SELECT x, y, action, color, size, tool, timestamp
        FROM drawing_commands
        WHERE room_id = ?
        ORDER BY id ASC
        """
        rows = await self.fetch_all(query, (room_id,))
        
        return [
            {
                "x": row[0], "y": row[1], "action": row[2],
                "color": row[3], "size": row[4], "tool": row[5],
                "timestamp": row[6]
            }
            for row in rows
        ]
    
    async def clear_room_drawings(self, room_id: str):
        """Очистка всех рисунков в комнате"""
        query = "DELETE FROM drawing_commands WHERE room_id = ?"
        await self.execute_query(query, (room_id,))
    
    async def save_template(self, room_id: str, template_data: Dict[str, Any]):
        """Сохранение шаблона"""
        query = """
        INSERT INTO templates (room_id, name, data, created_at)
        VALUES (?, ?, ?, ?)
        """
        params = (
            room_id,
            template_data.get("name", "Шаблон"),
            json.dumps(template_data),
            datetime.now().isoformat()
        )
        await self.execute_query(query, params)
    
    async def get_room_templates(self, room_id: str) -> List[Dict]:
        """Получение шаблонов для комнаты"""
        query = """
        SELECT id, name, data, created_at
        FROM templates
        WHERE room_id = ?
        ORDER BY created_at DESC
        """
        rows = await self.fetch_all(query, (room_id,))
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "data": json.loads(row[2]),
                "created_at": row[3]
            }
            for row in rows
        ]
    
    async def save_app_version(self, version: AppVersion):
        """Сохранение версии приложения"""
        query = """
        INSERT INTO app_versions (platform, version, download_url, file_size, release_notes, is_required, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            version.platform, version.version, version.download_url,
            version.file_size, version.release_notes, version.is_required,
            version.created_at.isoformat()
        )
        await self.execute_query(query, params)
    
    async def get_latest_version(self, platform: str) -> Optional[Dict]:
        """Получение последней версии для платформы"""
        query = """
        SELECT platform, version, download_url, file_size, release_notes, is_required, created_at
        FROM app_versions
        WHERE platform = ?
        ORDER BY created_at DESC
        LIMIT 1
        """
        row = await self.fetch_one(query, (platform,))
        
        if row:
            return {
                "platform": row[0],
                "version": row[1],
                "download_url": row[2],
                "file_size": row[3],
                "release_notes": row[4],
                "is_required": bool(row[5]),
                "created_at": row[6]
            }
        return None
    
    async def save_drawing_event(self, room_id: str, event: DrawingEvent):
        """Сохранение события рисования"""
        query = """
        INSERT INTO drawing_events (
            event_id, event_name, room_id, drawing_type, action, 
            platform, style, data, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            event.event_id, 
            event.event_name,
            room_id,
            event.drawing_type,
            event.action,
            event.platform,
            json.dumps(event.style.dict()),
            json.dumps(event.data if isinstance(event.data, dict) else event.data.dict()),
            event.timestamp.isoformat()
        )
        
        try:
            await self.execute_query(query, params)
            return True
        except sqlite3.IntegrityError:
            # Событие с таким event_id уже существует
            return False
    
    async def get_room_events(self, room_id: str) -> List[Dict]:
        """Получение всех событий рисования для комнаты"""
        query = """
        SELECT event_id, event_name, drawing_type, action, platform, style, data, timestamp
        FROM drawing_events
        WHERE room_id = ?
        ORDER BY timestamp ASC
        """
        
        rows = await self.fetch_all(query, (room_id,))
        
        return [
            {
                "event_id": row[0],
                "event_name": row[1],
                "drawing_type": row[2],
                "action": row[3],
                "platform": row[4],
                "style": json.loads(row[5]),
                "data": json.loads(row[6]),
                "timestamp": row[7]
            }
            for row in rows
        ]
    
    async def get_event(self, event_id: str) -> Optional[Dict]:
        """Получение конкретного события по ID"""
        query = """
        SELECT event_id, event_name, room_id, drawing_type, action, platform, style, data, timestamp
        FROM drawing_events
        WHERE event_id = ?
        """
        
        row = await self.fetch_one(query, (event_id,))
        
        if not row:
            return None
            
        return {
            "event_id": row[0],
            "event_name": row[1],
            "room_id": row[2],
            "drawing_type": row[3],
            "action": row[4],
            "platform": row[5],
            "style": json.loads(row[6]),
            "data": json.loads(row[7]),
            "timestamp": row[8]
        }
    
    async def delete_event(self, event_id: str) -> bool:
        """Удаление события по ID"""
        query = """
        DELETE FROM drawing_events
        WHERE event_id = ?
        """
        
        try:
            await self.execute_query(query, (event_id,))
            return True
        except Exception:
            return False
            
    async def clear_room_events(self, room_id: str):
        """Очистка всех событий рисования в комнате"""
        query = "DELETE FROM drawing_events WHERE room_id = ?"
        await self.execute_query(query, (room_id,))

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect("drawing_sync.db") as db:
        # Таблица команд рисования
        await db.execute("""
        CREATE TABLE IF NOT EXISTS drawing_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            action TEXT NOT NULL,
            color TEXT DEFAULT '#000000',
            size INTEGER DEFAULT 5,
            tool TEXT DEFAULT 'brush',
            timestamp TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Таблица комнат
        await db.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            max_users INTEGER DEFAULT 50,
            is_private BOOLEAN DEFAULT FALSE,
            password TEXT
        )
        """)
        
        # Таблица шаблонов
        await db.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            name TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Таблица версий приложений
        await db.execute("""
        CREATE TABLE IF NOT EXISTS app_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            version TEXT NOT NULL,
            download_url TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            release_notes TEXT NOT NULL,
            is_required BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Индексы для оптимизации
        await db.execute("CREATE INDEX IF NOT EXISTS idx_drawing_room ON drawing_commands(room_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_templates_room ON templates(room_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_versions_platform ON app_versions(platform)")
        
        # Таблица событий рисования
        await db.execute("""
        CREATE TABLE IF NOT EXISTS drawing_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            event_name TEXT,
            room_id TEXT NOT NULL,
            drawing_type TEXT NOT NULL,
            action TEXT NOT NULL,
            platform TEXT NOT NULL,
            style TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Индекс для событий рисования
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_room ON drawing_events(room_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_event_id ON drawing_events(event_id)")
        
        await db.commit()
        print("✅ База данных инициализирована")

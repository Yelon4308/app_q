import sqlite3
import aiosqlite
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from models.drawing import DrawingCommand, Room, Template, AppVersion

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
        """Сохранение команды рисования с поддержкой географических координат"""
        query = """
        INSERT INTO drawing_commands 
        (room_id, x, y, lat, lon, is_geographical, action, color, size, tool, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            room_id, command.x, command.y, command.lat, command.lon, 
            command.is_geographical, command.action,
            command.color, command.size, command.tool, command.timestamp
        )
        await self.execute_query(query, params)
    
    async def get_room_drawings(self, room_id: str) -> List[Dict]:
        """Получение всех команд рисования для комнаты с поддержкой географических координат"""
        query = """
        SELECT x, y, lat, lon, is_geographical, action, color, size, tool, timestamp
        FROM drawing_commands
        WHERE room_id = ?
        ORDER BY id ASC
        """
        rows = await self.fetch_all(query, (room_id,))
        
        return [
            {
                "x": row[0], "y": row[1], 
                "lat": row[2], "lon": row[3], 
                "is_geographical": bool(row[4]),
                "action": row[5],
                "color": row[6], "size": row[7], 
                "tool": row[8],
                "timestamp": row[9]
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

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect("drawing_sync.db") as db:
        # Проверяем существование таблицы drawing_commands
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drawing_commands'")
        table_exists = await cursor.fetchone() is not None
        
        if table_exists:
            # Проверяем существование столбцов lat, lon, is_geographical
            try:
                cursor = await db.execute("PRAGMA table_info(drawing_commands)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Если нужных столбцов нет, добавляем их
                if 'lat' not in column_names:
                    await db.execute("ALTER TABLE drawing_commands ADD COLUMN lat REAL")
                if 'lon' not in column_names:
                    await db.execute("ALTER TABLE drawing_commands ADD COLUMN lon REAL")
                if 'is_geographical' not in column_names:
                    await db.execute("ALTER TABLE drawing_commands ADD COLUMN is_geographical BOOLEAN DEFAULT FALSE")
                
                print("Таблица drawing_commands обновлена для поддержки географических координат")
            except Exception as e:
                print(f"Ошибка при обновлении таблицы: {e}")
        else:
            # Создаем таблицу с новой структурой
            await db.execute("""
            CREATE TABLE IF NOT EXISTS drawing_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                x REAL,
                y REAL,
                lat REAL,
                lon REAL,
                is_geographical BOOLEAN DEFAULT FALSE,
                action TEXT NOT NULL,
                color TEXT DEFAULT '#000000',
                size INTEGER DEFAULT 5,
                tool TEXT DEFAULT 'brush',
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("Таблица drawing_commands создана с поддержкой географических координат")
        
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
        
        await db.commit()
        print("✅ База данных инициализирована")

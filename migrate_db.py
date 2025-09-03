import sqlite3
import os
import asyncio
import aiosqlite
import sys

async def migrate_database():
    """Функция для миграции существующей базы данных для поддержки географических координат"""
    db_path = "drawing_sync.db"
    
    if not os.path.exists(db_path):
        print(f"База данных {db_path} не найдена. Миграция не требуется.")
        return
    
    print(f"Начинаем миграцию базы данных {db_path}...")
    
    try:
        # Подключение к БД
        async with aiosqlite.connect(db_path) as db:
            # Проверяем существование таблицы drawing_commands
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drawing_commands'")
            result = await cursor.fetchone()
            
            if not result:
                print("Таблица drawing_commands не найдена.")
                return
            
            # Проверяем структуру таблицы
            cursor = await db.execute("PRAGMA table_info(drawing_commands)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Проверяем наличие столбцов для географических координат
            changes_needed = False
            if 'lat' not in column_names:
                print("Добавление столбца lat...")
                await db.execute("ALTER TABLE drawing_commands ADD COLUMN lat REAL")
                changes_needed = True
            
            if 'lon' not in column_names:
                print("Добавление столбца lon...")
                await db.execute("ALTER TABLE drawing_commands ADD COLUMN lon REAL")
                changes_needed = True
            
            if 'is_geographical' not in column_names:
                print("Добавление столбца is_geographical...")
                await db.execute("ALTER TABLE drawing_commands ADD COLUMN is_geographical BOOLEAN DEFAULT FALSE")
                changes_needed = True
            
            # Создаем резервную копию базы данных перед изменениями
            if changes_needed:
                await db.commit()
                print("Миграция успешно завершена.")
            else:
                print("Миграция не требуется. База данных уже поддерживает географические координаты.")
            
    except Exception as e:
        print(f"Ошибка при миграции базы данных: {e}")
        return

if __name__ == "__main__":
    asyncio.run(migrate_database())
    print("Скрипт миграции завершен.")

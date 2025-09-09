import sqlite3
import asyncio
import os
from database import init_db

async def main():
    """Запуск міграції бази даних"""
    print("🔄 Запускаємо міграцію бази даних...")
    
    # Перевіряємо наявність бази даних
    db_exists = os.path.exists("drawing_sync.db")
    
    if db_exists:
        print("ℹ️ База даних вже існує")
        
        # Створюємо резервну копію
        print("📦 Створюємо резервну копію бази даних...")
        if os.path.exists("drawing_sync.db.bak"):
            os.remove("drawing_sync.db.bak")
        os.rename("drawing_sync.db", "drawing_sync.db.bak")
        print("✅ Резервна копія створена: drawing_sync.db.bak")
    
    # Ініціалізуємо базу даних (створюємо таблиці)
    await init_db()
    
    if db_exists:
        print("🔄 Відновлюємо дані з резервної копії...")
        
        # Переносимо дані зі старої структури в нову
        try:
            # Підключаємося до нової і старої БД
            conn_new = sqlite3.connect("drawing_sync.db")
            conn_old = sqlite3.connect("drawing_sync.db.bak")
            
            # Копіюємо дані з існуючих таблиць
            tables = [
                "drawing_commands", 
                "rooms", 
                "templates", 
                "app_versions"
            ]
            
            for table in tables:
                try:
                    print(f"🔄 Перенос даних таблиці {table}...")
                    
                    # Отримуємо список колонок
                    cursor_old = conn_old.execute(f"PRAGMA table_info({table})")
                    columns = [column[1] for column in cursor_old.fetchall()]
                    
                    if not columns:
                        print(f"⚠️ Таблиця {table} не знайдена в старій БД, пропускаємо")
                        continue
                    
                    # Отримуємо дані
                    cursor_old = conn_old.execute(f"SELECT * FROM {table}")
                    rows = cursor_old.fetchall()
                    
                    if not rows:
                        print(f"ℹ️ Таблиця {table} порожня, пропускаємо")
                        continue
                    
                    # Вставляємо дані в нову таблицю
                    placeholders = ', '.join(['?' for _ in columns])
                    columns_str = ', '.join(columns)
                    
                    for row in rows:
                        conn_new.execute(
                            f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                            row
                        )
                    
                    conn_new.commit()
                    print(f"✅ Дані таблиці {table} перенесені: {len(rows)} записів")
                    
                except Exception as e:
                    print(f"❌ Помилка переносу таблиці {table}: {e}")
            
            conn_new.close()
            conn_old.close()
            print("✅ Міграція даних завершена")
            
        except Exception as e:
            print(f"❌ Помилка міграції: {e}")
    
    print("✅ Міграція бази даних завершена успішно")

if __name__ == "__main__":
    asyncio.run(main())

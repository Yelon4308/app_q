"""
Файл конфігурації для сервера синхронізації
"""

# Налаштування сервера
HOST = "0.0.0.0"       # Слухати на всіх інтерфейсах
PORT = 8000            # Порт
DEBUG = True           # Режим налагодження (змінити на False у продакшені)

# Налаштування бази даних
DATABASE_PATH = "drawing_sync.db"

# Налаштування додатку
APP_NAME = "Штаб на пожежі"
APP_DESCRIPTION = "Додаток для координації дій рятувальних служб"
APP_VERSION = "1.0.0"

# Шляхи до оновлень
UPDATES_DIR = "static/updates"
ANDROID_UPDATES_DIR = f"{UPDATES_DIR}/android"
WINDOWS_UPDATES_DIR = f"{UPDATES_DIR}/windows"
LINUX_UPDATES_DIR = f"{UPDATES_DIR}/linux"

# Додаткові налаштування
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 МБ максимальний розмір файлу для завантаження
MAX_ROOM_HISTORY = 1000              # Максимальна кількість команд для зберігання в історії кімнати

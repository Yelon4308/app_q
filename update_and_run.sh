#!/bin/bash
# Скрипт для оновлення та запуску сервера подій малювання

# Кольори для виводу
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функція для виводу повідомлень
function log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

function error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Перевірка наявності Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 не встановлено. Будь ласка, встановіть Python 3."
    exit 1
fi

# Перевірка наявності pip
if ! command -v pip &> /dev/null; then
    error "pip не встановлено. Будь ласка, встановіть pip."
    exit 1
fi

# Оновлення залежностей
log "Оновлення залежностей..."
pip install -r requirements.txt || {
    error "Помилка встановлення залежностей."
    exit 1
}

# Виконання міграції бази даних
log "Виконання міграції бази даних..."
python3 migrate_db.py || {
    error "Помилка міграції бази даних."
    exit 1
}

# Запуск сервера
log "Запуск сервера..."
if [ "$1" == "--debug" ]; then
    log "Режим налагодження з автоперезавантаженням"
    python3 run_server.py --reload --log-level debug
else
    python3 run_server.py
fi

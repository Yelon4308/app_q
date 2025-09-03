#!/usr/bin/env python3
"""
Запуск Drawing Sync Server в продакшене
"""
import uvicorn
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Drawing Sync Server")
    parser.add_argument("--host", default="0.0.0.0", help="Хост сервера")
    parser.add_argument("--port", type=int, default=8000, help="Порт сервера")
    parser.add_argument("--reload", action="store_true", help="Автоперезагрузка при изменениях")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    
    args = parser.parse_args()
    
    print(f"""
🚀 Запуск Drawing Sync Server
📡 Хост: {args.host}
🔌 Порт: {args.port}
📝 Лог уровень: {args.log_level}
🔄 Автоперезагрузка: {args.reload}
    """)
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()

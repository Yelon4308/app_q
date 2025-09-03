"""
Адаптер для запуску сервера на Render
"""
import os
import sys
import uvicorn

def main():
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()

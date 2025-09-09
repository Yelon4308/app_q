#!/usr/bin/env python3
"""
Скрипт для загрузки новых версий приложений на сервер
"""
import requests
import os
import argparse
from pathlib import Path

class AppUploader:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        
    def upload_version(self, platform, version, file_path, release_notes, is_required=False):
        """Загрузка новой версии приложения"""
        
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return False
            
        # Проверка расширения файла
        valid_extensions = {
            "android": [".apk"],
            "windows": [".exe", ".msi"],
            "linux": [".AppImage", ".deb", ".rpm"]
        }
        
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in valid_extensions.get(platform, []):
            print(f"❌ Неверное расширение {file_extension} для платформы {platform}")
            return False
        
        print(f"📤 Загрузка {platform} v{version}...")
        print(f"📁 Файл: {file_path}")
        print(f"📝 Размер: {os.path.getsize(file_path) / 1024 / 1024:.1f} MB")
        
        url = f"{self.server_url}/api/updates/upload/{platform}"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'version': version,
                    'release_notes': release_notes,
                    'is_required': str(is_required).lower()
                }
                
                response = requests.post(url, files=files, data=data, timeout=300)
                
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Успешно загружено!")
                print(f"🔗 URL скачивания: {result['download_url']}")
                return True
            else:
                print(f"❌ Ошибка загрузки: {response.status_code}")
                print(f"📄 Ответ: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def check_latest_version(self, platform):
        """Проверка последней версии"""
        try:
            url = f"{self.server_url}/api/updates/check/{platform}"
            response = requests.get(url, params={"current_version": "0.0.0"})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("has_update"):
                    print(f"📱 Последняя версия для {platform}: {data['latest_version']}")
                    print(f"📝 Описание: {data['release_notes']}")
                else:
                    print(f"📱 Версии для {platform} не найдены")
            else:
                print(f"❌ Ошибка проверки: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description="Загрузка версий приложения")
    parser.add_argument("action", choices=["upload", "check"], help="Действие")
    parser.add_argument("--platform", choices=["android", "windows", "linux"], help="Платформа")
    parser.add_argument("--version", help="Версия приложения (например, 1.0.0)")
    parser.add_argument("--file", help="Путь к файлу приложения")
    parser.add_argument("--notes", help="Описание изменений")
    parser.add_argument("--required", action="store_true", help="Обязательное обновление")
    parser.add_argument("--server", default="http://localhost:8000", help="URL сервера")
    
    args = parser.parse_args()
    
    uploader = AppUploader(args.server)
    
    if args.action == "upload":
        if not all([args.platform, args.version, args.file, args.notes]):
            print("❌ Для загрузки нужны параметры: --platform, --version, --file, --notes")
            return
            
        uploader.upload_version(
            args.platform, 
            args.version, 
            args.file, 
            args.notes, 
            args.required
        )
        
    elif args.action == "check":
        if args.platform:
            uploader.check_latest_version(args.platform)
        else:
            for platform in ["android", "windows", "linux"]:
                uploader.check_latest_version(platform)
                print()

if __name__ == "__main__":
    # Примеры использования:
    print("📱 App Version Uploader")
    print()
    print("Примеры использования:")
    print("python upload_app.py upload --platform android --version 1.0.0 --file app.apk --notes 'Первый релиз'")
    print("python upload_app.py check --platform android")
    print("python upload_app.py check  # Проверить все платформы")
    print()
    
    main()

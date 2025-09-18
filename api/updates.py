from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
import os
import shutil
from datetime import datetime
from typing import Optional

from database import Database
from models.drawing import AppVersion

router = APIRouter()
db = Database()

# Создаем папки для файлов обновлений
os.makedirs("static/updates/android", exist_ok=True)
os.makedirs("static/updates/windows", exist_ok=True)
os.makedirs("static/updates/linux", exist_ok=True)

@router.get("/check/{platform}")
async def check_updates(platform: str, current_version: str = "1.0.0"):
    """Проверка обновлений для платформы"""
    if platform not in ["android", "windows", "linux"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемая платформа")
    
    latest = await db.get_latest_version(platform)
    
    if not latest:
        return {
            "has_update": False,
            "message": "Обновления не найдены"
        }
    
    # Простое сравнение версий (в реальном проекте лучше использовать semver)
    has_update = latest["version"] != current_version
    
    return {
        "has_update": has_update,
        "current_version": current_version,
        "latest_version": latest["version"],
        "download_url": f"/api/updates/download/{platform}",
        "file_size": latest["file_size"],
        "release_notes": latest["release_notes"],
        "is_required": latest["is_required"],
        "updated_at": latest["created_at"]
    }

@router.get("/download/{platform}")
async def download_update(platform: str):
    """Скачивание обновления"""
    if platform not in ["android", "windows", "linux"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемая платформа")
    
    latest = await db.get_latest_version(platform)
    
    if not latest:
        raise HTTPException(status_code=404, detail="Обновление не найдено")
    
    # Определяем расширение файла
    extensions = {
        "android": ".apk",
        "windows": ".exe", 
        "linux": ".AppImage"
    }
    
    file_path = f"static/updates/{platform}/app{extensions[platform]}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл обновления не найден")
    
    filename = f"DrawingApp_{latest['version']}{extensions[platform]}"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.post("/upload/{platform}")
async def upload_update(
    platform: str,
    version: str = Form(...),
    release_notes: str = Form(...),
    is_required: bool = Form(False),
    file: UploadFile = File(...)
):
    """Загрузка нового обновления (для администрирования)"""
    if platform not in ["android", "windows", "linux"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемая платформа")
    
    # Проверяем расширение файла
    valid_extensions = {
        "android": [".apk"],
        "windows": [".exe", ".msi"],
        "linux": [".AppImage", ".deb", ".rpm"]
    }
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in valid_extensions[platform]:
        raise HTTPException(
            status_code=400, 
            detail=f"Неверное расширение файла для {platform}: {file_extension}"
        )
    
    # Определяем путь для сохранения
    if platform == "android":
        save_path = "static/updates/android/app.apk"
    elif platform == "windows":
        save_path = "static/updates/windows/app.exe"
    else:  # linux
        save_path = "static/updates/linux/app.AppImage"
    
    # Сохраняем файл
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(save_path)
        
        # Сохраняем информацию о версии в БД
        app_version = AppVersion(
            platform=platform,
            version=version,
            download_url=f"/api/updates/download/{platform}",
            file_size=file_size,
            release_notes=release_notes,
            is_required=is_required,
            created_at=datetime.now()
        )
        
        await db.save_app_version(app_version)
        
        return {
            "success": True,
            "message": f"Обновление для {platform} v{version} успешно загружено",
            "file_size": file_size,
            "download_url": f"/api/updates/download/{platform}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")

@router.get("/versions/{platform}")
async def get_version_history(platform: str):
    """История версий для платформы"""
    if platform not in ["android", "windows", "linux"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемая платформа")
    
    # Тут можно добавить логику для получения всех версий из БД
    latest = await db.get_latest_version(platform)
    
    if latest:
        return {"versions": [latest]}
    else:
        return {"versions": []}

@router.delete("/versions/{platform}")
async def delete_version(platform: str):
    """Удаление версии (для администрирования)"""
    if platform not in ["android", "windows", "linux"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемая платформа")
    
    # Логика удаления файла и записи из БД
    # Пока что просто заглушка
    return {"message": f"Версия для {platform} удалена"}

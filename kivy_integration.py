"""
Пример интеграции Drawing Sync Server с Kivy приложением
"""
import asyncio
import websockets
import json
import requests
import threading
from datetime import datetime

class DrawingSyncClient:
    """Клиент для синхронизации рисования с сервером"""
    
    def __init__(self, server_url="ws://localhost:8000", room_id="default"):
        self.server_url = server_url
        self.room_id = room_id
        self.websocket = None
        self.connected = False
        self.callbacks = {
            'on_drawing': None,
            'on_clear': None,
            'on_template': None,
            'on_user_joined': None,
            'on_user_left': None
        }
        
    def set_callback(self, event_type, callback_function):
        """Установка callback функций для обработки событий"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback_function
    
    async def connect(self):
        """Подключение к серверу"""
        try:
            uri = f"{self.server_url}/ws/{self.room_id}"
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print(f"✅ Подключен к комнате: {self.room_id}")
            
            # Запускаем обработчик сообщений
            await self._message_handler()
            
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Отключение от сервера"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print("❌ Отключен от сервера")
    
    async def send_drawing_command(self, x, y, action="draw", color="#000000", size=5, tool="brush"):
        """Отправка команды рисования"""
        if not self.connected:
            return False
            
        command = {
            "type": "drawing",
            "x": x,
            "y": y,
            "action": action,
            "color": color,
            "size": size,
            "tool": tool
        }
        
        try:
            await self.websocket.send(json.dumps(command))
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки команды: {e}")
            return False
    
    async def clear_canvas(self):
        """Очистка холста"""
        if not self.connected:
            return False
            
        try:
            await self.websocket.send(json.dumps({"type": "clear"}))
            return True
        except Exception as e:
            print(f"❌ Ошибка очистки: {e}")
            return False
    
    async def send_template(self, template_data):
        """Отправка шаблона"""
        if not self.connected:
            return False
            
        try:
            await self.websocket.send(json.dumps({
                "type": "template",
                "data": template_data
            }))
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки шаблона: {e}")
            return False
    
    async def _message_handler(self):
        """Обработчик входящих сообщений"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Соединение закрыто")
            self.connected = False
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
    
    async def _handle_message(self, data):
        """Обработка конкретного сообщения"""
        message_type = data.get("type")
        
        if message_type == "drawing" and self.callbacks['on_drawing']:
            drawing_data = data.get("data", {})
            self.callbacks['on_drawing'](drawing_data)
            
        elif message_type == "clear" and self.callbacks['on_clear']:
            self.callbacks['on_clear']()
            
        elif message_type == "template" and self.callbacks['on_template']:
            template_data = data.get("data", {})
            self.callbacks['on_template'](template_data)
            
        elif message_type == "user_joined" and self.callbacks['on_user_joined']:
            self.callbacks['on_user_joined'](data)
            
        elif message_type == "user_left" and self.callbacks['on_user_left']:
            self.callbacks['on_user_left'](data)
    
    def run_in_thread(self):
        """Запуск клиента в отдельном потоке"""
        def run_client():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect())
        
        thread = threading.Thread(target=run_client, daemon=True)
        thread.start()
        return thread

class UpdateChecker:
    """Проверка обновлений приложения"""
    
    def __init__(self, server_url="http://localhost:8000", platform="android"):
        self.server_url = server_url
        self.platform = platform
    
    def check_for_updates(self, current_version="1.0.0"):
        """Проверка наличия обновлений"""
        try:
            url = f"{self.server_url}/api/updates/check/{self.platform}"
            params = {"current_version": current_version}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Ошибка проверки обновлений: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка подключения к серверу обновлений: {e}")
            return None
    
    def download_update(self, save_path="update_file"):
        """Скачивание обновления"""
        try:
            url = f"{self.server_url}/api/updates/download/{self.platform}"
            
            response = requests.get(url, timeout=30, stream=True)
            
            if response.status_code == 200:
                # Определяем расширение файла
                extension = ".apk" if self.platform == "android" else ".exe" if self.platform == "windows" else ".AppImage"
                full_path = f"{save_path}{extension}"
                
                with open(full_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ Обновление скачано: {full_path}")
                return full_path
            else:
                print(f"❌ Ошибка скачивания: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка скачивания обновления: {e}")
            return None

# Пример использования в Kivy приложении
class KivyDrawingApp:
    """Пример интеграции с Kivy приложением"""
    
    def __init__(self):
        self.sync_client = DrawingSyncClient(room_id="my_room")
        self.update_checker = UpdateChecker(platform="android")  # или "windows", "linux"
        
        # Настройка callbacks
        self.sync_client.set_callback('on_drawing', self.on_remote_drawing)
        self.sync_client.set_callback('on_clear', self.on_remote_clear)
        self.sync_client.set_callback('on_template', self.on_remote_template)
        self.sync_client.set_callback('on_user_joined', self.on_user_joined)
        self.sync_client.set_callback('on_user_left', self.on_user_left)
    
    def start_sync(self):
        """Запуск синхронизации"""
        self.sync_client.run_in_thread()
    
    def on_remote_drawing(self, drawing_data):
        """Обработка команды рисования от другого пользователя"""
        print(f"🎨 Рисование: {drawing_data}")
        # Тут нужно применить команду рисования к холсту Kivy
        # self.canvas.apply_drawing_command(drawing_data)
    
    def on_remote_clear(self):
        """Обработка очистки холста"""
        print("🧹 Очистка холста")
        # self.canvas.clear()
    
    def on_remote_template(self, template_data):
        """Обработка добавления шаблона"""
        print(f"📄 Шаблон: {template_data}")
        # self.canvas.add_template(template_data)
    
    def on_user_joined(self, user_data):
        """Пользователь присоединился"""
        print(f"👋 Пользователь присоединился: {user_data}")
    
    def on_user_left(self, user_data):
        """Пользователь покинул комнату"""
        print(f"👋 Пользователь ушел: {user_data}")
    
    def send_drawing(self, x, y, action="draw", color="#000000", size=5, tool="brush"):
        """Отправка команды рисования"""
        # Вызывается при рисовании пользователем
        asyncio.create_task(
            self.sync_client.send_drawing_command(x, y, action, color, size, tool)
        )
    
    def clear_canvas(self):
        """Очистка холста"""
        asyncio.create_task(self.sync_client.clear_canvas())
    
    def check_updates(self):
        """Проверка обновлений"""
        current_version = "1.0.0"  # Версия вашего приложения
        update_info = self.update_checker.check_for_updates(current_version)
        
        if update_info and update_info.get("has_update"):
            print(f"🔄 Доступно обновление: {update_info['latest_version']}")
            print(f"📝 Описание: {update_info['release_notes']}")
            
            if update_info.get("is_required"):
                print("⚠️ Обязательное обновление!")
            
            # Можно показать диалог пользователю
            return update_info
        else:
            print("✅ У вас последняя версия")
            return None

# Пример запуска
if __name__ == "__main__":
    app = KivyDrawingApp()
    
    # Проверяем обновления
    app.check_updates()
    
    # Запускаем синхронизацию
    app.start_sync()
    
    # Имитация рисования
    import time
    time.sleep(2)  # Ждем подключения
    
    # Отправляем тестовую команду рисования
    app.send_drawing(100, 200, "draw", "#FF0000", 5, "brush")

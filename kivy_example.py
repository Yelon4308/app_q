"""
Минимальный пример интеграции Drawing Sync с Kivy приложением
Адаптируйте этот код под ваше существующее приложение
"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.graphics import Line, Color, Ellipse
from kivy.clock import Clock
import asyncio
import websockets
import json
import threading
from datetime import datetime

class DrawingSyncWidget(Widget):
    """Виджет с поддержкой синхронизации рисования"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Настройки синхронизации
        self.server_url = "ws://localhost:8000"  # Замените на ваш сервер
        self.room_id = "kivy_room"
        self.websocket = None
        self.is_connected = False
        
        # Настройки рисования
        self.current_line = None
        self.is_drawing = False
        self.current_color = [1, 0, 0, 1]  # Красный
        self.line_width = 3
        
        # Привязка событий
        self.bind(on_touch_down=self.on_touch_down)
        self.bind(on_touch_move=self.on_touch_move)
        self.bind(on_touch_up=self.on_touch_up)
    
    def connect_to_server(self):
        """Подключение к серверу в отдельном потоке"""
        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._websocket_client())
        
        thread = threading.Thread(target=run_websocket, daemon=True)
        thread.start()
    
    async def _websocket_client(self):
        """WebSocket клиент"""
        try:
            uri = f"{self.server_url}/ws/{self.room_id}"
            print(f"🔌 Подключение к {uri}")
            
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.is_connected = True
                print(f"✅ Подключен к комнате {self.room_id}")
                
                # Обработка входящих сообщений
                async for message in websocket:
                    data = json.loads(message)
                    self._handle_server_message(data)
                    
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            self.is_connected = False
    
    def _handle_server_message(self, data):
        """Обработка сообщений от сервера"""
        if data.get("type") == "drawing":
            drawing_data = data.get("data", {})
            # Планируем выполнение в главном потоке Kivy
            Clock.schedule_once(lambda dt: self._apply_remote_drawing(drawing_data), 0)
        
        elif data.get("type") == "clear":
            Clock.schedule_once(lambda dt: self._clear_canvas(), 0)
        
        elif data.get("type") == "user_joined":
            print(f"👋 Пользователь присоединился. Всего: {data.get('total_users', 0)}")
        
        elif data.get("type") == "user_left":
            print(f"👋 Пользователь ушел. Всего: {data.get('total_users', 0)}")
    
    def _apply_remote_drawing(self, drawing_data):
        """Применение команды рисования от другого пользователя"""
        x = drawing_data.get("x", 0)
        y = drawing_data.get("y", 0)
        action = drawing_data.get("action", "draw")
        color_hex = drawing_data.get("color", "#FF0000")
        size = drawing_data.get("size", 3)
        
        # Конвертируем HEX в RGB для Kivy
        color_rgb = self._hex_to_rgb(color_hex)
        
        with self.canvas:
            if action == "down":
                Color(*color_rgb)
                self.remote_line = Line(points=[x, y], width=size)
            elif action == "draw" and hasattr(self, 'remote_line'):
                self.remote_line.points += [x, y]
            elif action == "up":
                self.remote_line = None
    
    def _clear_canvas(self):
        """Очистка холста"""
        self.canvas.clear()
    
    def _hex_to_rgb(self, hex_color):
        """Конвертация HEX в RGB для Kivy"""
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4)] + [1.0]
    
    def _rgb_to_hex(self, rgb_color):
        """Конвертация RGB в HEX"""
        return "#{:02x}{:02x}{:02x}".format(
            int(rgb_color[0] * 255),
            int(rgb_color[1] * 255),
            int(rgb_color[2] * 255)
        )
    
    def send_drawing_command(self, x, y, action):
        """Отправка команды рисования на сервер"""
        if not self.is_connected or not self.websocket:
            return
        
        command = {
            "type": "drawing",
            "x": x,
            "y": y,
            "action": action,
            "color": self._rgb_to_hex(self.current_color),
            "size": self.line_width,
            "tool": "brush"
        }
        
        # Отправляем асинхронно
        def send_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.websocket.send(json.dumps(command)))
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
        
        threading.Thread(target=send_async, daemon=True).start()
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_drawing = True
            
            # Рисуем локально
            with self.canvas:
                Color(*self.current_color)
                self.current_line = Line(points=[touch.x, touch.y], width=self.line_width)
            
            # Отправляем на сервер
            self.send_drawing_command(touch.x, touch.y, "down")
            return True
        return False
    
    def on_touch_move(self, touch):
        if self.is_drawing and self.collide_point(*touch.pos):
            if self.current_line:
                self.current_line.points += [touch.x, touch.y]
            
            # Отправляем на сервер
            self.send_drawing_command(touch.x, touch.y, "draw")
            return True
        return False
    
    def on_touch_up(self, touch):
        if self.is_drawing:
            self.is_drawing = False
            self.current_line = None
            
            # Отправляем на сервер
            self.send_drawing_command(touch.x, touch.y, "up")
            return True
        return False
    
    def clear_canvas(self):
        """Очистка холста и отправка команды на сервер"""
        self.canvas.clear()
        
        if self.is_connected and self.websocket:
            def send_clear():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.websocket.send(json.dumps({"type": "clear"})))
                except Exception as e:
                    print(f"❌ Ошибка очистки: {e}")
            
            threading.Thread(target=send_clear, daemon=True).start()
    
    def change_color(self, color):
        """Изменение цвета кисти"""
        self.current_color = color
    
    def change_size(self, size):
        """Изменение размера кисти"""
        self.line_width = size

class DrawingSyncApp(App):
    """Пример Kivy приложения с синхронизацией"""
    
    def build(self):
        # Основной layout
        root = BoxLayout(orientation='vertical')
        
        # Информационная панель
        info_layout = BoxLayout(size_hint=(1, 0.1), orientation='horizontal')
        
        room_input = TextInput(
            text='kivy_room',
            size_hint=(0.3, 1),
            multiline=False
        )
        
        connect_btn = Button(
            text='Подключиться',
            size_hint=(0.2, 1)
        )
        
        status_label = Label(
            text='Не подключен',
            size_hint=(0.5, 1)
        )
        
        info_layout.add_widget(Label(text='Комната:', size_hint=(0.1, 1)))
        info_layout.add_widget(room_input)
        info_layout.add_widget(connect_btn)
        info_layout.add_widget(status_label)
        
        # Виджет для рисования
        drawing_widget = DrawingSyncWidget(size_hint=(1, 0.8))
        
        # Панель управления
        controls = BoxLayout(size_hint=(1, 0.1), orientation='horizontal')
        
        # Кнопки цветов
        red_btn = Button(text='🔴', size_hint=(0.1, 1))
        green_btn = Button(text='🟢', size_hint=(0.1, 1))
        blue_btn = Button(text='🔵', size_hint=(0.1, 1))
        black_btn = Button(text='⚫', size_hint=(0.1, 1))
        
        # Кнопки размера
        small_btn = Button(text='◦', size_hint=(0.1, 1))
        medium_btn = Button(text='●', size_hint=(0.1, 1))
        large_btn = Button(text='⬤', size_hint=(0.1, 1))
        
        # Кнопка очистки
        clear_btn = Button(text='Очистить', size_hint=(0.2, 1))
        
        # Привязка событий
        def connect_to_room(instance):
            drawing_widget.room_id = room_input.text
            drawing_widget.connect_to_server()
            status_label.text = f'Подключение к {room_input.text}...'
        
        connect_btn.bind(on_press=connect_to_room)
        
        red_btn.bind(on_press=lambda x: drawing_widget.change_color([1, 0, 0, 1]))
        green_btn.bind(on_press=lambda x: drawing_widget.change_color([0, 1, 0, 1]))
        blue_btn.bind(on_press=lambda x: drawing_widget.change_color([0, 0, 1, 1]))
        black_btn.bind(on_press=lambda x: drawing_widget.change_color([0, 0, 0, 1]))
        
        small_btn.bind(on_press=lambda x: drawing_widget.change_size(2))
        medium_btn.bind(on_press=lambda x: drawing_widget.change_size(5))
        large_btn.bind(on_press=lambda x: drawing_widget.change_size(10))
        
        clear_btn.bind(on_press=lambda x: drawing_widget.clear_canvas())
        
        # Добавляем элементы
        controls.add_widget(red_btn)
        controls.add_widget(green_btn)
        controls.add_widget(blue_btn)
        controls.add_widget(black_btn)
        controls.add_widget(Label(text='|', size_hint=(0.05, 1)))
        controls.add_widget(small_btn)
        controls.add_widget(medium_btn)
        controls.add_widget(large_btn)
        controls.add_widget(Label(text='|', size_hint=(0.05, 1)))
        controls.add_widget(clear_btn)
        
        root.add_widget(info_layout)
        root.add_widget(drawing_widget)
        root.add_widget(controls)
        
        # Автоподключение при запуске
        Clock.schedule_once(lambda dt: connect_to_room(None), 1)
        
        return root

if __name__ == '__main__':
    # Установите необходимые зависимости:
    # pip install kivy websockets
    
    DrawingSyncApp().run()

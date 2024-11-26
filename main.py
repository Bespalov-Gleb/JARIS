import flet as ft
import logging
import os
import asyncio
from dotenv import load_dotenv
from typing import Optional
from screeninfo import get_monitors

from jarvis_v2 import Jarvis, JarvisConfig
from db_pkg.database import Database
from db_pkg.models import User

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Message(ft.Row):
    """Компонент сообщения в чате"""
    def __init__(self, user_name: str, message_type: str, message: str):
        super().__init__()
        self.user_name = user_name
        self.message_type = message_type
        self.message = message
        self.vertical_alignment = "start"
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(user_name)),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(user_name),
            ),
            ft.Column(
                [
                    ft.Text(user_name, weight="bold"),
                    ft.Text(message, selectable=True),
                ],
                tight=True,
                spacing=5,
            ),
        ]

    def get_initials(self, user_name: str) -> str:
        return user_name[:1].capitalize() if user_name else "?"

    def get_avatar_color(self, user_name: str) -> str:
        colors = [
            ft.colors.AMBER, ft.colors.BLUE, ft.colors.BROWN,
            ft.colors.CYAN, ft.colors.GREEN, ft.colors.INDIGO,
            ft.colors.LIME, ft.colors.ORANGE, ft.colors.PINK,
            ft.colors.PURPLE, ft.colors.RED, ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors[hash(user_name) % len(colors)]

class JarvisGUI:
    """Графический интерфейс голосового ассистента"""
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self.initialize_jarvis()
        self.setup_ui()

    def setup_page(self) -> None:
        """Настройка параметров страницы"""
        try:
            monitor = get_monitors()[0]
            self.page.title = 'JARVIS'
            self.page.theme_mode = 'SYSTEM'
            self.page.window_width = monitor.width
            self.page.window_height = monitor.height
            self.page.window_resizable = True
            self.page.vertical_alignment = 'center'
            self.page.horizontal_alignment = 'center'
            self.page.update()
        except Exception as e:
            logger.error(f"Failed to setup page: {str(e)}")
            raise

    def initialize_jarvis(self) -> None:
        """Инициализация ядра голосового ассистента"""
        try:
            load_dotenv()
            picovoice_token = os.getenv('PICOVOICE_TOKEN')
            eden_token = os.getenv('EDEN_AI_TOKEN')
            openai_token = os.getenv('OPENAI_TOKEN')
            
            if not all([picovoice_token, eden_token]):
                raise ValueError("Missing required environment variables")
                
            config = JarvisConfig(
                picovoice_token=picovoice_token,
                eden_token=eden_token,
                openai_token=openai_token
            )
                
            self.jarvis = Jarvis(config)
        except Exception as e:
            logger.error(f"Failed to initialize Jarvis: {str(e)}")
            raise

    def setup_ui(self) -> None:
        """Настройка пользовательского интерфейса"""
        try:
            # Создание основных элементов интерфейса
            self.chat_messages = ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.ALWAYS,
                height=400,
            )

            self.input_field = ft.TextField(
                hint_text="Введите команду...",
                border=ft.InputBorder.OUTLINE,
                expand=True,
                on_submit=self.send_message,
            )

            self.send_button = ft.IconButton(
                icon=ft.icons.SEND_ROUNDED,
                tooltip="Отправить",
                on_click=self.send_message,
            )

            self.voice_button = ft.IconButton(
                icon=ft.icons.MIC,
                tooltip="Голосовой ввод",
                on_click=self.toggle_voice_input,
            )

            # Компоновка элементов
            self.page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("JARVIS", size=30, weight=ft.FontWeight.BOLD),
                        self.chat_messages,
                        ft.Row([
                            self.input_field,
                            self.send_button,
                            self.voice_button,
                        ]),
                    ]),
                    padding=20,
                )
            )
        except Exception as e:
            logger.error(f"Failed to setup UI: {str(e)}")
            raise

    async def send_message(self, e=None) -> None:
        """Обработка отправки сообщения"""
        try:
            if not self.input_field.value:
                return

            message = self.input_field.value
            self.input_field.value = ""
            self.page.update()

            # Добавляем сообщение пользователя
            self.add_chat_message("User", "user", message)

            # Обрабатываем команду
            await self.jarvis.process_command(message)

            # Получаем последнее сообщение ассистента
            history = self.jarvis.state_manager.get_message_history(1)
            if history and history[-1]["role"] == "assistant":
                self.add_chat_message(
                    "JARVIS",
                    "assistant",
                    history[-1]["content"]
                )
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.add_chat_message(
                "System",
                "error",
                "Произошла ошибка при обработке команды"
            )

    def add_chat_message(self, user: str, type: str, message: str) -> None:
        """Добавление сообщения в чат"""
        try:
            self.chat_messages.controls.append(Message(user, type, message))
            self.page.update()
            self.chat_messages.scroll_to(offset=float('inf'))
        except Exception as e:
            logger.error(f"Failed to add chat message: {str(e)}")

    def toggle_voice_input(self, e=None) -> None:
        """Переключение голосового ввода"""
        try:
            if self.jarvis.state_manager.state.is_listening:
                self.jarvis.stop()
                self.voice_button.icon = ft.icons.MIC
            else:
                self.jarvis.start()
                self.voice_button.icon = ft.icons.MIC_OFF
            self.page.update()
        except Exception as e:
            logger.error(f"Failed to toggle voice input: {str(e)}")
            self.add_chat_message(
                "System",
                "error",
                "Ошибка при работе с микрофоном"
            )

def main(page: ft.Page):
    """Точка входа в приложение"""
    try:
        app = JarvisGUI(page)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        page.add(
            ft.Text(
                "Failed to start application. Check logs for details.",
                color=ft.colors.RED
            )
        )

if __name__ == "__main__":
    ft.app(target=main)

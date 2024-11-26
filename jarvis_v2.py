import logging
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from core.voice_processor import VoiceProcessor
from core.tts_engine import TextToSpeech
from core.command_handler import CommandHandler
from core.state_manager import StateManager
from db_pkg.database import Database
from db_pkg.models import User

@dataclass
class JarvisConfig:
    picovoice_token: str
    eden_token: str
    openai_token: Optional[str] = None
    model_path: str = "assets/path/Svetlana_en_windows_v3_0_0.ppn"
    state_file: str = "jarvis_state.json"
    log_file: str = "jarvis.log"

class Jarvis:
    """
    Основной класс голосового ассистента JARIS.
    Управляет взаимодействием между компонентами и обработкой команд.
    """
    
    def __init__(self, config: JarvisConfig):
        """
        Инициализация ассистента
        
        Args:
            config: Конфигурация ассистента
        """
        # Настройка логирования
        logging.basicConfig(
            filename=config.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        try:
            # Инициализация компонентов
            self.voice_processor = VoiceProcessor(
                config.picovoice_token,
                config.model_path
            )
            self.tts_engine = TextToSpeech(config.eden_token)
            self.command_handler = CommandHandler()
            self.state_manager = StateManager(config.state_file)
            
            # Инициализация базы данных
            self.db = Database()
            self.user = self._init_user()
            
            self.logger.info("Jarvis initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Jarvis: {str(e)}")
            raise
            
    def _init_user(self) -> User:
        """Инициализация пользователя из базы данных"""
        try:
            user = self.db.get_query(User).filter(User.id == -1).first()
            if not user:
                self.logger.warning("User not found in database")
            return user
        except Exception as e:
            self.logger.error(f"Failed to initialize user: {str(e)}")
            raise

    async def process_voice_command(self) -> None:
        """Обработка голосовой команды"""
        try:
            # Получение аудио от voice processor
            audio_data = await self.voice_processor.get_audio()
            if not audio_data:
                return
                
            # Распознавание команды
            command = self.command_handler.find_command(audio_data)
            if not command:
                await self.tts_engine.synthesize_async("Команда не распознана")
                return
                
            # Выполнение команды
            response = await self.command_handler.execute_command(command)
            
            # Сохранение в историю
            self.state_manager.add_message("user", command)
            self.state_manager.add_message("assistant", response)
            
            # Озвучивание ответа
            await self.tts_engine.synthesize_async(response)
            
        except Exception as e:
            self.logger.error(f"Error processing voice command: {str(e)}")
            await self.tts_engine.synthesize_async("Произошла ошибка при обработке команды")

    async def start(self) -> None:
        """Запуск ассистента"""
        try:
            self.logger.info("Starting Jarvis")
            self.state_manager.update_state(is_running=True)
            
            while self.state_manager.state.is_running:
                await self.process_voice_command()
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}")
            raise
        finally:
            self.cleanup()
            
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        try:
            self.voice_processor.cleanup()
            self.state_manager.save_state()
            self.logger.info("Jarvis cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

if __name__ == '__main__':
    load_dotenv()
    
    config = JarvisConfig(
        picovoice_token=os.getenv('PICOVOICE_TOKEN'),
        eden_token=os.getenv('EDEN_AI_TOKEN'),
        openai_token=os.getenv('OPENAI_TOKEN')
    )
    
    jarvis = Jarvis(config)
    jarvis.start()

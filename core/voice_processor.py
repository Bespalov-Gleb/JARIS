import logging
from typing import Optional
import pvporcupine
from pvrecorder import PvRecorder
import os

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Компонент для обработки голосовых команд"""
    
    def __init__(self, picovoice_token: str, model_path: str):
        """
        Инициализация обработчика голоса
        
        Args:
            picovoice_token (str): Токен для Picovoice
            model_path (str): Путь к модели распознавания
        """
        self.picovoice_token = picovoice_token
        self.model_path = model_path
        self.porcupine = None
        self.recorder = None
        self._initialize_voice_processing()
    
    def _initialize_voice_processing(self) -> None:
        """Инициализация компонентов распознавания голоса"""
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.picovoice_token,
                keyword_paths=[os.path.join(os.getcwd(), "assets", "path", self.model_path)],
                sensitivities=[1]
            )
            self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
            logger.info("Voice processing initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize voice processing: {str(e)}")
            raise

    def start_recording(self) -> None:
        """Начать запись звука"""
        try:
            if not self.recorder:
                raise RuntimeError("Recorder not initialized")
            self.recorder.start()
            logger.info(f"Started recording using device: {self.recorder.selected_device}")
        except Exception as e:
            logger.error(f"Failed to start recording: {str(e)}")
            raise

    def stop_recording(self) -> None:
        """Остановить запись звука"""
        try:
            if self.recorder:
                self.recorder.stop()
                logger.info("Recording stopped")
        except Exception as e:
            logger.error(f"Failed to stop recording: {str(e)}")
            raise

    def process_frame(self, frame) -> Optional[int]:
        """
        Обработка звукового фрейма
        
        Args:
            frame: Звуковой фрейм для обработки
            
        Returns:
            Optional[int]: Индекс распознанного ключевого слова или None
        """
        try:
            return self.porcupine.process(frame) if self.porcupine else None
        except Exception as e:
            logger.error(f"Failed to process audio frame: {str(e)}")
            return None

    def cleanup(self) -> None:
        """Освобождение ресурсов"""
        try:
            if self.recorder:
                self.recorder.delete()
            if self.porcupine:
                self.porcupine.delete()
            logger.info("Voice processor resources cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup resources: {str(e)}")

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class AssistantState:
    """Состояние голосового ассистента"""
    is_listening: bool = False
    is_speaking: bool = False
    current_command: Optional[str] = None
    message_history: list = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

class StateManager:
    """Управление состоянием голосового ассистента"""
    
    def __init__(self, state_file: str = 'assistant_state.json'):
        """
        Инициализация менеджера состояний
        
        Args:
            state_file (str): Путь к файлу состояния
        """
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> AssistantState:
        """Загрузка состояния из файла"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return AssistantState(**data)
            return AssistantState()
        except Exception as e:
            logger.error(f"Failed to load state: {str(e)}")
            return AssistantState()

    def save_state(self) -> None:
        """Сохранение состояния в файл"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state.__dict__, f, ensure_ascii=False, indent=2)
            logger.info("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")

    def update_state(self, **kwargs) -> None:
        """
        Обновление состояния
        
        Args:
            **kwargs: Параметры для обновления
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
            self.save_state()
        except Exception as e:
            logger.error(f"Failed to update state: {str(e)}")

    def add_message(self, role: str, content: str) -> None:
        """
        Добавление сообщения в историю
        
        Args:
            role (str): Роль отправителя
            content (str): Содержание сообщения
        """
        try:
            self.state.message_history.append({
                "role": role,
                "content": content,
                "timestamp": time.time()
            })
            if len(self.state.message_history) > 100:  # Ограничиваем историю
                self.state.message_history = self.state.message_history[-100:]
            self.save_state()
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}")

    def get_message_history(self, limit: int = None) -> list:
        """
        Получение истории сообщений
        
        Args:
            limit (int, optional): Ограничение количества сообщений
            
        Returns:
            list: История сообщений
        """
        try:
            history = self.state.message_history
            if limit:
                history = history[-limit:]
            return history
        except Exception as e:
            logger.error(f"Failed to get message history: {str(e)}")
            return []

    def clear_history(self) -> None:
        """Очистка истории сообщений"""
        try:
            self.state.message_history = []
            self.save_state()
            logger.info("Message history cleared")
        except Exception as e:
            logger.error(f"Failed to clear history: {str(e)}")

    def get_settings(self) -> Dict[str, Any]:
        """
        Получение настроек
        
        Returns:
            Dict[str, Any]: Текущие настройки
        """
        return self.state.settings

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        Обновление настроек
        
        Args:
            new_settings (Dict[str, Any]): Новые настройки
        """
        try:
            self.state.settings.update(new_settings)
            self.save_state()
            logger.info("Settings updated successfully")
        except Exception as e:
            logger.error(f"Failed to update settings: {str(e)}")

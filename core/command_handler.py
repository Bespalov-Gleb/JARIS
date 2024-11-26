import logging
from typing import Dict, Any, Optional, List
import yaml
from fuzzywuzzy import fuzz
import webbrowser
import subprocess
import os

logger = logging.getLogger(__name__)

class CommandHandler:
    """Обработчик команд голосового ассистента"""
    
    def __init__(self, commands_file: str = 'commands.yaml'):
        """
        Инициализация обработчика команд
        
        Args:
            commands_file (str): Путь к файлу с командами
        """
        self.commands_file = commands_file
        self.commands = self._load_commands()
        self.command_cache: Dict[str, Dict[str, Any]] = {}

    def _load_commands(self) -> Dict[str, Any]:
        """Загрузка команд из файла"""
        try:
            with open(self.commands_file, 'r', encoding='utf-8') as f:
                commands = yaml.safe_load(f)
            logger.info("Commands loaded successfully")
            return commands
        except Exception as e:
            logger.error(f"Failed to load commands: {str(e)}")
            raise

    def find_command(self, user_input: str, threshold: int = 80) -> Optional[Dict[str, Any]]:
        """
        Поиск команды по пользовательскому вводу
        
        Args:
            user_input (str): Пользовательский ввод
            threshold (int): Порог схожести для нечеткого поиска
            
        Returns:
            Optional[Dict[str, Any]]: Найденная команда или None
        """
        try:
            # Проверяем кэш
            if user_input in self.command_cache:
                return self.command_cache[user_input]

            max_ratio = 0
            matched_command = None

            for cmd_name, cmd_info in self.commands.items():
                for variant in cmd_info.get('variants', []):
                    ratio = fuzz.ratio(user_input.lower(), variant.lower())
                    if ratio > max_ratio and ratio >= threshold:
                        max_ratio = ratio
                        matched_command = cmd_info

            # Сохраняем в кэш
            if matched_command:
                self.command_cache[user_input] = matched_command
                
            return matched_command
        except Exception as e:
            logger.error(f"Error finding command: {str(e)}")
            return None

    def execute_command(self, command: Dict[str, Any], **kwargs) -> bool:
        """
        Выполнение команды
        
        Args:
            command (Dict[str, Any]): Команда для выполнения
            **kwargs: Дополнительные параметры
            
        Returns:
            bool: Успешность выполнения команды
        """
        try:
            cmd_type = command.get('type')
            if not cmd_type:
                raise ValueError("Command type not specified")

            if cmd_type == 'browser':
                url = command.get('url')
                if url:
                    webbrowser.open(url)
                    return True
            elif cmd_type == 'system':
                cmd = command.get('command')
                if cmd:
                    subprocess.Popen(cmd, shell=True)
                    return True
            elif cmd_type == 'custom':
                # Выполнение пользовательских команд
                handler = command.get('handler')
                if handler and callable(handler):
                    handler(**kwargs)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            return False

    def add_custom_command(self, name: str, handler: callable, variants: List[str]) -> None:
        """
        Добавление пользовательской команды
        
        Args:
            name (str): Имя команды
            handler (callable): Функция-обработчик
            variants (List[str]): Варианты произношения команды
        """
        try:
            self.commands[name] = {
                'type': 'custom',
                'handler': handler,
                'variants': variants
            }
            logger.info(f"Added custom command: {name}")
        except Exception as e:
            logger.error(f"Failed to add custom command: {str(e)}")
            raise

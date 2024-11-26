import logging
import os
import requests
from typing import Optional
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class TextToSpeech:
    """Компонент для синтеза речи"""
    
    def __init__(self, eden_token: str):
        """
        Инициализация движка синтеза речи
        
        Args:
            eden_token (str): Токен для EdenAI API
        """
        self.eden_token = eden_token
        self.headers = {"Authorization": f"Bearer {eden_token}"}
        self.base_url = 'https://api.edenai.run/v2/audio/text_to_speech'

    async def synthesize_async(self, text: str) -> None:
        """
        Асинхронный синтез речи
        
        Args:
            text (str): Текст для синтеза
        """
        try:
            payload = {
                "providers": "lovoai",
                "language": "ru-RU",
                "option": "MALE",
                "lovoai": "ru-RU_Pyotr Semenov",
                "text": text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, headers=self.headers) as response:
                    if response.status != 200:
                        raise Exception(f"API request failed with status {response.status}")
                    
                    result = await response.json()
                    audio_url = result.get('lovoai', {}).get('audio_resource_url')
                    
                    if not audio_url:
                        raise ValueError("No audio URL in response")
                    
                    await self._save_audio_async(audio_url)
                    logger.info("Successfully synthesized speech")
                    
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {str(e)}")
            raise

    async def _save_audio_async(self, audio_url: str) -> None:
        """
        Асинхронное сохранение аудио файла
        
        Args:
            audio_url (str): URL для загрузки аудио
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download audio: {response.status}")
                    
                    content = await response.read()
                    file_name = 'moment_file.wav'
                    
                    with open(file_name, 'wb') as file:
                        file.write(content)
                    
                    os.replace(
                        f'{os.getcwd()}/moment_file.wav',
                        f'{os.getcwd()}/assets/sound/moment_file.wav'
                    )
                    
        except Exception as e:
            logger.error(f"Failed to save audio file: {str(e)}")
            raise

    def synthesize(self, text: str) -> None:
        """
        Синхронный метод синтеза речи
        
        Args:
            text (str): Текст для синтеза
        """
        asyncio.run(self.synthesize_async(text))

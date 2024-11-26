import unittest
import os
from unittest.mock import MagicMock, patch
from core.voice_processor import VoiceProcessor
from core.tts_engine import TextToSpeech
from core.command_handler import CommandHandler
from core.state_manager import StateManager

class TestVoiceProcessor(unittest.TestCase):
    def setUp(self):
        self.token = "test_token"
        self.model_path = "test_model.ppn"
        
    @patch('pvporcupine.create')
    @patch('pvrecorder.PvRecorder')
    def test_initialization(self, mock_recorder, mock_porcupine):
        processor = VoiceProcessor(self.token, self.model_path)
        self.assertIsNotNone(processor)
        mock_porcupine.assert_called_once()
        mock_recorder.assert_called_once()

    @patch('pvporcupine.create')
    @patch('pvrecorder.PvRecorder')
    def test_start_recording(self, mock_recorder, mock_porcupine):
        processor = VoiceProcessor(self.token, self.model_path)
        processor.start_recording()
        mock_recorder.return_value.start.assert_called_once()

class TestTextToSpeech(unittest.TestCase):
    def setUp(self):
        self.token = "test_token"
        self.tts = TextToSpeech(self.token)

    @patch('aiohttp.ClientSession')
    async def test_synthesis(self, mock_session):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'lovoai': {'audio_resource_url': 'http://test.com/audio.wav'}
        }
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        await self.tts.synthesize_async("test text")
        mock_session.return_value.__aenter__.return_value.post.assert_called_once()

class TestCommandHandler(unittest.TestCase):
    def setUp(self):
        self.handler = CommandHandler()

    def test_find_command(self):
        test_command = "открой браузер"
        result = self.handler.find_command(test_command)
        self.assertIsNotNone(result)

    def test_command_cache(self):
        test_command = "открой браузер"
        # Первый вызов - команда кэшируется
        first_result = self.handler.find_command(test_command)
        # Второй вызов - команда берется из кэша
        second_result = self.handler.find_command(test_command)
        self.assertEqual(first_result, second_result)

class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.state_file = "test_state.json"
        self.manager = StateManager(self.state_file)

    def tearDown(self):
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_update_state(self):
        self.manager.update_state(is_listening=True)
        self.assertTrue(self.manager.state.is_listening)

    def test_message_history(self):
        self.manager.add_message("user", "test message")
        history = self.manager.get_message_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["content"], "test message")

if __name__ == '__main__':
    unittest.main()

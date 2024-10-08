#Это версия без интерфейса, без подключения базы данных для одного пользователя

import json
import os
import random
import struct
import time
import traceback
import webbrowser
import platform

import vosk
from g4f.client import Client
import googlesearch
import pvporcupine
import simpleaudio as sa
import sounddevice as sd
import yaml
from fuzzywuzzy import fuzz
from pvrecorder import PvRecorder
from rich import print
from PyQt6 import QtWidgets
import sys
import requests
from gpt import gpt1


# TODO: переделать команду для чата: открывает нужную вкладку, печатает ответ и произносит его


class Jarvis:
    def __init__(self, picovoice_token, eden_token):
        self.picovoice_token = picovoice_token
        self.eden_token = eden_token

        self.message_log = [{"role": "system", "content": "Ты голосовой ассистент из железного человека."}]
        self.is_first_request = True
        self.VA_CMD_LIST = yaml.safe_load(open('commands.yaml', 'rt', encoding='utf8'), )
        self.CDIR = os.getcwd()
        path_file = "path_win.ppn" if platform.system() == "Windows" else "path_mac.ppn"
        self.porcupine = pvporcupine.create(
            access_key=self.picovoice_token,
            keyword_paths=[os.path.join(f"{self.CDIR}", "assets", "path", path_file)],
            model_path=os.path.join(f'{self.CDIR}', 'assets', 'path', 'porcupine_params_ru.pv'),
            sensitivities=[1]
        )
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)

    def tts(self, text):
        headers = {
            "Authorization": f"Bearer {self.eden_token}"}
        url = 'https://api.edenai.run/v2/audio/text_to_speech'
        payload = {
            "providers": "lovoai", "language": "ru-RU",
            "option": "MALE",
            "lovoai": "ru-RU_Pyotr Semenov",
            "text": f'{text}'
        }
        response = requests.post(url, json=payload, headers=headers)
        result = json.loads(response.text)

        audio_url = result.get('lovoai').get('audio_resource_url')
        file_name = 'moment_file.wav'

        with open(file_name, 'wb') as file:
            file.write(requests.get(audio_url).content)
            file.close()
        os.replace(f'{os.getcwd()}/moment_file.wav', f'{os.getcwd()}/assets/sound')

    def start_jarvis(self, kaldi_rec):
        self.recorder.start()
        print('Using device: %s' % self.recorder.selected_device)

        print(f"Jarvis (v3.0) начал свою работу ...")
        self.play('run')

        time.sleep(0.5)

        ltc = time.time() - 1000

        while True:
            try:
                pcm = self.recorder.read()
                keyword_index = self.porcupine.process(pcm)

                if keyword_index >= 0:
                    self.recorder.stop()
                    self.play("greet", True)
                    print("Yes, sir.")
                    self.recorder.start()  # prevent self-recording
                    ltc = time.time()

                while time.time() - ltc <= 4:
                    pcm = self.recorder.read()
                    sp = struct.pack("h" * len(pcm), *pcm)

                    if kaldi_rec.AcceptWaveform(sp):
                        if self.va_respond(json.loads(kaldi_rec.Result())["text"], type='base'):
                            ltc = time.time()

                        break

            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                raise

    def gpt_answer(self, question):
        client = Client()
        res = ''
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f'{question}'}],
            stream=True

        )
        for mes in response:
            res += mes
        return res

    # self.play(f'{CDIR}\\sound\\ok{random.choice([1, 2, 3, 4])}.wav')

    def main_connect(self, kaldi_rec):
        self.recorder.stop()
        self.play('gpt_start')
        self.recorder.start()

        return self.va_respond(json.loads(kaldi_rec.Result())["text"], type='gpt')

    def play(self, phrase, wait_done=True):
        filename = os.path.join(self.CDIR, "assets", "svet_audio")
        if phrase == "greet":  # for py 3.8
            filename = os.path.join(filename, f"{random.choice(['welcome', 'i_here', 'attention', 'hear_me'])}.wav")
        elif phrase == "ok":
            filename = os.path.join(filename, f"{random.choice(['done', 'yep', 'contact'])}.wav")
        elif phrase == "not_found":
            filename = os.path.join(filename, f"{random.choice(['bad_hear', 'can_you_rep'])}.wav")
        elif phrase == "thanks":
            filename = os.path.join(filename, "thanks.wav")
        elif phrase == "run":
            filename = os.path.join(filename, "listen.wav")
        elif phrase == "stupid":
            filename = os.path.join(filename, "just_learn.wav")
        elif phrase == "ready":
            filename = os.path.join(filename, "ready.wav")
        elif phrase == "off":
            filename = os.path.join(filename, f"{random.choice(['power_off.wav', 'see_u.wav', 'see_u_later.wav'])}")
        elif phrase == "loading":
            filename = os.path.join(filename, f"{random.choice(['check_sys', 'start_check'])}.wav")
        elif phrase == "result":
            filename = os.path.join(filename, "done.wav")
        elif phrase == 'new_fol':
            filename = os.path.join(filename, "folder_create.wav")
        elif phrase == 'new_file':
            filename = os.path.join(filename, 'file_create.wav')
        elif phrase == 'delete':
            filename = os.path.join(filename, 'done.wav')
        elif phrase == 'cong':
            filename = os.path.join(filename, f'{random.choice(["congratilations.wav", "glad.wav"])}')
        elif phrase == 'gpt_start':
            filename = os.path.join(filename, 'larger_find.wav')
        elif phrase == 'dir_name':
            filename = os.path.join(filename, 'another_name_fol.wav')
        elif phrase == 'file_name':
            filename = os.path.join(filename, 'another_name_file.wav')
        elif phrase == 'is_found':
            filename = os.path.join(filename, 'check_done.wav')
        elif phrase == 'nfs':
            filename = os.path.join(filename, 'nfs.wav')
        elif phrase == 'something_else':
            filename = os.path.join(filename, f'{random.choice(["dfa.wav", "strange.wav", "not_found.wav"])}')
        elif phrase == 'watching':
            filename = os.path.join(filename, 'glad_watching.wav')
        elif phrase == 'youtube':
            filename = os.path.join(filename, 'check_youtube.wav')
        elif phrase == 'not_found':
            filename = os.path.join(filename, 'strange.wav')
        elif phrase == 'moment_file':
            filename = os.path.join(filename, "moment_file.wav")
        elif phrase == 'subscribe':
            filename = os.path.join(filename, 'subscribe.wav.wav')
        elif phrase == 'switch_done':
            filename = os.path.join(filename, 'swith_done.wav')

        if wait_done:
            self.recorder.stop()

        print(filename)

        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()

        if wait_done:
            play_obj.wait_done()
            # time.sleep((len(wave_obj.audio_data) / wave_obj.sample_rate) + 0.5)
            # print("END")
            # time.sleep(0.5)
            self.recorder.start()

    def va_respond(self, voice: str, type: str):
        print(f"Распознано: {voice}")

        if type == 'base':
            cmd = self.recognize_cmd(self.filter_cmd(voice))

            print(cmd)
            if len(cmd['cmd'].strip()) <= 0:
                return False
            elif 'заметки' in cmd:
                self.create_note(voice)
            elif cmd['percent'] < 50 or cmd['cmd'] not in self.VA_CMD_LIST.keys():

                if fuzz.ratio(voice.join(voice.split()[:1]).strip(), "скажи") > 75:
                    self.play('gpt_start')
                    if self.is_first_request:
                        self.message_log.append({"role": "user", "content": voice})
                        self.is_first_request = True
                        response = self.gpt_answer(voice)
                        self.message_log.append({"role": "assistant", "content": response})
                        self.recorder.stop()
                        if len(response) < 1000:

                            self.tts(response)
                            # pr_tts = multiprocessing.Process(target=self.tts(response), name='tts')
                            # pr_tts.start()
                            # text_gpt = multiprocessing.Process(target=)
                            self.play('moment_file')
                            os.remove('moment_file.wav')
                            time.sleep(0.5)
                            self.recorder.start()
                            return False
                        else:
                            self.play('something_else')
                            time.sleep(0.5)
                            self.recorder.start()

                else:
                    self.play("not_found")
                    time.sleep(1)

                    return False
            else:
                self.execute_cmd(cmd['cmd'], voice)
                return True, voice

        elif type == 'gpt':
            response = gpt1(voice)
            text = ''
            for msg in response:
                text += str(msg)
            return text

        elif type == 'note':
            self.create_note(voice)

    def filter_cmd(self, raw_voice: str):
        VA_ALIAS = ('джарвис',)
        VA_TBR = ('скажи', 'покажи', 'ответь', 'произнеси', 'расскажи', 'сколько', 'слушай')
        cmd = raw_voice

        for x in VA_ALIAS:
            cmd = cmd.replace(x, "").strip()

        for x in VA_TBR:
            cmd = cmd.replace(x, "").strip()

        return cmd

    def recognize_cmd(self, cmd: str):
        rc = {'cmd': '', 'percent': 0}
        for c, v in self.VA_CMD_LIST.items():

            for x in v:
                vrt = fuzz.ratio(cmd, x)
                if vrt > rc['percent']:
                    rc['cmd'] = c
                    rc['percent'] = vrt

        return rc

    def create_note(self, voice):
        info = voice.split(' ')[3:]
        with open('notes.txt', 'w') as file:
            content = info
            file.write(content)
        file.close()

    def execute_cmd(self, cmd: str, voice: str):
        if cmd == 'open_browser':
            webbrowser.open('google.org')
            self.play("ok")

        elif cmd == 'open_youtube':
            webbrowser.open('https://www.youtube.com/')
            self.play("ok")

        elif cmd == 'open_google':
            webbrowser.open('https://www.google.com/')
            self.play("ok")

        # elif cmd == 'sound_off':
        #     self.play('switch_done')
        #
        #     devices = AudioUtilities.GetSpeakers()
        #     interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        #     volume = cast(interface, POINTER(IAudioEndpointVolume))
        #     volume.SetMute(1, None)
        #
        #
        # elif cmd == 'sound_on':
        #     devices = AudioUtilities.GetSpeakers()
        #     interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        #     volume = cast(interface, POINTER(IAudioEndpointVolume))
        #     volume.SetMute(0, None)
        #
        #     self.play('switch_done')

        elif cmd == 'thanks':
            self.play("thanks")

        elif cmd == 'stupid':
            self.play("stupid")

        elif cmd == 'show_devises':
            self.play("ok")
            print(sd.query_devices())

        elif cmd == 'off':
            self.play("off", True)
            # flet.exe
            close = "taskkill /IM flet.exe"
            os.system(close)

            self.porcupine.delete()
            exit(0)
        elif cmd == 'power_off':
            self.play('off', True)
            os.system('shutdown /s /t 1')

        elif cmd == 'find_files':
            self.play('loading')
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            target = file_name[0]
            dirlist = QtWidgets.QFileDialog.getExistingDirectory(None, 'Выбрать папку', '.')
            self.recorder.stop()
            for root, dirs, files in os.walk(top=dirlist, topdown=True, onerror=None, followlinks=False):
                if target in dirs:
                    self.play('result')
                    path = QtWidgets.QMessageBox.information(None, 'Путь к файлу', self.CDIR)
                    break
                elif target in files:
                    self.play('result')
                    path = QtWidgets.QMessageBox.information(None, 'Путь к файлу', self.CDIR)
                    break
            self.recorder.start()

        elif cmd == 'make_new_dir':
            self.play('loading')
            prg = QtWidgets.QApplication(sys.argv)
            step = QtWidgets.QInputDialog.getText(None, 'Введите имя папки', 'Имя папки:')
            dir_name = step[0]
            self.recorder.stop()
            try:
                os.mkdir(dir_name)
                self.play('new_fol')
            except FileExistsError:
                self.play('dir_name')
                step = QtWidgets.QInputDialog.getText(None, 'Введите имя папки', 'Имя папки:')
                dir_name = step[0]
                os.mkdir(dir_name)
                self.play('new_fol')
        elif cmd == 'make_new_file':
            self.play('loading')
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            file_name = file_name[0]
            self.recorder.stop()
            try:
                new_file = open(file_name, 'w+')
                self.play('new_file')
                self.recorder.start()
            except FileExistsError:
                self.play('file_name')
                file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
                file_name = file_name[0]
                new_file = open(file_name, 'w+')
                self.play('new_file')
                self.recorder.start()

        elif cmd == "delete_dir":
            self.play("loading")
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            target = file_name[0]
            dirlist = QtWidgets.QFileDialog.getExistingDirectory(None, 'Выбрать папку', '.')
            self.recorder.stop()
            for root, dirs, files in os.walk(top=dirlist, topdown=True, onerror=None, followlinks=False):
                if target in dirs:
                    self.play('delete')
                    os.rmdir(target)
                    break
            self.recorder.start()

        elif cmd == 'delete_file':
            self.play("loading")
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            target = file_name[0]
            dirlist = QtWidgets.QFileDialog.getExistingDirectory(None, 'Выбрать папку', '.')
            self.recorder.stop()
            for root, dirs, files in os.walk(top=dirlist, topdown=True, onerror=None, followlinks=False):
                if target in files:
                    self.play('delete')
                    os.remove(target)
                    break
            self.recorder.start()
        elif cmd == 'congratilations':
            self.play('cong')
        elif cmd == 'VK':
            webbrowser.open('https://vk.com')
            self.play('ok')
        elif cmd == 'TG':
            webbrowser.open('https://web.telegram.org')
            self.play('ok')
        elif cmd == 'find_google':
            step = voice.split(' ')
            self.play('ok')
            query = ''
            for i in range(3, len(step)):
                query = query + step[i]
            webbrowser.open('https://www.google.com/search?q=' + query)

        # TODO найти способ заменить serach на обычное открытие страниц
        elif cmd == 'find_person':
            step = voice.split(' ')
            search_term = step[-2] + '+' + step[-1]
            # открытие ссылки на поисковик в браузере
            url = "https://google.com/search?q=" + search_term
            webbrowser.get().open(url)
            # альтернативный поиск с автоматическим открытием ссылок на результаты (в некоторых случаях может быть небезопасно)
            search_results = []
            try:
                for _ in googlesearch.search(search_term,  # что искать
                                             tld="com",  # верхнеуровневый домен
                                             lang='ru',  # используется язык, на котором говорит ассистент
                                             num=1,  # количество результатов на странице
                                             start=0,  # индекс первого извлекаемого результата
                                             stop=2,
                                             # индекс последнего извлекаемого результата (я хочу, чтобы открывался первый результат)
                                             pause=1.0,  # задержка между HTTP-запросами
                                             ):
                    search_results.append(_)
                    webbrowser.get().open(_)

            # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
            except:
                self.play('not_found')
                traceback.print_exc()
                return
            print(search_results)
            self.recorder.stop()
            self.play('is_found')
            self.recorder.start()

        elif cmd == 'youtube_search':
            self.recorder.stop()
            self.play('youtube')
            step = voice.split(' ')
            search_term = ''
            for i in range(3, len(step)):
                search_term += step[i]
            url = "https://www.youtube.com/results?search_query=" + search_term
            webbrowser.get().open(url)
            self.play('watching')
            time.sleep(2.0)
            self.recorder.start()





if __name__ == '__main__':
    model = vosk.Model("assets\\model_small")
    samplerate = 16000
    kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
    PICOVOICE_TOKEN = 'ltRSIRF80lF1Az7esIb8ENGAvfYt1EdGM9UP3xxvu0f56mdGJf0f+g=='
    EDEN_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiN2U3NWFmYWMtMDFlYS00N2I2LWE5YzItMGViZTE4NGQ4NDNjIiwidHlwZSI6ImFwaV90b2tlbiJ9.x0l0jnypRoTRaRnA4EB3tVDI4Shc6OzBk97L0B2y4Lw'
    jarvis_object = Jarvis(picovoice_token=PICOVOICE_TOKEN, eden_token=EDEN_TOKEN)
    jarvis_object.start_jarvis(kaldi_rec)


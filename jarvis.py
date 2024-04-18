import json
import os
import random
import struct
import time
import traceback
import webbrowser
import googlesearch
import openai
import pvporcupine
import simpleaudio as sa
import sounddevice as sd
from fuzzywuzzy import fuzz
from pvrecorder import PvRecorder
from rich import print
from PyQt6 import QtWidgets
import sys


class Jarvis:
    def __init__(self, picovoice_token):
        self.picovoice_token = picovoice_token

        self.CDIR = os.getcwd()
        self.porcupine = pvporcupine.create(
            access_key=self.picovoice_token,
            keywords=['jarvis'],
            sensitivities=[1]
        )
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)

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

                    while time.time() - ltc <= 10:
                        pcm = self.recorder.read()
                        sp = struct.pack("h" * len(pcm), *pcm)

                        if kaldi_rec.AcceptWaveform(sp):
                            if self.va_respond(json.loads(kaldi_rec.Result())["text"]):
                                ltc = time.time()

                            break

                except Exception as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    raise


    def gpt_answer(self, message_log):
        model_engine = "gpt-3.5-turbo"
        max_tokens = 1024  # default 1024
        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=message_log,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=1,
            stop=None
        )

        # Find the first response from the chatbot that has text in it (some responses may not have text)
        for choice in response.choices:
            if "text" in choice:
                return choice.text

        # If no response with text is found, return the first response's content (which may be empty)
        return response.choices[0].message.content


    # self.play(f'{CDIR}\\sound\\ok{random.choice([1, 2, 3, 4])}.wav')

    def play(self, phrase, wait_done=True):
        filename = fr"{self.CDIR}/assets/sound/"

        if phrase == "greet":  # for py 3.8
            filename += f"greet{random.choice([1, 2, 3])}.wav"
        elif phrase == "ok":
            filename += f"ok{random.choice([1, 2, 3])}.wav"
        elif phrase == "not_found":
            filename += "not_found.wav"
        elif phrase == "thanks":
            filename += "thanks.wav"
        elif phrase == "run":
            filename += "run.wav"
        elif phrase == "stupid":
            filename += "stupid.wav"
        elif phrase == "ready":
            filename += "ready.wav"
        elif phrase == "off":
            filename += "off.wav"
        elif phrase == "loading":
            filename += "loading.wav"
        elif phrase == "result":
            filename += "result.wav"
        elif phrase == 'new_element':
            filename += "new_element.wav"
        elif phrase == 'delete':
            filename += 'delete.wav'
        elif phrase == 'cong':
            filename += 'cong.wav'
        elif phrase == 'gpt_start':
            filename += 'gpt_start.wav'
        elif phrase == 'dir_name':
            filename += 'dir_name.wav'
        elif phrase == 'file_name':
            filename += 'file_name.wav'
        elif phrase == 'is_found':
            filename += 'is_found.wav'
        elif phrase == 'nfs':
            filename += 'nfs.wav'
        elif phrase == 'something_else':
            filename += 'something_else.wav'
        elif phrase == 'watching':
            filename += 'watching.wav'
        elif phrase == 'youtube':
            filename += 'youtube.wav'
        elif phrase == 'not_found':
            filename += 'not_found.wav'
        elif phrase == 'moment_file':
            filename = f"{self.CDIR}\\moment_file.wav"

        if wait_done:
            self.recorder.stop()

        wave_obj = sa.WaveObject.from_wave_file(filename)
        self.play_obj = wave_obj.self.play()

        if wait_done:
            self.play_obj.wait_done()
            # time.sleep((len(wave_obj.audio_data) / wave_obj.sample_rate) + 0.5)
            # print("END")
            # time.sleep(0.5)
            self.recorder.start()


    def q_callback(self, indata, frames, time, status, q):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))


    def va_respond(self, voice: str, VA_CMD_LIST, tts):
        global self.recorder, message_log, first_request
        print(f"Распознано: {voice}")

        cmd = self.recognize_cmd(self.filter_cmd(voice))

        print(cmd)

        if len(cmd['cmd'].strip()) <= 0:
            return False
        elif cmd['percent'] < 54 or cmd['cmd'] not in VA_CMD_LIST.keys():

            if fuzz.ratio(voice.join(voice.split()[:1]).strip(), "скажи") > 75:
                self.play('gpt_start')
                if first_request:
                    message_log.append({"role": "user", "content": voice})
                    first_request = True
                    response = self.gpt_answer()
                    message_log.append({"role": "assistant", "content": response})
                    self.recorder.stop()
                    if len(response) < 1000:
                        tts(response)
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


    def filter_cmd(self, raw_voice: str, VA_ALIAS, VA_TBR):
        cmd = raw_voice

        for x in VA_ALIAS:
            cmd = cmd.replace(x, "").strip()

        for x in VA_TBR:
            cmd = cmd.replace(x, "").strip()

        return cmd


    def recognize_cmd(self, cmd: str, VA_CMD_LIST):
        rc = {'cmd': '', 'percent': 0}
        for c, v in VA_CMD_LIST.items():

            for x in v:
                vrt = fuzz.ratio(cmd, x)
                if vrt > rc['percent']:
                    rc['cmd'] = c
                    rc['percent'] = vrt

        return rc


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
        #     self.play("ok", True)
        #
        #     devices = AudioUtilities.GetSpeakers()
        #     interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        #     volume = cast(interface, POINTER(IAudioEndpointVolume))
        #     volume.SetMute(1, None)

        # elif cmd == 'sound_on':
        #     devices = AudioUtilities.GetSpeakers()
        #     interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        #     volume = cast(interface, POINTER(IAudioEndpointVolume))
        #     volume.SetMute(0, None)
        #
        #     self.play("ok")

        elif cmd == 'thanks':
            self.play("thanks")

        elif cmd == 'stupid':
            self.play("stupid")

            '''elif cmd == 'switch_to_headphones':
                self.play("ok")
                pyautogui.moveTo(5, 1064, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(31, 938, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(249, 420, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(110, 342, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(550, 245, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(607, 198, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(1887, 15, duration=0.7)
                pyautogui.leftClick()
                time.sleep(0.5)
                self.play("ready")
    
            elif cmd == 'switch_to_dynamics':
                self.play("ok")
                pyautogui.moveTo(5, 1064, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(31, 938, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(249, 420, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(110, 342, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(550, 245, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(566, 299, duration=0.7)
                pyautogui.leftClick()
                pyautogui.moveTo(1887, 15, duration=0.7)
                pyautogui.leftClick()
                time.sleep(0.5)
                self.play("ready")'''

        elif cmd == 'show_devises':
            self.play("ok")
            print(sd.query_devices())

        elif cmd == 'off':
            self.play("off", True)

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
                self.play('new_element')
            except FileExistsError:
                self.play('dir_name')
                step = QtWidgets.QInputDialog.getText(None, 'Введите имя папки', 'Имя папки:')
                dir_name = step[0]
                os.mkdir(dir_name)
                self.play('new_element')
        elif cmd == 'make_new_file':
            self.play('loading')
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            file_name = file_name[0]
            self.recorder.stop()
            try:
                new_file = open(file_name, 'w+')
                self.play('new_element')
                self.recorder.start()
            except FileExistsError:
                self.play('file_name')
                file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
                file_name = file_name[0]
                new_file = open(file_name, 'w+')
                self.play('new_element')
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

        '''elif cmd == 'time_now':
            self.recorder.stop()
            strtime = datetime.datetime.now().strftime('%H:%M')
            step = strtime.split(':')
            hour = num2words.num2words(int(step[0]), lang='ru')
            minutes = num2words.num2words(int(step[1]), lang='ru')
            if step[1][0] == 0:
                minutes = 'ноль' + ' ' + minutes
            if hour == 'один':
                hour = 'час'
            elif hour == 'ноль':
                hour = 'двенадцать'
            text = ('Сейчас' + ' ' + hour + ' ' + minutes)
            tts(text=text)
            time.sleep(2.0)
            self.play('moment_file')
            os.remove('assets/sound/moment_file.wav')
            self.recorder.start()'''


if __name__ == '__main__':
    print('Работай через приложение пж')
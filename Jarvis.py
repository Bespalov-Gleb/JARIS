import flet as ft
import os
from dotenv import load_dotenv
import datetime
import json
import os
import queue
import random
import struct
import time
import traceback
from ctypes import POINTER, cast
import webbrowser
import googlesearch
import num2words
import sqlite3

import openai
import pvporcupine
import simpleaudio as sa
import sounddevice as sd
import vosk
import yaml
from comtypes import CLSCTX_ALL
from fuzzywuzzy import fuzz
from pvrecorder import PvRecorder
from pycaw.pycaw import (
    AudioUtilities,
    IAudioEndpointVolume
)
from rich import print
from PyQt6 import QtCore, QtWidgets, QtGui

import pyautogui
import sys
import requests


def start_settings(page: ft.Page):
    page.title = 'Jarvis'
    page.theme_mode = 'dark'
    page.window_width = 1010
    page.window_height = 810
    page.window_resizable = False
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    openai_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен OpenAI')
    picovoice_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен Picovoice')
    chrome_pass = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Путь к Chrome')

    def tts(text):
        headers = {
            "Authorization": f"Bearer {EDEN_TOKEN}"}
        url = 'https://api.edenai.run/v2/audio/text_to_speech'
        unx_time = int(time.time())
        payload = {
            "providers": "lovoai", "language": "ru-RU",
            "option": "MALE",
            "lovoai": "ru-RU_Pyotr Semenov",
            "text": f'{text}'
        }
        response = requests.post(url, json=payload, headers=headers)
        result = json.loads(response.text)

        audio_url = result.get('lovoai').get('audio_resource_url')
        r = requests.get(audio_url)
        file_name = 'moment_file.wav'

        with open(file_name, 'wb') as file:
            file.write(r.content)
            file.close()

    def register(e):
        db = sqlite3.connect('jarvis.db')
        cur = db.cursor()
        cur.execute(f"INSERT INTO users VALUES(NULL, '{user_login.value}', '{user_password.value}', '{openai_user.value}', '{picovoice_user.value}', '{eden_user.value}')")
        btn_reg.text = 'Зарегестрировано!'
        page.update()
        db.commit()
        db.close()

    def validate(e):
        if all([user_login.value, user_password.value, openai_user.value, picovoice_user.value, eden_user.value]):
            btn_reg.disabled = False
            btn_auth.disabled = False
        else:
            btn_reg.disabled = True
            btn_auth.disabled = True
        page.update()

    def validate_a(e):
        if all([user_login_a.value, user_password_a.value]):
            btn_reg.disabled = False
            btn_auth.disabled = False
        else:
            btn_reg.disabled = True
            btn_auth.disabled = True
        page.update()

    def auth_user(e):

        db = sqlite3.connect('jarvis.db')
        cur = db.cursor()

        cur.execute(f"SELECT * FROM users WHERE login = '{user_login_a.value}' AND password = '{user_password_a.value}'")
        if cur.fetchone() != None:
            s = cur.fetchone()
            ul = s[1]
            up = s[2]
            op = s[3]
            pc = s[4]
            ed = s[5]
            OPENAI_TOKEN = op
            PICOVOICE_TOKEN = pc
            openai.api_key = OPENAI_TOKEN
            porcupine = pvporcupine.create(
                access_key=PICOVOICE_TOKEN,
                keywords=['jarvis'],
                sensitivities=[1]
            )
            recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
            user_login_a.value = ''
            user_password_a.value = ''
            btn_auth.text = 'Авторизовано!'
            page.clean()
            page.navigation_bar = ft.NavigationBar(
                destinations=[
                    ft.NavigationDestination(icon=ft.icons.SETTINGS, label='Настройки'),
                    ft.NavigationDestination(icon=ft.icons.WECHAT, label='Джарвис'),
                    ft.NavigationDestination(icon=ft.icons.KEYBOARD_COMMAND_KEY, label='Команды')
                ], on_change=navigate
            )
            page.add(jarvis_st)
            cur.execute(
                f"INSERT INTO users VALUES(-1,'{ul}', '{up}', '{op}', '{pc}', '{ed}' )")

            page.update()
            db.commit()
            db.close()
            return recorder, porcupine
        else:
            page.snack_bar = ft.SnackBar(ft.Text('Неверный логин или пароль!'))
            page.snack_bar.open = True
            page.update()

        db.commit()
        db.close()

    def navigate_reg(e):
        index = page.navigation_bar.selected_index
        page.clean()
        if index == 0:
            page.add(panel_register)
        elif index == 1:
            page.add(panel_auth)

    user_login = ft.TextField(label='Логин', width=300, on_change=validate)
    user_password = ft.TextField(label='Пароль', width=300, password=True, on_change=validate)

    user_login_a = ft.TextField(label='Логин', width=300, on_change=validate_a)
    user_password_a = ft.TextField(label='Пароль', width=300, password=True, on_change=validate_a)

    openai_user = ft.TextField(label='Токен OpenAI', width=300, on_change=validate)
    picovoice_user = ft.TextField(label='Токен Picovoice', width=300, on_change=validate)
    eden_user = ft.TextField(label='Токен EdenAI', width=300, on_change=validate)
    btn_reg = ft.OutlinedButton(text='Регистраця', width=300, on_click=register, disabled=True)
    btn_auth = ft.OutlinedButton(text='Авторизация', width=300, on_click=auth_user, disabled=True)

    panel_register = ft.Row([
        ft.Column([
            ft.Text('Регистрация', size=25),
            user_login,
            user_password,
            openai_user,
            picovoice_user,
            eden_user,
            btn_reg
        ], alignment=ft.MainAxisAlignment.CENTER)
    ], alignment=ft.MainAxisAlignment.CENTER)

    panel_auth = ft.Row([
        ft.Column([
            ft.Text('Авторизация', size=25),
            user_login_a,
            user_password_a,
            btn_auth
        ], alignment=ft.MainAxisAlignment.CENTER)
    ], alignment=ft.MainAxisAlignment.CENTER)

    def open_jarvis(e):
        if ((openai_token.value == '') or (picovoice_token.value == '') or (chrome_pass.value == '')):
            page.snack_bar = ft.SnackBar(ft.Text('Необходимо заполнить все поля'))
            page.snack_bar.open = True
            page.update()
        else:
            f = open('user_settings.txt', 'w+')
            if os.stat('user_settings.txt').st_size == 0:
                f.write(openai_token.value + '\n')
                f.write(picovoice_token.value + '\n')
                f.write(chrome_pass.value)
                set_but.text = 'Сохранено!'
                f.close()
                page.update()

    def quit_j(e):
        db = sqlite3.connect('jarvis.db')
        c = db.cursor()
        c.execute("""DELETE FROM users WHERE id = -1""")
        db.commit()
        db.close()
        page.clean()
        page.add(panel_auth)
        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER, label='Регистрация'),
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER_OUTLINED, label='Авторизация')
            ], on_change=navigate_reg
        )
        page.update()

    set_but = ft.ElevatedButton(text='Сохранить', width=300, on_click=open_jarvis)
    quit_btn = ft.ElevatedButton(text='Выйти из аккаунта', width=300, icon=ft.icons.EXIT_TO_APP, on_click=quit_j)

    panel_settings = ft.Row(
        [
            ft.Column(
                [
                    ft.Text('Настройки', size=25),
                    openai_token,
                    picovoice_token,
                    chrome_pass,
                    set_but,
                    quit_btn
                ], alignment=ft.MainAxisAlignment.CENTER
            )
        ], alignment=ft.MainAxisAlignment.CENTER
    )

    def navigate(e):
        index = page.navigation_bar.selected_index
        page.clean()
        if index == 0:
            page.add(panel_settings)
        elif index == 1:
            page.add(jarvis_st)
            page.update()
        elif index == 2:
            page.add((panel_com))

    def check_jarvis(e):
        start_jarvis()

    # panel_jarvis = ft.Column([
    # ft.Row([ft.Text('Диалоговая строка')], alignment=ft.MainAxisAlignment.CENTER),
    # ft.Row([ft.Image(src='qt_material/clideo_editor_e88b8c1b9b3440159e1d616a8e862b5d.gif', width=450, height=450)], alignment=ft.MainAxisAlignment.CENTER),
    # ft.Row([ft.Text('Джарвис', size=25)], alignment=ft.MainAxisAlignment.CENTER)
    # ], alignment=ft.MainAxisAlignment.CENTER)

    back_ground_jarvis = ft.Container(
        width=1010,
        height=810,
        alignment=ft.alignment.center_left,
        bgcolor='black',
        content=(ft.Image(src='qt_material/bg 1000_600.jpg'))
    )

    eye_jarvis = ft.Container(ft.Image('qt_material/20240223_151534.gif',
                                       height=500, width=500), height=800, width=1000,
                              alignment=ft.alignment.top_center)

    black_str = ft.Container(
        bgcolor='black',
        width=100,
        height=50,
    )
    jarvis = ft.Container(ft.Text('Jarvis', size=35, color='blue'), height=800, width=1000,
                          alignment=ft.alignment.Alignment(0, 0.3))

    start_btn = ft.Row([ft.Container(ft.ElevatedButton(text='Запуск', on_click=check_jarvis, bgcolor='blue',
                                                       color='black', height=50, width=150), height=800, width=1000,
                                     alignment=ft.alignment.Alignment(0, 0.5))])

    jarvis_st = ft.Row([ft.Column([ft.Stack([back_ground_jarvis,
                                             eye_jarvis,
                                             jarvis,
                                             start_btn

                                             ])]
                                  )])

    # command = ft.Container(ft.Text('Команды', size=25),height=800, width=1000, alignment=ft.alignment.Alignment(0, -1))
    list_commands = ft.Container(ft.Column([
        ft.Row([ft.Text('Отключение Джарвиса: отключение, пора спать и т.п.', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Браузер: открой браузер, гугл хром и т.п.', size=15)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Открытие сайтов: открой ютуб/вк/телеграм/гугл', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Включение звука: включи звук, верни звук, режим со звуком', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Отключение звука: выключи звук, беззвучный режим, режим без звука', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Смена устройста: перейди на наушники/динамики, звук на наушники/динамики и т.п.', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Отключение ПК: выключи компьютер, завершение работы, мы закончили', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Поиск в интернете: найди информацию о, найди в интернете и т.п.', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Поиск файлов: найди файл, пробеги по системе, анализ системы и т.п.', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Создание файла/папки: новая папка/файл, создать папку/файл и т.п.', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Удалить папку/файл: удали папку/файл', size=15)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Поиск человека: пробей человека, что можешь найти про, найди в соц сетях', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Поиск в Ютуб: открой в ютубе, найди в ютубе', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Время: который час, сколько время', size=15)], alignment=ft.MainAxisAlignment.CENTER)

    ], alignment=ft.MainAxisAlignment.START), height=800, width=1000, alignment=ft.Alignment(0, -0.3))
    panel_com = list_commands

    db = sqlite3.connect('jarvis.db')
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            login TEXT,
            password TEXT,
            openai_token TEXT,
            picovoice_token TEXT,
            eden_token TEXT
            )""")
    cur.execute("""SELECT * FROM users WHERE id = -1""")
    if cur.fetchone() != None:
        cur.execute("""SELECT openai_token, picovoice_token, eden_token FROM users WHERE id = -1""")
        s = cur.fetchone()
        OPENAI_TOKEN = s[0]
        PICOVOICE_TOKEN = s[1]
        EDEN_TOKEN = s[2]

        page.add(jarvis_st)

        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.SETTINGS, label='Настройки'),
                ft.NavigationDestination(icon=ft.icons.WECHAT, label='Джарвис'),
                ft.NavigationDestination(icon=ft.icons.KEYBOARD_COMMAND_KEY, label='Команды')
            ], on_change=navigate
        )
        page.update()
        db.close()

    else:
        page.add(panel_register)
        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER, label='Регистрация'),
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER_OUTLINED, label='Авторизация')
            ], on_change=navigate_reg
        )
        page.update()
        PICOVOICE_TOKEN = 'start'
        OPENAI_TOKEN = 'start'
        db.close()

    if PICOVOICE_TOKEN != 'start':
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_TOKEN,
            keywords=['jarvis'],
            sensitivities=[1]
        )
        recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    if OPENAI_TOKEN != 'start':
        openai.api_key = OPENAI_TOKEN
    load_dotenv("dev.env")

    VA_NAME = 'Jarvis'
    VA_VER = "3.0"
    VA_ALIAS = ('джарвис',)
    VA_TBR = ('скажи', 'покажи', 'ответь', 'произнеси', 'расскажи', 'сколько', 'слушай')
    MICROPHONE_INDEX = -1
    CDIR = os.getcwd()
    VA_CMD_LIST = yaml.safe_load(
        open('commands.yaml', 'rt', encoding='utf8'),
    )

    # ChatGPT vars
    message_log = [
        {"role": "system", "content": "Ты голосовой ассистент из железного человека."}
    ]

    first_request = True

    model = vosk.Model("model_small")
    samplerate = 16000
    device = -1
    kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
    q = queue.Queue()

    def start_jarvis():
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_TOKEN,
            keywords=['jarvis'],
            sensitivities=[1]
        )
        recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
        recorder.start()
        print('Using device: %s' % recorder.selected_device)

        print(f"Jarvis (v3.0) начал свою работу ...")
        play('run')

        time.sleep(0.5)

        ltc = time.time() - 1000

        while True:
            try:
                pcm = recorder.read()
                keyword_index = porcupine.process(pcm)

                if keyword_index >= 0:
                    recorder.stop()
                    play("greet", True)
                    print("Yes, sir.")
                    recorder.start()  # prevent self-recording
                    ltc = time.time()

                while time.time() - ltc <= 10:
                    pcm = recorder.read()
                    sp = struct.pack("h" * len(pcm), *pcm)

                    if kaldi_rec.AcceptWaveform(sp):
                        if va_respond(json.loads(kaldi_rec.Result())["text"]):
                            ltc = time.time()

                        break

            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                raise

    def gpt_answer():
        global message_log

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

    # play(f'{CDIR}\\sound\\ok{random.choice([1, 2, 3, 4])}.wav')

    def play(phrase, wait_done=True):

        filename = f"{CDIR}\\sound\\"

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
            filename = f"{CDIR}\\moment_file.wav"

        if wait_done:
            recorder.stop()

        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()

        if wait_done:
            play_obj.wait_done()
            # time.sleep((len(wave_obj.audio_data) / wave_obj.sample_rate) + 0.5)
            # print("END")
            # time.sleep(0.5)
            recorder.start()

    def q_callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    def va_respond(voice: str):
        global recorder, message_log, first_request
        print(f"Распознано: {voice}")

        cmd = recognize_cmd(filter_cmd(voice))

        print(cmd)

        if len(cmd['cmd'].strip()) <= 0:
            return False
        elif cmd['percent'] < 54 or cmd['cmd'] not in VA_CMD_LIST.keys():

            if fuzz.ratio(voice.join(voice.split()[:1]).strip(), "скажи") > 75:
                play('gpt_start')
                if first_request:
                    message_log.append({"role": "user", "content": voice})
                    first_request = True
                    response = gpt_answer()
                    message_log.append({"role": "assistant", "content": response})
                    recorder.stop()
                    if len(response) < 1000:
                        tts(response)
                        play('moment_file')
                        os.remove('moment_file.wav')
                        time.sleep(0.5)
                        recorder.start()
                        return False
                    else:
                        play('something_else')
                        time.sleep(0.5)
                        recorder.start()
            else:
                play("not_found")
                time.sleep(1)

                return False
        else:
            execute_cmd(cmd['cmd'], voice)
            return True, voice

    def filter_cmd(raw_voice: str):
        cmd = raw_voice

        for x in VA_ALIAS:
            cmd = cmd.replace(x, "").strip()

        for x in VA_TBR:
            cmd = cmd.replace(x, "").strip()

        return cmd

    def recognize_cmd(cmd: str):
        rc = {'cmd': '', 'percent': 0}
        for c, v in VA_CMD_LIST.items():

            for x in v:
                vrt = fuzz.ratio(cmd, x)
                if vrt > rc['percent']:
                    rc['cmd'] = c
                    rc['percent'] = vrt

        return rc

    def execute_cmd(cmd: str, voice: str):

        if cmd == 'open_browser':
            webbrowser.open('google.org')
            play("ok")

        elif cmd == 'open_youtube':
            webbrowser.open('https://www.youtube.com/')
            play("ok")

        elif cmd == 'open_google':
            webbrowser.open('https://www.google.com/')
            play("ok")

        elif cmd == 'sound_off':
            play("ok", True)

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(1, None)

        elif cmd == 'sound_on':
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(0, None)

            play("ok")

        elif cmd == 'thanks':
            play("thanks")

        elif cmd == 'stupid':
            play("stupid")

        elif cmd == 'switch_to_headphones':
            play("ok")
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
            play("ready")

        elif cmd == 'switch_to_dynamics':
            play("ok")
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
            play("ready")

        elif cmd == 'show_devises':
            play("ok")
            print(sd.query_devices())

        elif cmd == 'off':
            play("off", True)

            porcupine.delete()
            exit(0)
        elif cmd == 'power_off':
            play('off', True)
            os.system('shutdown /s /t 1')

        elif cmd == 'find_files':
            play('loading')
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            target = file_name[0]
            dirlist = QtWidgets.QFileDialog.getExistingDirectory(None, 'Выбрать папку', '.')
            recorder.stop()
            for root, dirs, files in os.walk(top=dirlist, topdown=True, onerror=None, followlinks=False):
                if target in dirs:
                    play('result')
                    path = QtWidgets.QMessageBox.information(None, 'Путь к файлу', os.getcwd())
                    break
                elif target in files:
                    play('result')
                    path = QtWidgets.QMessageBox.information(None, 'Путь к файлу', os.getcwd())
                    break
            recorder.start()

        elif cmd == 'make_new_dir':
            play('loading')
            prg = QtWidgets.QApplication(sys.argv)
            step = QtWidgets.QInputDialog.getText(None, 'Введите имя папки', 'Имя папки:')
            dir_name = step[0]
            recorder.stop()
            try:
                os.mkdir(dir_name)
                play('new_element')
            except FileExistsError:
                play('dir_name')
                step = QtWidgets.QInputDialog.getText(None, 'Введите имя папки', 'Имя папки:')
                dir_name = step[0]
                os.mkdir(dir_name)
                play('new_element')
        elif cmd == 'make_new_file':
            play('loading')
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            file_name = file_name[0]
            recorder.stop()
            try:
                new_file = open(file_name, 'w+')
                play('new_element')
                recorder.start()
            except FileExistsError:
                play('file_name')
                file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
                file_name = file_name[0]
                new_file = open(file_name, 'w+')
                play('new_element')
                recorder.start()

        elif cmd == "delete_dir":
            play("loading")
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            target = file_name[0]
            dirlist = QtWidgets.QFileDialog.getExistingDirectory(None, 'Выбрать папку', '.')
            recorder.stop()
            for root, dirs, files in os.walk(top=dirlist, topdown=True, onerror=None, followlinks=False):
                if target in dirs:
                    play('delete')
                    os.rmdir(target)
                    break
            recorder.start()

        elif cmd == 'delete_file':
            play("loading")
            prg = QtWidgets.QApplication(sys.argv)
            file_name = QtWidgets.QInputDialog.getText(None, 'Введите имя файла', 'Имя файла:')
            target = file_name[0]
            dirlist = QtWidgets.QFileDialog.getExistingDirectory(None, 'Выбрать папку', '.')
            recorder.stop()
            for root, dirs, files in os.walk(top=dirlist, topdown=True, onerror=None, followlinks=False):
                if target in files:
                    play('delete')
                    os.remove(target)
                    break
            recorder.start()
        elif cmd == 'congratilations':
            play('cong')
        elif cmd == 'VK':
            webbrowser.open('https://vk.com')
            play('ok')
        elif cmd == 'TG':
            webbrowser.open('https://web.telegram.org')
            play('ok')
        elif cmd == 'find_google':
            step = voice.split(' ')
            play('ok')
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
                play('not_found')
                traceback.print_exc()
                return
            print(search_results)
            recorder.stop()
            play('is_found')
            recorder.start()

        elif cmd == 'youtube_search':
            recorder.stop()
            play('youtube')
            step = voice.split(' ')
            search_term = ''
            for i in range(3, len(step)):
                search_term += step[i]
            url = "https://www.youtube.com/results?search_query=" + search_term
            webbrowser.get().open(url)
            play('watching')
            time.sleep(2.0)
            recorder.start()

        elif cmd == 'time_now':
            recorder.stop()
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
            play('moment_file')
            os.remove('sound/moment_file.wav')
            recorder.start()


ft.app(target=start_settings, view=ft.WEB_BROWSER)

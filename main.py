import flet as ft
from dotenv import load_dotenv
import os
import queue

# from ctypes import POINTER, cast

import multiprocessing
import openai
import pvporcupine

import vosk
import yaml
#from comtypes import CLSCTX_ALL

from pvrecorder import PvRecorder

# from pycaw.pycaw import (
#     AudioUtilities,
#     IAudioEndpointVolume
# )

from db_pkg.database import Database
from db_pkg.models import User
from gpt import gpt1
from jarvis import Jarvis


class Message(ft.Row):
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

    def get_initials(self, user_name: str):
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"  # or any default value you prefer

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]


def start_settings(page: ft.Page):
    page.title = 'Jarvis'
    page.theme_mode = 'dark'
    page.window_width = 1010
    page.window_height = 810
    page.window_resizable = False
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    openai_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен опенаи')
    picovoice_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен пиковойс')
    chrome_pass = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Путь к Chrome')

    db = Database()
    CDIR = os.getcwd()

    def register(e):
        user_to_add = User(
            id=None,
            login=user_login.value,
            password=user_password.value,
            openai_token=openai_user.value,
            picovoice_token=picovoice_user.value,
            eden_token=eden_user.value
        )
        db.add(user_to_add)

        btn_reg.text = 'Зарегестрировано!'
        page.update()

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
        user = db.get_query(User).filter(User.login == user_login_a.value and User.password == user_password_a.value).first()
        if user is not None:
            openai.api_key = user.openai_token
            porcupine = pvporcupine.create(
                access_key=user.picovoice_token,
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

            user_to_add = User(
                id=-1,
                login=user.login,
                password=user.password,
                openai_token=user.openai_token,
                picovoice_token=user.picovoice_token,
                eden_token=user.eden_token
            )
            db.add(user_to_add)

            page.update()

            return recorder, porcupine
        else:
            page.snack_bar = ft.SnackBar(ft.Text('Неверный логин или пароль!'))
            page.snack_bar.open = True
            page.update()

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
        user_to_delete = db.get_query(User).filter(User.id == -1)
        db.delete(user_to_delete)
        # c.execute("""DELETE FROM users WHERE id = -1""")

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
        elif index == 3:
            page.add(
                bord,
                message_line
            )

    def check_jarvis(e):
        kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
        jarvis_object.start_jarvis(kaldi_rec)



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
        content=(ft.Image(src=f'{CDIR}/assets/qt_material/bg 1000_600.jpg'))
    )

    eye_jarvis = ft.Container(ft.Image(f'{CDIR}/assets/qt_material/20240223_151534.gif',
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

    user = db.get_query(User).filter(User.id == -1).first()

    def join_chat_click(e):
        page.session.set("user_name", join_user_name)
        new_message.prefix = ft.Text(f"{join_user_name}: ")
        page.pubsub.send_all(Message(user_name=join_user_name, message=f"{join_user_name} начал новый диалог.",
                                     message_type="login_message"))
        page.update()

    def send_message_click(e):
        if new_message.value != "":
            page.pubsub.send_all(Message(user_name=page.session.get("user_name"), message=new_message.value, message_type="chat_message"))
            new_message.value = ""
            new_message.focus()
            chat.update()
            page.update()

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = Message(user_name=join_user_name, message=message.message, message_type='chat_message')
        elif message.message_type == "login_message":
            m = ft.Text(message.message, italic=True, color=ft.colors.WHITE, size=12)
        chat.controls.append(m)
        chat.update()
        page.update()

        gpt_answer(message)

    def gpt_answer(message: Message):
        response = gpt1(message.message)
        text = ''
        for msg in response:
            text += msg

        m = Message(user_name='SVET', message=text, message_type='chat_message')
        jarvis_object.tts(response)
        chat.controls.append(m)
        chat.update()
        page.update()

    page.pubsub.subscribe(on_message)

    # A dialog asking for a user display name

    join_user_name = db.get_query(User.login).filter(User.id == -1).first()
    join_user_name = str(join_user_name)
    join_user_name = join_user_name[2:-3]

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # A new message entry form
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    join_chat_click(join_user_name)
    message_line = ft.Row(
        [
            new_message,
            ft.IconButton(
                icon=ft.icons.SEND_ROUNDED,
                tooltip="Send message",
                on_click=send_message_click,
            ),
        ]
    )
    bord = ft.Container(
                    content=chat,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    border_radius=5,
                    padding=10,
                    expand=True,
                )

    # Add everything to the page

    if user is not None:
        OPENAI_TOKEN = user.openai_token
        PICOVOICE_TOKEN = user.picovoice_token
        EDEN_TOKEN = user.eden_token

        jarvis_object = Jarvis(picovoice_token=PICOVOICE_TOKEN, eden_token=EDEN_TOKEN)

        page.add(jarvis_st)

        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.SETTINGS, label='Настройки'),
                ft.NavigationDestination(icon=ft.icons.WECHAT, label='Джарвис'),
                ft.NavigationDestination(icon=ft.icons.KEYBOARD_COMMAND_KEY, label='Команды'),
                ft.NavigationDestination(icon=ft.icons.CHAT, label='ChatGPT')
            ], on_change=navigate
        )
        page.update()

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
    VA_CMD_LIST = yaml.safe_load(
        open('commands.yaml', 'rt', encoding='utf8'),
    )

    # ChatGPT vars




    model = vosk.Model("assets/model_small")
    samplerate = 16000
    device = -1
    q = queue.Queue()


app = multiprocessing.Process(target=ft.app(target=start_settings), daemon=True)
app.start()

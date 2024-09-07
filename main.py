import flet as ft
from dotenv import load_dotenv
import os
import queue
from screeninfo import get_monitors

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
from PyQt6 import QtWidgets
from colorama import *



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
    page.title = 'SVET'
    page.theme_mode = 'SYSTEM'
    CDIR = os.getcwd()
    monitor = get_monitors()[0]
    page.window_width = monitor.width
    page.window_height = monitor.height
    page.window_resizable = True
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'
    openai_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен OpenAI')
    picovoice_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен picovoice')
    edenai_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен EdenAI')

    db = Database()


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
        if all([user_login.value, user_password.value, picovoice_user.value, eden_user.value]):
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
                keyword_paths=[os.path.join(f"{CDIR}", "assets", "path", "path_win.ppn")],
                model_path=os.path.join(f'{CDIR}', 'assets', 'path', 'porcupine_params_ru.pv'),
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
                    ft.NavigationDestination(icon=ft.icons.WECHAT, label='SVET'),
                    ft.NavigationDestination(icon=ft.icons.KEYBOARD_COMMAND_KEY, label='Команды'),
                    ft.NavigationDestination(icon=ft.icons.CHAT, label='ChatGPT')
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
        if (user_login.value == '') or (user_password.value == '') or (picovoice_token.value == '') or (edenai_token.value == ''):
            page.snack_bar = ft.SnackBar(ft.Text('Необходимо заполнить все поля'))
            page.snack_bar.open = True
            page.update()
        else:
            user_to_delete = db.get_query(User).filter(User.id == -1).one()
            log = db.get_query(User.login).filter(User.id == -1).one()
            pas = db.get_query(User.password).filter(User.id == -1).one()
            ot = db.get_query(User.openai_token).filter(User.id == -1).one()
            pv = db.get_query(User.picovoice_token).filter(User.id == -1).one()
            et = db.get_query(User.eden_token).filter(User.id == -1).one()
            db.delete(user_to_delete)
            db.add(User(
                id=-1,
                login=log,
                password=pas,
                openai_token=ot,
                picovoice_token=pv,
                edenai_token=et
            ))

    def quit_j(e):
        user_to_delete = db.get_query(User).filter(User.id == -1).one()
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

    def on_hower_inter(e):
        if internet_com.opacity == False:

            internet_com.opacity = True
        else:

            internet_com.opacity = False
        e.control.update()

    def on_hower_pk(e):
        if pk_com.opacity == False:

            pk_com.opacity = True
        else:

            pk_com.opacity = False
        e.control.update()

    def on_hower_learn(e):
        if learn_com.opacity == False:

            learn_com.opacity = True
        else:

            learn_com.opacity = False
        e.control.update()


    def navigate(e):
        index = page.navigation_bar.selected_index
        page.clean()
        if index == 0:
            page.add(panel_settings)
        elif index == 1:
            page.add(panel_svet)
            page.update()
        elif index == 2:
            page.add(ft.Row([ft.Column([ft.Text('Команды', size=45)], alignment=ft.MainAxisAlignment.START)], alignment=ft.MainAxisAlignment.CENTER),
                     ft.Row([ft.Text('aaaaaaaaaaaaaaaaa', opacity=False, size=40)]),
                     ft.Row([ft.Text('aaaaaaaaaaaaaaaaa', opacity=False, size=40)]),
                     ft.Row([ft.Column([
                         ft.Container(width=300, height=300, content=card_for_inter, on_hover=on_hower_inter)
                     ]),
                         ft.Column([ft.Text('aaaaaaaaaaaaaaaaaaaa', opacity=False, size=25)]),
                         ft.Column([
                             ft.Container(width=300, height=300, content=card_for_pk, on_hover=on_hower_pk)
                         ]),
                         ft.Column([ft.Text('aaaaaaaaaaaaaaaaaaaa', opacity=False, size=25)]),
                         ft.Column([
                             ft.Container(width=300, height=300, content=card_for_learn, on_hover=on_hower_learn)
                         ])], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([ft.Column([
                        ft.Container(width=300, height=300, content=internet_com, on_hover=on_hower_inter)
                    ]),
                        ft.Column([ft.Text('aaaaaaaaaaaaaaaaaaaa', opacity=False, size=25)]),
                        ft.Column([
                            ft.Container(width=300, height=300, content=pk_com, on_hover=on_hower_pk)
                        ]),
                        ft.Column([ft.Text('aaaaaaaaaaaaaaaaaaaa', opacity=False, size=25)]),
                        ft.Column([
                            ft.Container(width=300, height=300, content=learn_com, on_hover=on_hower_learn)
                        ])], alignment=ft.MainAxisAlignment.CENTER))

            page.update()
        elif index == 3:
            page.add(
                bord,
                message_line
            )
            page.update()

    def check_jarvis(e):
        page.clean()
        panel_svet = ft.Container(
            ft.Stack([
                ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
                svet,
                start_btn,
                ask_gpt_btn
            ]), alignment=ft.Alignment(1, 1)
        )
        page.add(panel_svet)
        page.update()
        kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
        jarvis_object.start_jarvis(kaldi_rec)


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
            print(m)
            chat.controls.append(m)
            chat.update()
            page.update()
            gpt_answer(mes=message.message, id=1, e=0)
        elif message.message_type == "login_message":
            m = ft.Text(message.message, italic=True, color=ft.colors.WHITE, size=12)
            chat.controls.append(m)
            chat.update()
            page.update()




    def gpt_answer(e, mes, id):
        if id == 0:
            response = jarvis_object.main_connect(kaldi_rec=vosk.KaldiRecognizer(model, samplerate))
            text = ''
            for i in response:
                text += str(i)
        if id == 1:
            response = gpt1(mes)
            text = ''
            for i in response:
                text += str(i)
        m = Message(user_name='SVET', message=text, message_type='chat_message')
        #jarvis_object.tts(response)
        chat.controls.append(m)
        chat.update()
        page.update()




    # panel_jarvis = ft.Column([
    # ft.Row([ft.Text('Диалоговая строка')], alignment=ft.MainAxisAlignment.CENTER),
    # ft.Row([ft.Image(src='qt_material/clideo_editor_e88b8c1b9b3440159e1d616a8e862b5d.gif', width=450, height=450)], alignment=ft.MainAxisAlignment.CENTER),
    # ft.Row([ft.Text('Джарвис', size=25)], alignment=ft.MainAxisAlignment.CENTER)
    # ], alignment=ft.MainAxisAlignment.CENTER)


    back_ground_jarvis = ft.Container(
        width=2100,
        height=1200,
        alignment=ft.Alignment(-2,-2),
        content=(ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg'))
    )

    eye_jarvis = ft.Container(ft.Image(f'{CDIR}/assets/qt_material/msg1032980595-187354.png',
                                       height=700, width=700), height=720, width=1300,
                              alignment=ft.alignment.Alignment(1,-1))

    black_str = ft.Container(
        bgcolor='black',
        width=100,
        height=50,
    )
    jarvis = ft.Container(ft.Text('Jarvis', size=35, color='blue'), height=800, width=1000,
                          alignment=ft.alignment.Alignment(0, 0.3))

    start_btn = ft.Row([ft.Container(ft.ElevatedButton(text='Запуск', on_click=check_jarvis, bgcolor=ft.colors.BLUE_300,
                                                       color='black', height=70, width=200), height=800, width=1000,
                                     alignment=ft.alignment.Alignment(1.1, 0.7))])
    ask_gpt_btn = ft.Row([ft.Container(ft.ElevatedButton(text='GPT', on_click=gpt_answer,bgcolor=ft.colors.BLUE_300,
                                                       color='black', height=70, width=200), height=800, width=1000,
                                     alignment=ft.alignment.Alignment(1.1, 1.0))])

    jarvis_st = ft.Row([ft.Column([ft.Stack([
        back_ground_jarvis,
        eye_jarvis,
        #start_btn,
        ask_gpt_btn
                                ])]
                                  )])

    sett = ft.Container(width=2100, height=1200, content=ft.Row([ft.Column([
        ft.Image(f'{CDIR}/assets/qt_material/photo1718366319.jpeg', width=300, height=300),
                    ft.Text('Настройки', size=25),
                    user_login,
                    user_password,
                    picovoice_token,
                    edenai_token,
                    set_but,
                    quit_btn], alignment=ft.alignment.center_right)], alignment=ft.MainAxisAlignment.CENTER))
    panel_settings = ft.Container(
        ft.Stack([
            ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
            sett]), alignment=ft.Alignment(1.0,1.0))

    svet = ft.Container(width=2100, height=1200, content=ft.Row([ft.Column([
        ft.Image(f'{CDIR}/assets/qt_material/msg1032980595-187354.png',
                 height=700, width=700)
    ])], alignment=ft.MainAxisAlignment.CENTER))

    label = ft.Row([ft.Container(ft.Text('SVET', size=45, color=ft.colors.BLUE_300),
                                 height=800, width=1000, alignment=ft.alignment.Alignment(0.98, 0.37))])


    panel_svet = ft.Container(
        ft.Stack([
            ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
            svet,
            start_btn
        ]), alignment=ft.Alignment(1,1)
    )




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


    internet_com = ft.Container(
        width=500,
        height=300,
        bgcolor='white',
        animate_opacity=300,
        opacity=False,
        content=ft.Text('Браузер - открой браузер, гугл хром\n'
                        'Сайты - открой ютуб/вконтакте/телеграм\n'
                        'Поиск - найди информацию о, найди в интернете\n'
                        'Ютуб - найди в ютубе, открой в ютубе\n'
                        'Найти человека - пробей человека, найди в соц сетях', color='black', size=20), alignment=ft.alignment.center_left)

    pk_com = ft.Container(
        width=500,
        height=300,
        bgcolor='white',
        animate_opacity=300,
        opacity=False,
        content=ft.Text('Отключение программы - отключение, пора спать\n'
                        'Включение/отключение звука - включи\отключи звук\n'
                        'Отключение ПК - завершение работы, мы закончили\n'
                        'Поиск/создание/удаление файлов - создай/найди/удали файл\n'
                        'Время - который час, сколько времени', color='black', size=20), alignment=ft.alignment.center
    )

    learn_com = ft.Container(
        width=500,
        height=300,
        bgcolor='white',
        animate_opacity=300,
        opacity=False,
        content=ft.Text('Здесь будут команды для работы с учебными материалами', color='black', size=20), alignment=ft.alignment.center_right)


    card_for_inter = ft.Image(f'{CDIR}/assets/qt_material/для интернета.png',
                 height=700, width=700)
    card_for_pk = ft.Image(f'{CDIR}/assets/qt_material/для пк.png',
                 height=700, width=700)
    card_for_learn = ft.Image(f'{CDIR}/assets/qt_material/для учебы.png',
                 height=700, width=700)

    user = db.get_query(User).filter(User.id == -1).first()


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

        page.add(panel_svet)

        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.SETTINGS, label='Настройки'),
                ft.NavigationDestination(icon=ft.icons.WECHAT, label='SVET'),
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

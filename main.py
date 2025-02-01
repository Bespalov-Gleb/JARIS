import flet as ft
from dotenv import load_dotenv
import os
import queue
from screeninfo import get_monitors

# from ctypes import POINTER, cast

import multiprocessing

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
    page.locale_configuration = ft.LocaleConfiguration(
        supported_locales=[ft.Locale('en', 'US'), ft.Locale('ru','RU')],
        current_locale=ft.Locale('en','US')
    )
    openai_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Токен OpenAI')
    picovoice_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Token Picovoice')
    edenai_token = ft.TextField(value='', width=300, text_align=ft.TextAlign.LEFT, label='Token EdenAI')

    db = Database()


    def register(e):
        user_to_add = User(
            id=None,
            login=user_login_en.value,
            password=user_password_en.value,
            openai_token=openai_user.value,
            picovoice_token=picovoice_user.value,
            eden_token=eden_user.value,
            current_lang='en'
        )
        db.add(user_to_add)

        btn_reg.text = 'Registered!'
        page.update()

    def validate(e):
        if all([user_login_en.value, user_password_en.value, picovoice_user.value, eden_user.value]):
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
                    ft.NavigationDestination(icon=ft.icons.SETTINGS, label='Settings'),
                    ft.NavigationDestination(icon=ft.icons.WECHAT, label='SVET'),
                    #ft.NavigationDestination(icon=ft.icons.KEYBOARD_COMMAND_KEY, label='Commands'),
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
                eden_token=user.eden_token,
                current_lang='en'
            )
            db.add(user_to_add)

            page.update()

            return recorder, porcupine
        else:
            page.snack_bar = ft.SnackBar(ft.Text('Invalid username or password!'))
            page.snack_bar.open = True
            page.update()

    def navigate_reg(e):
        index = page.navigation_bar.selected_index
        page.clean()
        if index == 0:
            page.add(panel_register)
        elif index == 1:
            page.add(panel_auth)




    user_login_en = ft.TextField(label='Login', width=300, on_change=validate)
    user_login_ru = ft.TextField(label='Логин', width=300, on_change=validate)

    user_password_en = ft.TextField(label='Password', width=300, password=True, on_change=validate)
    user_password_ru = ft.TextField(label='Пароль', width=300, password=True, on_change=validate)


    user_login_a = ft.TextField(label='Login', width=300, on_change=validate_a)
    user_password_a = ft.TextField(label='Password', width=300, password=True, on_change=validate_a)

    openai_user = ft.TextField(label='Token OpenAI', width=300, on_change=validate)
    picovoice_user = ft.TextField(label='Token Picovoice', width=300, on_change=validate)
    eden_user = ft.TextField(label='Token EdenAI', width=300, on_change=validate)
    btn_reg = ft.OutlinedButton(text='Registration', width=300, on_click=register, disabled=True)
    btn_auth = ft.OutlinedButton(text='Authorization', width=300, on_click=auth_user, disabled=True)

    panel_register = ft.Row([
        ft.Column([
            ft.Text('Registration', size=25),
            user_login_en,
            user_password_en,
            picovoice_user,
            eden_user,
            btn_reg
        ], alignment=ft.MainAxisAlignment.CENTER)
    ], alignment=ft.MainAxisAlignment.CENTER)

    panel_auth = ft.Row([
        ft.Column([
            ft.Text('Authorization', size=25),
            user_login_a,
            user_password_a,
            btn_auth
        ], alignment=ft.MainAxisAlignment.CENTER)
    ], alignment=ft.MainAxisAlignment.CENTER)

    def open_jarvis(e):
        if (user_login_en.value == '') or (user_password_en.value == '') or (picovoice_token.value == '') or (edenai_token.value == ''):
            page.snack_bar = ft.SnackBar(ft.Text('All fields must be filled in'))
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
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER, label='Registration'),
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER_OUTLINED, label='Authorization')
            ], on_change=navigate_reg
        )
        page.update()


    set_but_en = ft.ElevatedButton(text='Save', width=300, on_click=open_jarvis)
    set_but_ru = ft.ElevatedButton(text='Сохранить', width=300, on_click=open_jarvis)

    quit_btn_en = ft.ElevatedButton(text='Log out of your account', width=300, icon=ft.icons.EXIT_TO_APP, on_click=quit_j)
    quit_btn_ru = ft.ElevatedButton(text='Log out of your account', width=300, icon=ft.icons.EXIT_TO_APP, on_click=quit_j)


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
        user = db.get_query(User).filter(User.id == -1).first()
        if index == 0:
            if user.current_lang == 'en':
                page.add(panel_settings_en)
                page.update()
            else:
                page.add(panel_settings_ru)
                page.update()
        elif index == 1:
            if user.current_lang == 'en':
                page.add(panel_svet_en)
                page.update()
            else:
                page.add(panel_svet_ru)
                page.update()
        '''elif index == 2:
            page.add(
                bord,
                message_line
            )
            page.update()'''

        '''elif index == 2:
            pass
            page.add(ft.Row([ft.Column([ft.Text('Commands', size=45)], alignment=ft.MainAxisAlignment.START)], alignment=ft.MainAxisAlignment.CENTER),
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

            page.update()'''


    def check_jarvis(e):
        page.clean()
        panel_svet = ft.Container(
            ft.Stack([
                ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
                svet,
                start_btn_en,

            ]), alignment=ft.Alignment(1, 1)
        )
        page.add(panel_svet_en)
        page.update()
        kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
        jarvis_object.start_jarvis(kaldi_rec=kaldi_rec)


    def join_chat_click(e):
        page.session.set("user_name", join_user_name)
        new_message.prefix = ft.Text(f"{join_user_name}: ")
        page.pubsub.send_all(Message(user_name=join_user_name, message=f"{join_user_name} start new dialog.",
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

        elif message.message_type == "login_message":
            m = ft.Text(message.message, italic=True, color=ft.colors.WHITE, size=12)
            chat.controls.append(m)
            chat.update()
            page.update()


    def language_change(e):
        if drop.value == 'English':
            page.locale_configuration.current_locale = ft.Locale("en", "US")
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
                eden_token=et,
                current_lang='en'
            ))

        elif drop.value == 'Русский':
            page.locale_configuration.current_locale = ft.Locale("ru", "RU")
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
                eden_token=et,
                current_lang='ru'
            ))
        else:
            page.snack_bar = ft.SnackBar(ft.Text('First choose a language!'))
            page.snack_bar.open = True
            page.update()
        page.update()




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

    start_btn_en = ft.Row([ft.Container(ft.ElevatedButton(text='Start', on_click=check_jarvis, bgcolor=ft.colors.BLUE_300,
                                                       color='black', height=70, width=200), height=800, width=1000,
                                     alignment=ft.alignment.Alignment(1.1, 0.7))])
    start_btn_ru = ft.Row(
        [ft.Container(ft.ElevatedButton(text='Запуск', on_click=check_jarvis, bgcolor=ft.colors.BLUE_300,
                                        color='black', height=70, width=200), height=800, width=1000,
                      alignment=ft.alignment.Alignment(1.1, 0.7))])
    '''ask_gpt_btn = ft.Row([ft.Container(ft.ElevatedButton(text='GPT', on_click=gpt_answer,bgcolor=ft.colors.BLUE_300,
                                                       color='black', height=70, width=200), height=800, width=1000,
                                     alignment=ft.alignment.Alignment(1.1, 1.0))])'''

    jarvis_st = ft.Row([ft.Column([ft.Stack([
        back_ground_jarvis,
        eye_jarvis,
        start_btn_en,
        ])]
                                  )])

    drop = ft.Dropdown(width=300,
                       options=[
                           ft.dropdown.Option("English"),
                           ft.dropdown.Option('Русский')
                       ])
    lang_ch_btn_en = ft.ElevatedButton(text='Save', width=300, on_click=language_change)
    lang_ch_btn_ru = ft.ElevatedButton(text='Сохранить', width=300, on_click=language_change)


    sett_en = ft.Container(width=2100, height=1200, content=ft.Row([ft.Column([
        ft.Image(f'{CDIR}/assets/qt_material/photo1718366319.jpeg', width=300, height=300),
                    ft.Text("Language", size=25),
                    drop,
                    lang_ch_btn_en,
                    ft.Text('Settings', size=25),
                    user_login_en,
                    user_password_en,
                    picovoice_token,
                    edenai_token,
                    set_but_en,
                    quit_btn_en], alignment=ft.alignment.center_right)], alignment=ft.MainAxisAlignment.CENTER))
    sett_ru = ft.Container(width=2100, height=1200, content=ft.Row([ft.Column([
        ft.Image(f'{CDIR}/assets/qt_material/photo1718366319.jpeg', width=300, height=300),
        ft.Text("Язык", size=25),
        drop,
        lang_ch_btn_en,
        ft.Text('Настройки', size=25),
        user_login_ru,
        user_password_ru,
        picovoice_token,
        edenai_token,
        set_but_ru,
        quit_btn_ru], alignment=ft.alignment.center_right)], alignment=ft.MainAxisAlignment.CENTER))
    panel_settings_en = ft.Container(
        ft.Stack([
            ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
            sett_en]), alignment=ft.Alignment(1.0,1.0))
    panel_settings_ru = ft.Container(
        ft.Stack([
            ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
            sett_ru]), alignment=ft.Alignment(1.0, 1.0))

    svet = ft.Container(width=2100, height=1200, content=ft.Row([ft.Column([
        ft.Image(f'{CDIR}/assets/qt_material/msg1032980595-187354.png',
                 height=700, width=700)
    ])], alignment=ft.MainAxisAlignment.CENTER))

    label = ft.Row([ft.Container(ft.Text('SVET', size=45, color=ft.colors.BLUE_300),
                                 height=800, width=1000, alignment=ft.alignment.Alignment(0.98, 0.37))])


    panel_svet_en = ft.Container(
        ft.Stack([
            ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
            svet,
            start_btn_en
        ]), alignment=ft.Alignment(1,1)
    )
    panel_svet_ru = ft.Container(
        ft.Stack([
            ft.Image(src=f'{CDIR}/assets/qt_material/city.jpg', height=1300, width=2200),
            svet,
            start_btn_ru
        ]), alignment=ft.Alignment(1, 1)
    )




    # command = ft.Container(ft.Text('Команды', size=25),height=800, width=1000, alignment=ft.alignment.Alignment(0, -1))
    list_commands = ft.Container(ft.Column([
        ft.Row([ft.Text("Disabling SVET: disconnecting, it's time to sleep, etc.", size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Browser: open the browser, Google chrome, etc.', size=15)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Opening websites: open YouTube/vk/telegram/Google', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Turn on the sound: turn on the sound, turn on the sound, sound mode', size=15)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ft.Text('Mute: mute, silent mode, mute mode', size=15)],
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
        if user.current_lang == 'en':
            page.add(panel_svet_en)
            page.navigation_bar = ft.NavigationBar(
                destinations=[
                    ft.NavigationDestination(icon=ft.icons.SETTINGS, label='Settings'),
                    ft.NavigationDestination(icon=ft.icons.WECHAT, label='SVET'),
                    # ft.NavigationDestination(icon=ft.icons.KEYBOARD_COMMAND_KEY, label='Команды'),
                    ft.NavigationDestination(icon=ft.icons.CHAT, label='ChatGPT')
                ], on_change=navigate
            )
            page.update()
        else:
            page.add(panel_svet_ru)
            page.navigation_bar = ft.NavigationBar(
                destinations=[
                    ft.NavigationDestination(icon=ft.icons.SETTINGS, label='Настройки'),
                    ft.NavigationDestination(icon=ft.icons.WECHAT, label='SVET'),
                    # ft.NavigationDestination(icon=ft.icons.KEYBOARD_COMMAND_KEY, label='Команды'),
                    ft.NavigationDestination(icon=ft.icons.CHAT, label='ChatGPT')
                ], on_change=navigate
            )
            page.update()



    else:
        page.add(panel_register)
        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER, label='Registration'),
                ft.NavigationDestination(icon=ft.icons.VERIFIED_USER_OUTLINED, label='Authorization')
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



    #if user.current_lang == 'ru':
    #    model = vosk.Model("assets/model_small")
    #else:
    model = vosk.Model("assets/vosk-model-small-en-us-0.15")
    samplerate = 16000
    device = -1
    q = queue.Queue()


app = multiprocessing.Process(target=ft.app(target=start_settings), daemon=True)
app.start()

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message

from config import SUPERADMIN_USERNAME
from states import Form
from database import is_admin


# Обработчик для команды /start
async def send_welcome(message: Message):
    username = message.from_user.username

    if username == SUPERADMIN_USERNAME:
        await superadmin_welcome(message)
    elif username and await is_admin(username):
        await admin_welcome(message)
    else:
        await student_welcome(message)


# Регистрация обработчика для команды /start
def register_start_handlers(dp):
    dp.register_message_handler(send_welcome, commands=['start'])


# Приветственное сообщение для студентов
async def student_welcome(message: Message):
    welcome_text = (
        "Приветствую! Я бот для управления логинами и паролями студентов.\n\n"
        "Отправьте своё ФИО в формате Фамилия Имя Отчество, чтобы получить логин и пароль.\n"
        "Если возникли проблемы или вы не нашли свою запись, обратитесь к лектору: @{lector}"
    ).format(lector=SUPERADMIN_USERNAME)
    await message.answer(welcome_text)
    await Form.check_fio.set()


# Общие кнопки для всех администраторов
_common_buttons = [
    "Добавить студента",
    "Обновить данные студента",
    "Удалить студента",
    "Показать всех студентов",
    "Показать студентов по программе",
    "Добавить студентов из файла",
    "Найти студента по логину",
    "Найти студента по Telegram"
]


# Функция для создания общего меню
def create_menu(button_names):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [KeyboardButton(name) for name in button_names]
    keyboard.add(*buttons)
    return keyboard


# Меню для администратора
def admin_menu():
    return create_menu(_common_buttons)


# Меню для суперадминистратора
def superadmin_menu():
    superadmin_buttons = _common_buttons + [
        "Добавить админа",
        "Удалить админа",
        "Показать всех админов"
    ]
    return create_menu(superadmin_buttons)


# Приветственное сообщение для администраторов
async def admin_welcome(message: Message):
    welcome_text = (
        "Приветствую, администратор!\n\n"
        "Вы можете использовать следующие команды для управления студентами."
    )
    await message.answer(welcome_text, reply_markup=admin_menu())


# Приветственное сообщение для суперадмина
async def superadmin_welcome(message: Message):
    welcome_text = (
        "Приветствую, суперадмин!\n\n"
        "Вы можете использовать команды для управления ботом и администраторами."
    )
    await message.answer(welcome_text, reply_markup=superadmin_menu())


import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message


LECTOR_USERNAME = os.getenv('LECTOR_USERNAME', '@tg_nik')  # Никнейм лектора


# Приветственное сообщение для студентов
async def student_welcome(message: Message):
    welcome_text = (
        "Приветствую! Я бот для управления логинами и паролями студентов.\n\n"
        "Отправьте своё ФИО, чтобы получить логин и пароль.\n"
        "Если возникли проблемы или вы не нашли свою запись, обратитесь к лектору: {lector}"
    ).format(lector=LECTOR_USERNAME)
    await message.answer(welcome_text)


# Приветственное сообщение для администратора
async def admin_welcome(message: Message):
    # Создаем клавиатуру для администраторов
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton("Добавить студента"),
        KeyboardButton("Обновить студента"),
        KeyboardButton("Удалить студента"),
        KeyboardButton("Показать студентов по программе"),
        KeyboardButton("Найти студента по логину"),
        KeyboardButton("Найти студента по Telegram")
    ]
    keyboard.add(*buttons)

    welcome_text = (
        "Приветствую, администратор!\n\n"
        "Вы можете использовать следующие команды:\n"
        "1. Добавить студента: нажмите 'Добавить студента' и введите <ФИО> <логин> <пароль> <программа>\n"
        "2. Обновить студента: нажмите 'Обновить студента' и введите <ФИО> <новый логин> <новый пароль>\n"
        "3. Удалить студента: нажмите 'Удалить студента' и введите <ФИО>\n"
        "4. Показать студентов по программе: нажмите 'Показать студентов по программе' и введите <название программы>\n"
        "5. Найти студента по логину или Telegram"
    )
    await message.answer(welcome_text, reply_markup=keyboard)


# Приветственное сообщение для суперадмина
async def superadmin_welcome(message: Message):
    # Создаем клавиатуру для суперадминов
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton("/add_admin"),
        KeyboardButton("/add_user"),
        KeyboardButton("/update_user"),
        KeyboardButton("/delete_user"),
        KeyboardButton("/list_program"),
        KeyboardButton("/get_fio_by_login"),
        KeyboardButton("/get_fio_by_tg")
    ]
    keyboard.add(*buttons)

    welcome_text = (
        "Приветствую, суперадмин!\n\n"
        "Вы можете управлять ботом с помощью следующих команд:\n"
        "/add_admin - Добавить администратора\n"
        "/add_user - Добавить студента\n"
        "/update_user - Обновить студента\n"
        "/delete_user - Удалить студента\n"
        "/list_program - Список студентов на программе\n"
        "/get_fio_by_login - Найти студента по логину\n"
        "/get_fio_by_tg - Найти студента по Telegram"
    )
    await message.answer(welcome_text, reply_markup=keyboard)

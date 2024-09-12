import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from states import Form
from config import BOT_TOKEN, SUPERADMIN_USERNAME, SUPERADMIN_ID
from lib import log_command, re_rsplit
from handlers import admin, student, superadmin, start


from database import (init_db, add_student, update_student_login_password, delete_student,
                      get_students_by_program, get_student_by_login, get_student_by_tg_username,
                      check_for_duplicate_tg, validate_duplicates, is_admin,
                      add_admin, delete_admin, get_all_admins,
                      get_user_by_username, get_all_students, update_student_tg, get_student_by_fio)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

start.register_start_handlers(dp)
student.register_student_handlers(dp)


# Декоратор для проверки доступа администратора
def admin_only(handler):
    async def wrapped(message: types.Message, *args, **kwargs):
        username = message.from_user.username
        if username == SUPERADMIN_USERNAME or await is_admin(username):
            return await handler(message)  # (message, *args, **kwargs)
        else:
            await message.answer("У вас нет прав доступа для выполнения этой команды.")
    return wrapped


# Команда для получения всех студентов
@dp.message_handler(lambda message: message.text == "Показать всех студентов")
@admin_only
async def list_all_students(message: types.Message):
    log_command(message, '/list_all_students')

    students = await get_all_students()
    if students:
        result = '\n'.join([f"{s[0]} - Логин: {s[1]}, Пароль: {s[2]}, Программа: {s[3]}, Телеграм: {s[4]}" for s in students])
        await message.answer(f"Список всех студентов:\n{result[:4000]}")
    else:
        await message.answer("Студенты не найдены.")


# Команда для добавления нескольких пользователей
@dp.message_handler(lambda message: message.text == "Добавить студента")
@admin_only
async def add_user_start(message: types.Message):
    log_command(message, '/add_user')
    await message.answer("Введите данные для добавления пользователей (каждый пользователь на новой строке):\n"
                         "<ФИО> <логин> <пароль> <программа>")
    await Form.add_user.set()


@dp.message_handler(state=Form.add_user)
async def process_add_user(message: types.Message, state: FSMContext):
    users_data = message.text.strip().split('\n')
    results = []

    for user_data in users_data:
        args = user_data.strip().split()
        if len(args) < 4:
            results.append(f"Ошибка: недостаточно данных для пользователя: {user_data.strip()}")
            continue

        full_name = ' '.join(args[:-3])
        login = args[-3]
        password = args[-2]
        program = args[-1]

        # Проверка на дублирование
        duplicate = await validate_duplicates(full_name)
        if duplicate:
            await bot.send_message(SUPERADMIN_ID, f"Внимание: найдены похожие ФИО: {full_name} и {duplicate}")

        await add_student(full_name, login, password, program)
        results.append(f"Пользователь {full_name} добавлен.")

    await message.answer('\n'.join(results))
    await state.finish()


# Команда для обновления пользователей
@dp.message_handler(lambda message: message.text == "Обновить данные студента")
@admin_only
async def update_user_start(message: types.Message):
    log_command(message, '/update_user')
    await message.answer("Введите данные для обновления пользователей (каждый пользователь на новой строке):\n"
                         "<ФИО> <новый логин> <новый пароль>")
    await Form.update_user.set()


@dp.message_handler(state=Form.update_user)
async def process_update_user(message: types.Message, state: FSMContext):
    users_data = message.text.strip().split('\n')
    results = []

    for user_data in users_data:
        args = user_data.strip().split()
        if len(args) < 3:
            results.append(f"Ошибка: недостаточно данных для пользователя: {user_data.strip()}")
            continue

        full_name = ' '.join(args[:-2])
        new_login = args[-2]
        new_password = args[-1]

        # Проверка на дублирование
        duplicate = await validate_duplicates(full_name)
        if duplicate:
            await bot.send_message(SUPERADMIN_ID, f"Внимание: найдены похожие ФИО: {full_name} и {duplicate}")

        await update_student_login_password(full_name, new_login, new_password)
        results.append(f"Данные пользователя {full_name} обновлены.")

    await message.answer('\n'.join(results))
    await state.finish()


# Команда для удаления пользователей
@dp.message_handler(lambda message: message.text == "Удалить студента")
@admin_only
async def delete_user_start(message: types.Message):
    log_command(message, '/delete_user')
    await message.answer("Введите ФИО пользователей для удаления (каждое ФИО на новой строке).")
    await Form.delete_user.set()


@dp.message_handler(state=Form.delete_user)
async def process_delete_user(message: types.Message, state: FSMContext):
    users_data = message.text.strip().split('\n')
    results = []

    for user_data in users_data:
        full_name = user_data.strip()
        success = await delete_student(full_name)
        if success:
            results.append(f"Пользователь {full_name} был успешно удален.")
        else:
            results.append(f"Пользователь {full_name} не найден или не удалось удалить.")

    await message.answer('\n'.join(results))
    await state.finish()


# Команда для добавления администратора (только для суперадмина)
@dp.message_handler(lambda message: message.text == "Добавить админа")
async def add_admin_start(message: types.Message):
    username = message.from_user.username
    if username != SUPERADMIN_USERNAME:
        await message.answer("Только суперадминистратор может добавлять администраторов.")
        return

    log_command(message, '/add_admin')
    await message.answer("Введите никнейм администратора, которого хотите добавить:")
    await Form.add_admin.set()


@dp.message_handler(state=Form.add_admin)
async def process_add_admin(message: types.Message, state: FSMContext):
    telegram_username = message.text.strip().lstrip('@')
    user = await get_user_by_username(telegram_username)

    if user:
        await message.answer(f"Пользователь с ником @{telegram_username} уже является админом.")
        await state.finish()
        return

    try:
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.user:
            await add_admin(telegram_username)
            await message.answer(f"Пользователь @{telegram_username} добавлен в админы.")
        else:
            await message.answer("Пользователь не найден в этом чате.")
    except Exception as e:
        await message.answer(f"Ошибка при добавлении админа: {e}")

    await state.finish()


# Команда для удаления администратора (доступна только суперадмину)
@dp.message_handler(lambda message: message.text == "Удалить админа")
async def delete_admin_start(message: types.Message):
    username = message.from_user.username
    if username != SUPERADMIN_USERNAME:
        await message.answer("Только суперадминистратор может удалять администраторов.")
        return

    log_command(message, '/delete_admin')
    await message.answer("Введите никнейм администратора, которого хотите удалить:")
    await Form.delete_admin.set()


@dp.message_handler(state=Form.delete_admin)
async def process_delete_admin(message: types.Message, state: FSMContext):
    telegram_username = message.text.strip().lstrip('@')
    user = await get_user_by_username(telegram_username)

    if user:
        await delete_admin(telegram_username)
        await message.answer(f"Пользователь @{telegram_username} был удален из администраторов.")
    else:
        await message.answer(f"Пользователь с ником @{telegram_username} не найден среди администраторов.")

    await state.finish()


# Команда для показа всех админов (доступно только суперадмину)
@dp.message_handler(lambda message: message.text == "Показать всех админов")
async def show_all_admins(message: types.Message):
    username = message.from_user.username
    if username != SUPERADMIN_USERNAME:
        await message.answer("Только суперадминистратор может просматривать список администраторов.")
        return

    log_command(message, '/show_all_admins')

    admins = await get_all_admins()
    if admins:
        admins_list = '\n'.join([f"@{admin}" for admin in admins])
        await message.answer(f"Список всех администраторов:\n{admins_list}")
    else:
        await message.answer("Администраторы не найдены.")


# Команда для загрузки пользователей из файла
@dp.message_handler(lambda message: message.text == "Добавить студентов из файла")
@admin_only
async def add_users_from_file(message: types.Message):
    log_command(message, '/add_users_from_file')
    await message.answer("Пожалуйста, отправьте CSV файл для добавления пользователей.")
    await Form.add_from_file.set()


@dp.message_handler(content_types=[types.ContentType.DOCUMENT], state=Form.add_from_file)
async def process_users_file(message: types.Message, state: FSMContext):
    log_command(message, 'Обработка файла пользователей')
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    await bot.download_file(file_path, 'users.csv')

    results = []

    # Открываем файл с несколькими разделителями: запятая, пробел и табуляция
    with open('users.csv', newline='', encoding='utf-8') as csvfile:
        content = csvfile.read().splitlines()
        for line in content:
            # Используем регулярное выражение для разделения по запятым, пробелам или табуляциям справа
            row = re_rsplit(r'[,\s\t]+', line.strip(), maxsplit=3)  # Используем rsplit для корректного разделения справа
            if len(row) < 4:
                results.append(f"Ошибка: недостаточно данных для строки {row}")
                continue

            full_name, login, password, program = row

            # Проверка на дублирование
            duplicate = await validate_duplicates(full_name)
            if duplicate:
                await bot.send_message(SUPERADMIN_USERNAME, f"Внимание: найдены похожие ФИО: {full_name} и {duplicate}")

            await add_student(full_name, login, password, program)
            results.append(f"Пользователь {full_name} добавлен.")

    await message.answer('\n'.join(results)[:4000])
    await state.finish()


# Команда для поиска студентов по программе
@dp.message_handler(lambda message: message.text == "Показать студентов по программе")
@admin_only
async def list_program_students(message: types.Message):
    log_command(message, '/list_program')
    await message.answer("Введите название программы:")
    await Form.list_program.set()


@dp.message_handler(state=Form.list_program)
async def process_list_program(message: types.Message, state: FSMContext):
    program = message.text.strip()

    students = await get_students_by_program(program)
    if students:
        result = '\n'.join([f"{s[0]} - Логин: {s[1]}, Пароль: {s[2]}, Телеграм: {s[3]}" for s in students])
        await message.answer(f"Студенты программы {program}:\n{result[:4000]}")
    else:
        await message.answer(f"Студенты по программе {program} не найдены.")

    await state.finish()


# Команда для поиска студента по логину
@dp.message_handler(lambda message: message.text == "Найти студента по логину")
@admin_only
async def get_fio_by_login_start(message: types.Message):
    log_command(message, '/get_fio_by_login')
    await message.answer("Введите логин студента:")
    await Form.get_fio_by_login.set()


@dp.message_handler(state=Form.get_fio_by_login)
async def process_get_fio_by_login(message: types.Message, state: FSMContext):
    login = message.text.strip()

    student = await get_student_by_login(login)
    if student:
        await message.answer(f"Студент с логином {login}:\nФИО: {student[1]}")
    else:
        await message.answer(f"Студент с логином {login} не найден.")

    await state.finish()


# Команда для поиска студента по Telegram нику
@dp.message_handler(lambda message: message.text == "Найти студента по Telegram")
@admin_only
async def get_fio_by_tg_start(message: types.Message):
    log_command(message, '/get_fio_by_tg')
    await message.answer("Введите Telegram ник студента:")
    await Form.get_fio_by_tg.set()


@dp.message_handler(state=Form.get_fio_by_tg)
async def process_get_fio_by_tg(message: types.Message, state: FSMContext):
    username = message.text.strip().strip('@')

    student = await get_student_by_tg_username(username)
    if student:
        await message.answer(f"Студент с Telegram ником @{username}:\nФИО: {student[1]}")
    else:
        await message.answer(f"Студент с Telegram ником @{username} не найден.")

    await state.finish()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db(SUPERADMIN_USERNAME))
    executor.start_polling(dp, skip_updates=True)

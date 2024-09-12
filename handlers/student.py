from config import SUPERADMIN_USERNAME
from states import Form
from aiogram import types
from aiogram.dispatcher import FSMContext


from lib import log_command
from database import get_student_by_fio, update_student_tg


# Проверка ФИО и отправка логина-пароля студенту
async def process_fio_check(message: types.Message, state: FSMContext):
    log_command(message, '/process_fio_check')
    full_name = message.text.strip()
    telegram_username = message.from_user.username

    # Поиск студента по ФИО (сначала точное совпадение, затем приближенное)
    student = await get_student_by_fio(full_name)
    if student:
        login = student[1]
        password = student[2]

        # Отправка логина и пароля студенту
        await message.answer(f"Ваши данные:\nЛогин: {login}\nПароль: {password}")

        # Обновляем информацию в базе данных о нике в Telegram
        await update_student_tg(full_name, telegram_username)

        await message.answer("Ваш Telegram ID сохранен в базе данных.")
    else:
        await message.answer(f"Запись с ФИО {full_name} не найдена. Пожалуйста, обратитесь к лектору: {SUPERADMIN_USERNAME}")

    await message.answer("Чтобы воспользоваться ботом снова, нажмите /start.")
    await state.finish()


# Регистрация обработчика для студентов
def register_student_handlers(dp):
    dp.register_message_handler(process_fio_check, state=Form.check_fio)

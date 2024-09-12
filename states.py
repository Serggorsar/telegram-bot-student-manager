from aiogram.dispatcher.filters.state import State, StatesGroup


# Состояния для добавления, обновления и удаления пользователей
class Form(StatesGroup):
    add_user = State()
    update_user = State()
    delete_user = State()
    add_from_file = State()
    add_admin = State()
    delete_admin = State()
    get_fio_by_login = State()
    get_fio_by_tg = State()
    check_fio = State()
    list_program = State()
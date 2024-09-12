import aiosqlite
from fuzzywuzzy import fuzz


async def init_db(SUPERADMIN_USERNAME):
    async with aiosqlite.connect('students.db') as db:
        # Создаем таблицу студентов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                login TEXT,
                password TEXT,
                program TEXT,
                telegram_username TEXT
            )
        ''')
        # Создаем таблицу админов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                telegram_username TEXT PRIMARY KEY,
                role TEXT  -- роль: 'superadmin' или 'admin'
            )
        ''')
        await db.commit()

        # Проверяем, есть ли суперадмин в таблице
        cursor = await db.execute("SELECT telegram_username FROM admins WHERE role = 'superadmin'")
        superadmin = await cursor.fetchone()

        # Если суперадмина нет, добавляем его
        if not superadmin:
            await db.execute("INSERT INTO admins (telegram_username, role) VALUES (?, ?)", (SUPERADMIN_USERNAME, 'superadmin'))
            await db.commit()
            print(f"Superadmin @{SUPERADMIN_USERNAME} has been added.")


# Функция для поиска студента с приоритетом на точное совпадение, затем с учетом ошибок
async def get_student_by_fio(full_name):
    async with aiosqlite.connect('students.db') as db:
        # Сначала пытаемся найти точное совпадение
        cursor = await db.execute("SELECT full_name, login, password FROM students WHERE full_name = ?", (full_name,))
        student = await cursor.fetchone()

        if student:
            return student

        # Если точное совпадение не найдено, ищем с помощью Левенштейна
        cursor = await db.execute("SELECT full_name, login, password FROM students")
        students = await cursor.fetchall()

        # Пробегаем по всем студентам и ищем наиболее похожее ФИО
        best_match = None
        best_score = 0
        normalized_name = normalize_fio(full_name)

        for student in students:
            db_full_name = normalize_fio(student[0])
            score = fuzz.ratio(normalized_name, db_full_name)  # Сравниваем с учетом опечаток

            if score > best_score:
                best_score = score
                best_match = student

        # Если совпадение лучше 90%, считаем, что это правильное ФИО
        if best_match and best_score >= 90:
            return best_match

        return None


# Функция для нормализации ФИО (замена е/ё и удаление лишних символов)
def normalize_fio(fio):
    fio = fio.lower().replace('ё', 'е')  # Нормализуем е/ё
    return fio


# Функция для обновления Telegram ID и никнейма студента
async def update_student_tg(full_name, telegram_username):
    async with aiosqlite.connect('students.db') as db:
        await db.execute("""
            UPDATE students 
            SET telegram_username = ? 
            WHERE full_name = ?
        """, (telegram_username, full_name))
        await db.commit()  # Подтверждаем изменения


async def add_student(full_name, login, password, program, telegram_username=None):
    async with aiosqlite.connect('students.db') as db:
        await db.execute("INSERT INTO students (full_name, login, password, program, telegram_username) VALUES (?, ?, ?, ?, ?)",
                         (full_name, login, password, program, telegram_username))
        await db.commit()


async def update_student_login_password(full_name, new_login, new_password):
    async with aiosqlite.connect('students.db') as db:
        await db.execute("UPDATE students SET login = ?, password = ? WHERE full_name = ?",
                         (new_login, new_password, full_name))
        await db.commit()


# Функция для удаления студента по ФИО
async def delete_student(full_name):
    async with aiosqlite.connect('students.db') as db:
        # Проверяем, существует ли пользователь
        cursor = await db.execute("SELECT 1 FROM students WHERE full_name = ?", (full_name,))
        student_exists = await cursor.fetchone()

        if student_exists:
            # Выполняем удаление и проверяем количество затронутых строк
            cursor = await db.execute("DELETE FROM students WHERE full_name = ?", (full_name,))
            await db.commit()

            # Проверяем, был ли удален хотя бы один пользователь
            if cursor.rowcount > 0:
                return True  # Пользователь успешно удален
            else:
                return False  # Не удалось удалить пользователя
        else:
            return False  # Пользователь не найден


async def get_students_by_program(program):
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT full_name, login, password, telegram_username FROM students WHERE program = ?", (program,))
        students = await cursor.fetchall()
        return students


async def get_student_by_login(login):
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT * FROM students WHERE login = ?", (login,))
        student = await cursor.fetchone()
        return student


async def get_student_by_tg_username(username):
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT * FROM students WHERE telegram_username = ?", (username,))
        student = await cursor.fetchone()
        return student


async def get_all_students():
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT full_name, login, password, program, telegram_username FROM students")
        students = await cursor.fetchall()
        return students


async def check_for_duplicate_tg(full_name, telegram_username):
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT telegram_username FROM students WHERE full_name = ?", (full_name,))
        existing_user = await cursor.fetchone()

        if existing_user and existing_user[0] != telegram_username:
            return True
    return False


async def validate_duplicates(full_name):
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT full_name FROM students")
        students = await cursor.fetchall()

        for student in students:
            ratio = fuzz.ratio(full_name.lower(), student[0].lower())
            if ratio > 90:  # Если ФИО почти совпадают
                return student[0]  # Возвращаем похожее ФИО
    return None


async def is_admin(telegram_username, required_role='admin'):
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT role FROM admins WHERE telegram_username = ?", (telegram_username,))
        result = await cursor.fetchone()
        if result:
            if required_role == 'superadmin':
                return result[0] == 'superadmin'
            return True
        return False


async def add_admin(telegram_username, role='admin'):
    async with aiosqlite.connect('students.db') as db:
        await db.execute("INSERT INTO admins (telegram_username, role) VALUES (?, ?)", (telegram_username, role))
        await db.commit()


async def delete_admin(telegram_username):
    async with aiosqlite.connect('students.db') as db:
        await db.execute("DELETE FROM admins WHERE telegram_username = ?", (telegram_username,))
        await db.commit()  # Подтверждаем изменения


async def get_all_admins():
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT telegram_username FROM admins")
        admins = await cursor.fetchall()
        return [admin[0] for admin in admins]


async def get_user_by_username(username):
    async with aiosqlite.connect('students.db') as db:
        cursor = await db.execute("SELECT telegram_username FROM admins WHERE telegram_username = ?", (username,))
        return await cursor.fetchone()

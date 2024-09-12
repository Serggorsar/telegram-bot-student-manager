import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPERADMIN_USERNAME = os.getenv('SUPERADMIN_USERNAME', '@tg_nik').lstrip('@')  # Ник в телеграме лектора
# TODO: убрать SUPERADMIN_ID
SUPERADMIN_ID = int(os.getenv('SUPERADMIN_ID', ''))  # ID в телеграме. Можно получить, написав в бот @userinfobot

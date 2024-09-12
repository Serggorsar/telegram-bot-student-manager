import logging
import re
from aiogram.types import Message


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Логирование для всех команд
def log_command(message, command_name):
    logger.info(f"Начало обработки команды {command_name} от пользователя {message.from_user.id}")


# re.split like str.rsplit https://stackoverflow.com/a/71645254
def re_rsplit(pattern, text, maxsplit):
    pattern = re.compile(pattern)
    if maxsplit < 1 or not pattern.search(text): # If split is 0 or less, or upon no match
        return [text]                            # Return the string itself as a one-item list
    prev = len(text)                             # Previous match value start position
    cnt = 0                                      # A match counter
    result = []                                  # Output list
    for m in reversed(list(pattern.finditer(text))):
        result.append(text[m.end():prev])        # Append a match to resulting list
        prev = m.start()                         # Set previous match start position
        cnt += 1                                 # Increment counter
        if cnt == maxsplit:                      # Break out of for loop if...
            break                                # ...match count equals max split value
    result.append(text[:prev])                   # Append the text chunk from start
    return list(reversed(result))                # Return reversed list


# Функция для отправки длинных сообщений, разбивая их по строкам."
async def send_long_message(message: Message, text: str):
    lines = text.split('\n')
    chunk_size = 3072  # Максимальный размер одного сообщения
    current_chunk = ""

    for line in lines:
        # Если добавление очередной строки превысит лимит, отправляем сообщение
        if len(current_chunk) + len(line) + 1 > chunk_size:
            await message.answer(current_chunk)
            current_chunk = line  # Начинаем новый блок с текущей строки
        else:
            # Добавляем строку в текущий блок
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

    # Отправляем оставшийся текст
    if current_chunk:
        await message.answer(current_chunk)

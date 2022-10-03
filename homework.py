import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import (HomeworkNameNotInDict, HomeworkNotList,
                        HomeworksNotInDict, HomeworkStatusesError,
                        ResponseDictEmpty, ResponseNotDict,
                        ResponseStatusNotOK, StatusNotInDict)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('Token_ya')
TELEGRAM_TOKEN = os.getenv('Token_tlgrm')
TELEGRAM_CHAT_ID = os.getenv('Chat_id')
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)
fileHandler = logging.FileHandler("logfile.log", encoding='UTF-8')
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)


def send_message(bot, message):
    """Функция отправляет сообщения в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        logger.error('Cбой при отправке сообщения в Telegram')
    else:
        logger.info(f'Бот отправил сообщение: {message}')


def get_api_answer(current_timestamp):
    """Функция делает запрос к эндпоинту API-сервиса и возвращает ответ API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(f'Ошибка при запросе к API yandex practicum: {error}')
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        logger.error(f'Ошибка! Status_code {status_code}')
        raise ResponseStatusNotOK(f'Ошибка! Status_code {status_code}')
    return response.json()


def check_response(response):
    """Функция проверяет запрос API на корректность.
    Возвращает список домашних работ по ключу 'homeworks'.
    """
    if type(response) is not dict:
        logger.error('Ответ от API не содержит словарь!')
        raise ResponseNotDict('Ответ от API не содержит словарь!')
    if not response:
        logger.error('Ответ от API содержит пустой словарь!')
        raise ResponseDictEmpty('Ответ от API содержит пустой словарь!')
    if 'homeworks' not in response:
        logger.error('Ответ от API не содержит ключа `homeworks`!')
        raise HomeworksNotInDict('Ответ от API не содержит ключа `homeworks`!')
    homeworks = response.get('homeworks')
    if type(homeworks) is not list:
        logger.error(
            'Домашняя работа в ответе от API получена не ввиде списка!')
        raise HomeworkNotList(
            'Домашняя работа в ответе от API получена не ввиде списка!')
    return homeworks


def parse_status(homework):
    """Функция извлекает из инф-ции о конкретной домашней работе ее статус."""
    if 'homework_name' not in homework:
        logger.error('Ключ [homework_name] не найден в словаре!')
        raise HomeworkNameNotInDict(
            'Ключ [homework_name] не найден в словаре!')
    if 'status' not in homework:
        logger.error('Ключ [status] не найден в словаре!')
        raise StatusNotInDict('Ключ [status] не найден в словаре!')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error('Cтатус домашней работы не документирован!')
        raise HomeworkStatusesError(
            'Cтатус домашней работы не документирован!')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None \
            or TELEGRAM_CHAT_ID is None:
        logger.critical('Ошибка чтения переменных окружения!')
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(0)
    homework_status = ''
    get_api_answer_error = ''
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logger.debug('В ответе нет новых статусов!')
            else:
                homework = homeworks[0]
                new_status = parse_status(homework)
                if homework_status != new_status:
                    send_message(bot, new_status)
                    homework_status = new_status

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if get_api_answer_error != message:
                send_message(bot, message)
                get_api_answer_error = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

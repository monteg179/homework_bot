"""Docstring."""

from http import HTTPStatus
import logging
import os
import requests
import sys
import time
from typing import Any, Final

import telegram
import dotenv

import exceptions

dotenv.load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 60 * 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS: dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class Logger():
    """Docstring."""

    STREAM_FORMAT: Final[str] = '%(asctime)s  [%(levelname)s]  %(message)s'

    FILE_FORMAT: Final[str] = ('%(asctime)s  [%(levelname)s]  '
                               '[%(filename)s:%(lineno)s] '
                               '[%(funcName)s]  %(message)s')

    FILE_NAME: Final[str] = 'blackbox.log'

    @staticmethod
    def create(name: str) -> logging.Logger:
        """Docstring."""
        logging.basicConfig(
            format=Logger.STREAM_FORMAT,
            level=logging.DEBUG,
            stream=sys.stdout
        )
        file_handler = logging.FileHandler(Logger.FILE_NAME, mode='a')
        file_handler.setFormatter(logging.Formatter(Logger.FILE_FORMAT))
        logger = logging.getLogger(name)
        logger.addHandler(file_handler)
        return logger


logger = Logger.create(__name__)


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    env = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    return all(env)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в Telegram."""
    logger.debug('Отправка сообщения')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения {str(error)}')
    else:
        logger.debug('Отправка сообщения выполнена успешно')


def get_api_answer(timestamp: int) -> dict[str, Any]:
    """Запрос к API Практикум.Домашка."""
    logger.debug('Запрос к Практикум.Домашка')
    try:
        response: requests.Response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            error_msg = (
                f'HTTP error: {response.status_code} '
                f'{response.reason} '
                f'{response.text} '
                f'{response.request.url} '
                f'{response.request.headers} '
                f'{timestamp}'
            )
            logger.debug(error_msg)
            raise requests.HTTPError(response)
        json = response.json()
    except Exception as error:
        error_msg = f'Ошибка запроса к Практикум.Домашка: {str(error)}'
        raise exceptions.RequestError(error_msg) from error
    else:
        logger.debug('Запрос к Практикум.Домашка выполнен успешно')
        return json


def check_response(response: dict[str, Any]) -> bool:
    """Проверка ответа API Практикум.Домашка."""
    logger.debug('Проверка ответа Практикум.Домашка')
    if not isinstance(response, dict):
        error_msg = (
            f'Ошибка проверки ответа, '
            f'response: {type(response)} = `{response}`'
        )
        raise TypeError(error_msg)
    current_date = response.get('current_date')
    if not isinstance(current_date, int):
        error_msg = (
            f'Ошибка проверки ответа, '
            f'current_date: {type(current_date)} = `{current_date}`'
        )
        raise TypeError(error_msg)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        error_msg = (
            f'Ошибка проверки ответа, '
            f'homeworks: {type(homeworks)} = `{homeworks}`'
        )
        raise TypeError(error_msg)
    logger.debug('Проверка ответа Практикум.Домашка выполнена успешно')
    return True


def parse_status(homework: dict[str, Any]) -> str:
    """Парсинг ответа API Практикум.Домашка."""
    logger.debug('Парсинг ответа Практикум.Домашка')
    try:
        homework_name = homework['homework_name']
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError as error:
        error_msg = f'Ошибка парсинга ответа Практикум.Домашка {str(error)}'
        raise exceptions.ParseResponseError(error_msg) from error
    else:
        logger.debug('Парсинг ответа Практикум.Домашка выполнен успешно')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        error_msg = ('Отсутствуют обязательные переменные окружения. '
                     'Программа будет принудительно остановлена')
        logger.critical(error_msg)
        sys.exit(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    last_error = None
    timestamp = int(time.time())
    logger.debug(f'Запуск Telegram-бота, timestamp = {timestamp}')
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            timestamp = response.get('current_date')
            homeworks = response.get('homeworks')
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.debug('В ответе нет новых статусов')
            last_error = None
        except exceptions.HomeworkError as homework_error:
            logger.error(str(homework_error))
            if homework_error != last_error:
                send_message(bot, str(homework_error))
            last_error = homework_error
        except Exception as error:
            logger.error(str(error))
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

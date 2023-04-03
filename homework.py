"""Docstring."""

import logging
import os
import requests
import sys
import time
from typing import Any, Final, Mapping

import telegram
import dotenv

import exceptions

dotenv.load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600.0
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS: dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class Logger():
    """Docstring."""

    FORMAT: Final[str] = ('%(asctime)s  [%(levelname)s]  '
                          '[%(filename)s:%(lineno)s] [%(funcName)s]  '
                          '%(message)s')

    FILE_NAME: Final[str] = 'homeworks.log'

    @staticmethod
    def create(name: str) -> logging.Logger:
        """Docstring."""
        formatter = logging.Formatter(Logger.FORMAT)
        file_handler = logging.FileHandler(Logger.FILE_NAME, mode='a')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.DEBUG)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        return logger


logger = Logger.create(__name__)


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    error_prefix = 'Отсутствует обязательная переменная'
    names = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    global_vars = globals()
    result = True
    for name in names:
        if global_vars.get(name) is None:
            result = False
            logger.critical(f'{error_prefix} {name}')
    return result


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в Telegram."""
    try:
        logger.debug(f'Отправка сообщения: {message}')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Отправка сообщение выполнена успешно')
    except Exception as error:
        error_text = str(error)
        logger.error(error_text)
        raise exceptions.SendMessageError(error_text) from error


def send_alarm(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в Telegram с подавлением исключений."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Отправка сообщение выполнена успешно')
    except Exception as error:
        logger.error(str(error))


def get_api_answer(timestamp: int) -> dict[str, Any]:
    """Запрос к API Практикум.Домашка."""
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        # response.raise_for_status()
        if response.status_code != 200:
            error_text = f'http error: status_code = {response.status_code}'
            raise requests.HTTPError(error_text)
        json = response.json()
        logger.debug('Запрос к Практикум.Домашка выполнен успешно')
        return json
    except Exception as error:
        error_text = str(error)
        logger.error(error_text)
        raise exceptions.RequestError(error_text) from error


def check_response(response: dict[str, Any]) -> bool:
    """Проверка ответа API Практикум.Домашка."""
    error_prefix = 'Ошибка проверки ответа:'
    if not isinstance(response, Mapping):
        error_text = f'{error_prefix} response: {type(response)}'
        logger.error(error_text)
        raise TypeError(error_text)
    current_date = response.get('current_date')
    if not isinstance(current_date, int):
        error_text = (f'{error_prefix} current_date: '
                      f'{type(current_date)} = "{current_date}"')
        logger.error(error_text)
        raise TypeError(error_text)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        error_text = f'{error_prefix} homeworks: {type(homeworks)}'
        logger.error(error_text)
        raise TypeError(error_text)
    for homework in homeworks:
        name = homework.get('homework_name')
        if not name or not isinstance(name, str):
            error_text = (f'{error_prefix} homework_name: '
                          f'{type(name)} = "{name}"')
            logger.error(error_text)
            raise TypeError(error_text)
        status = homework.get('status')
        if not status or not isinstance(status, str):
            error_text = f'{error_prefix} status: {type(status)} = {status}'
            logger.error(error_text)
            raise TypeError(error_text)
    logger.debug('Проверка ответа Практикум.Домашка выполнена успешно')
    return True


def parse_status(homework: dict[str, Any]) -> str:
    """Парсинг ответа API Практикум.Домашка."""
    try:
        homework_name: str = homework['homework_name']
        status: str = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
        logger.debug('Парсинг ответа Практикум.Домашка выполнен успешно')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        error_text = str(error)
        logger.error(error_text)
        raise exceptions.ParseResponseError(error_text) from error


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.info('Программа будет принудительно остановлена')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Запуск Telegram-бота')
    last_error = None
    timestamp = int(time.time())
    # timestamp = 0
    while True:
        try:
            response: dict[str, Any] = get_api_answer(timestamp)
            check_response(response)
            timestamp = response.get('current_date')
            homeworks: list[dict[str, Any]] = response.get('homeworks')
            if len(homeworks) == 0:
                logger.debug('В ответе нет новых статусов')
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
            last_error = None
        except exceptions.SendMessageError:
            pass
        except Exception as error:
            if error != last_error:
                send_alarm(bot, str(error))
            last_error = error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

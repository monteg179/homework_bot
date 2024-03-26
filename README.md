# HOMEWORK BOT

## ОПИСАНИЕ
Телеграм-бот для отслеживания статуса проверки домашней работы на Яндекс.Практикум.
Присылает сообщения при изменении статуса задания сданного на проверку.

## ЗАПУСК ПРОЕКТА
1. клонировать репозиторий
```sh
git clone git@github.com:monteg179/homework_bot.git
cd homework_bot
```

2. создать и заполнить файл .env
```
PRACTICUM_TOKEN=<токен Яндекс.Практикум>
TELEGRAM_TOKEN=<токен telegram бота>
TELEGRAM_CHAT_ID=<telegram id>
```

3. создать, запустить и настроить виртуальное окружение
```sh
python -m venv .venv
source .env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

4. запуск
```sh
python homework.py
```

## ИСПОЛЬЗОВАННЫЕ ТЕХНОЛОГИИ
- Python
- Python Telegram Bot

## АВТОРЫ
* Сергей Кузнецов - monteg179@yandex.ru

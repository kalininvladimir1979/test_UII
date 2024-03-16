# pip install "python-telegram-bot[job-queue]"
# pip install gspread

import openai
import os
import requests
import aiohttp
import json
import time
import pickle
import gspread
import json
import asyncio
import datetime
# функция для асинхронного общения с сhatgpt
import httpx

# from oauth2client.service_account import ServiceAccountCredentials
# from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext import Updater
from telegram import Update
from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from datetime import datetime
from langchain.docstore.document import Document
# from aiogram.types import InputFile

import json
import asyncio
import aiohttp
import shutil


### -------------------------------------------------------------------------------------

#@title Запустим для начала эту кнопку
# %pip install openai==0.28
# %pip install python-dotenv

MODEL_TURBO_16K = "gpt-3.5-turbo-16k"
MODEL_TURBO_0613 = "gpt-3.5-turbo-0613"
MODEL_GPT4 = "gpt-4-0613"

system = """
Ты - специалист по определению настроения текстовых сообщений от пользователя.
Ты профессионально различаешь позитивный текст от негативного.
Если вопрос пользователя позитивный, то ответь одним словом: "positive"
Если вопрос пользователя негативный, то ответь одним словом: "negative"
Не называй клиента 'клиентом', обращайся к клиенту по имени? если оно известно.
Обращайся к клиенту на 'вы'
Не говори о клиенте в третьем лице.
"""

system_positive = """
Ты - специалист по ответам пользователя в стиле Бетмана.
Ты отвечаешь на вопрос пользователя как главный персонаж из фильмы 'Бетман'
Не называй клиента 'клиентом', обращайся к клиенту по имени? если оно известно.
Обращайся к клиенту на 'вы'
Не говори о клиенте в третьем лице.
"""

system_negative = """
Ты - специалист по ответам пользователя в стиле Джокер.
Ты отвечаешь на вопрос пользователя как главный персонаж из фильмы 'Джокер'
Не называй клиента 'клиентом', обращайся к клиенту по имени? если оно известно.
Обращайся к клиенту на 'вы'
Не говори о клиенте в третьем лице."""

def analitic_topic(model, topic, system, temperature=0):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Скажите пожалуйсьта, как с вами связаться?"},
        {"role": "assistant", "content": "positive"},
        {"role": "user", "content": "Сколько вас можно ждать, ответте уже наконец-то?"},
        {"role": "assistant", "content": "negative"},
        {"role": "user", "content": topic}
    ]
    completion = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return completion.choices[0].message.content


def answer(ocenka, model, topic, temperature=0):
    if ocenka == 'positive':
        system = system_positive
    elif ocenka == 'negative':
        system = system_negative

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": topic}
    ]
    completion = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return completion.choices[0].message.content



### -------------------------------------------------------------------------------------

# подгружаем переменные окружения
load_dotenv(".env")
# передаем секретные данные в переменные
TOKEN = os.environ.get("TG_TOKEN")
GPT_SECRET_KEY = os.environ.get("OPENAI_API_KEY")
# передаем секретный токен chatgpt
openai.api_key = GPT_SECRET_KEY


# Проверка загрузки ключа AI
if not GPT_SECRET_KEY:
    print("Ключ не читается")
else:
    print(f"----------\nКлюч OpenAI загружен | {len(GPT_SECRET_KEY)}") 
# Проверка загрузки ключа TG
if not TOKEN:
    print("Ключ TG не читается")
else:
    print(f"Ключ TG загружен     | {len(TOKEN)}")


# функция-обработчик команды /start 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        
    # Путь к изображению
    image_path = "betmen_djoker.jpg"
    
    # Открываем файл изображения для чтения в двоичном режиме
    with open(image_path, 'rb') as photo:
        # Отправляем изображение вместе с текстом
        await update.message.reply_photo(photo, caption='''Добро пожовать в мир чудных героев Бетмена и Джокера. 
Вы никогда не будете знать, кто с вами будет говорить, но со временем вы найдете закономерность. 
Удачи, напишите мне что-нибудь!''')


#### --------------------------------------------------------------
        
topic = "Кто ты, злое создание!?" #@param {type:"string"}

ocenka = analitic_topic(MODEL_TURBO_0613, topic, system)
print("Оценка вопроса: ", ocenka)

answer_topic = answer(ocenka, MODEL_TURBO_0613, topic)
print("Ответ: \n", answer_topic)

#### --------------------------------------------------------------


# функция-обработчик текстовых сообщений
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = update.message.text
    
    # выполнение запроса в chatgpt
    first_message = await update.message.reply_text('Ваше сообщение принято, ответ скоро придет...')
    
    ocenka = analitic_topic(MODEL_TURBO_0613, topic, system)
    print("Оценка вопроса: ", ocenka)

    answer_topic = answer(ocenka, MODEL_TURBO_0613, topic)
    print("Ответ: \n", answer_topic)

    # Отправляем только answer в чат
    await context.bot.edit_message_text(text=answer_topic, chat_id=update.message.chat_id, message_id=first_message.message_id)

    return

def main():

    # создаем приложение и передаем в него токен бота
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    # добавление обработчиков
    application.add_handler(CommandHandler("start", start, block=False))
    application.add_handler(MessageHandler(filters.TEXT, text, block=False))

    # запуск бота (нажать Ctrl+C для остановки)
    application.run_polling()
    print('Бот остановлен')

if __name__ == "__main__":
    main()
import asyncio
import logging
import sqlite3
import re
import requests
import nest_asyncio
import random
import os
from aiohttp import web
nest_asyncio.apply()

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, BusinessConnection, BotCommand
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- Конфигурация ---
TOKEN = os.getenv('TOKEN')
WEB_SERVER_HOST = '0.0.0.0'  # Хост для веб-сервера
WEB_SERVER_PORT = 3000       # Порт для веб-сервера
WEBHOOK_PATH = '/webhook'    # Путь для вебхука

DB_PATH = "bahur_bot.db"
BASE_WEBHOOK_URL = os.getenv('WEBHOOK_BASE_URL')

# --- Инициализация бота ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DeepSeek и данные Bahur ---
def load_bahur_data():
    with open("bahur_data.txt", "r", encoding="utf-8") as f:
        return f.read()

BAHUR_DATA = load_bahur_data()

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Первый ряд (1 кнопка)
    builder.row(
        InlineKeyboardButton(text='🧸 Ai-Медвежонок', callback_data='ai')
    )
    
    # Второй ряд (3 кнопки)
    builder.row(
        InlineKeyboardButton(text='🍦 Прайс', url="https://drive.google.com/file/d/1J70LlZwh6g7JOryDG2br-weQrYfv6zTc/view?usp=sharing"),
        InlineKeyboardButton(text='🍿 Магазин', url="https://www.bahur.store/m/"),
        InlineKeyboardButton(text='♾️ Вопросы', url="https://vk.com/@bahur_store-optovye-praisy-ot-bahur")
    )
    
    # Третий ряд (3 кнопки)
    builder.row(
        InlineKeyboardButton(text='🎮 Чат', url="https://t.me/+VYDZEvbp1pce4KeT"),
        InlineKeyboardButton(text='💎 Статьи', url="https://vk.com/bahur_store?w=app6326142_-133936126%2523w%253Dapp6326142_-133936126"),
        InlineKeyboardButton(text='🏆 Отзывы', url="https://vk.com/@bahur_store")
    )

    builder.row(
        InlineKeyboardButton(text='🍓 Ноты', callback_data='instruction')
    )
    
    return builder.as_markup()  # Убрал resize_keyboard=True для Inline клавиатуры

def create_reply_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    builder.row(KeyboardButton(text='🍓 Ноты'))
    builder.row(
        KeyboardButton(text='🍦 Прайс'),
        KeyboardButton(text='🍿 Магазин'),
        KeyboardButton(text='♾️ Вопросы')
    )
    builder.row(
        KeyboardButton(text='🎮 Чат'),
        KeyboardButton(text='💎 Статьи'),
        KeyboardButton(text='🏆 Отзывы')
    )
    builder.row(KeyboardButton(text='🧸 Ai-Медвежонок'))
    
    return builder.as_markup(resize_keyboard=True)

# --- Настройки ---
TOKEN = '8102330882:AAESnqYWciSpebuEmghAqjTKcgJtq3fSQ-4'

# --- DeepSeek и данные Bahur ---
def load_bahur_data():
    with open("bahur_data.txt", "r", encoding="utf-8") as f:
        return f.read()

BAHUR_DATA = load_bahur_data()

def greet():
    return random.choice([
    "Привет-привет! 🐾 Готов раскрыть все секреты продаж — спрашивай смело!",
    "Эй, друг! 🌟 Ai-Медвежонок на связи — давай обсудим твои вопросы за виртуальным мёдом!",
    "Мягкий привет! 🧸✨ Хочешь, расскажу, как продавать лучше, чем медведь в лесу малину?",
    "Здравствуй, человек! 🌟 Готов устроить мозговой штурм? Задавай вопрос — я в деле!",
    "Приветик из цифровой берлоги! 🐻‍❄️💻 Чем могу помочь? (Совет: спроси что-нибудь классное!)",
    "Алло-алло! 📞 Ты дозвонился до самого продающего медведя в сети. Вопросы — в студию!",
    "Хей-хей! 🎯 Готов к диалогу, как пчела к мёду. Запускай свой запрос!",
    "Тыдыщь! 🎩✨ Ai-Медвежонок-волшебник приветствует тебя. Какой вопрос спрятан у тебя в рукаве?",
    "Привет, землянин! 👽🐻 (Шучу, я просто AI). Давай общаться — спрашивай что угодно!"
    ])


def ask_deepseek(question):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-a6d1ccf8368d4e23a01712ccfc4d4e71",  # <-- Вставьте свой ключ
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты - Ai-Медвежонок (менеджер по продажам), здоровайся креативно, зная это. Используй ТОЛЬКО эти данные для ответа клиенту:\n"
                    f"{BAHUR_DATA}\n"
                    "Если есть подходящая ссылка из данных, обязательно включи её в ответ. "
                    "Отвечай только по теме вопроса, без лишней информации, на русском языке, без markdown, обязательно с крутыми смайликами."
                    "Если вопрос не по теме, то обязательно переведи в шутку, никаких 'не знаю' и аккуратно предложи купить духи"
                    "Когда вставляешь ссылку, используй HTML-формат: <a href='ССЫЛКА'>ТЕКСТ</a>. Не используй markdown."
                    "Но если он пишет несколько слов, которые похожи на ноты, предложи ему нажать на кнопку 🍓 Ноты в меню"
                    "Не пиши про номера ароматов в прайсе"
                )
            },
            {
                "role": "user",
                "content": f"{question}"
            }
        ],
        "temperature": 0.9
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Состояния пользователей для AI ---
user_states = {}

# --- Healthcheck endpoint ---
async def healthcheck(request):
    logging.info("Healthcheck requested")
    return web.Response(text="OK")

# --- Обработка обычных сообщений ---
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_regular_message(message: Message):
    logging.info(f"Received message from user {message.from_user.id}: {message.text}")
    user_id = message.from_user.id
    # Режим AI
    if user_states.get(user_id) == 'awaiting_ai_question':
        question = message.text.strip()
        try:
            logging.info(f"Sending question to DeepSeek: {question}")
            await message.answer("Начинаю поиск...")
            ai_answer = ask_deepseek(question)
            await message.answer(ai_answer, parse_mode=ParseMode.HTML)
            logging.info("AI answer sent")
        except Exception as e:
            ai_answer = "Ошибка при обращении к AI: " + str(e)
            await message.answer(ai_answer)
            logging.error(f"AI error: {e}")
        return
    # Обычный поиск
    text = message.text.strip().lower()
    search_vals = [v for v in map(str.strip, text.split(',')) if v]
    if not search_vals:
        await message.answer('Пустой запрос!')
        logging.warning("Empty search query")
        return
    search_pattern = '|'.join(map(re.escape, search_vals))
    search_sql = ' AND '.join([f"description LIKE '%{v}%'" for v in search_vals])
    query = f"SELECT * FROM aromas WHERE {search_sql} ORDER BY RANDOM() LIMIT 1"
    logging.debug(f"SQL Query: {query}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query)
    db_val = c.fetchone()
    logging.debug(f"db_val: {db_val}")
    if db_val:
        brand, aroma, description, url = db_val[1], db_val[2], db_val[3], db_val[4]
        matches = list(re.finditer(search_pattern, description, re.IGNORECASE))
        for match in set(m.group(0) for m in matches):
            description = re.sub(re.escape(match), f'<u><b>{match}</b></u>', description, flags=re.IGNORECASE)
        c.execute('INSERT INTO finds(search_string, patterns) VALUES (?, ?)', (query, search_pattern))
        find_id = c.lastrowid
        conn.commit()
        keyboard = [
            [InlineKeyboardButton(text='🚀 Подробнее', url=url), InlineKeyboardButton(text='♾️ Повторить', callback_data=f'repeat_{find_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.answer(f'✨ {brand} {aroma}\n\n{description}', reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        logging.info(f"Found and sent aroma: {brand} {aroma}")
    else:
        await message.answer('Я отвечаю за ноты. С этим вопросом тебя ждёт 🧸 Ai-Медвежонок в меню')
        logging.info("No aroma found for query")
    conn.close()
    logging.debug("DB connection closed")

# --- Обработка обычных команд ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    logging.info(f"/start command from user {message.from_user.id}")
    print("Получена команда /start")
    text = (
        '<b>Здравствуйте!\n\n'
        'Я — ваш ароматный помощник от BAHUR.\n'
        '🍓 Ищу ноты и 🧸 отвечаю на вопросы с любовью. ❤</b>'
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    logging.info("Sent start message with main menu")

# --- Обработка callback-кнопок ---
@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    logging.info(f"Callback from user {user_id}: {data}")
    # Если нажата любая кнопка кроме 'ai', сбрасываем режим AI
    if data != 'ai' and user_id in user_states:
        user_states.pop(user_id, None)
        logging.debug(f"AI state reset for user {user_id}")
    if data == 'instruction':
        text = (
            '🍉 Напиши любую ноту ( апельсин | клубника ) и я пришлю, что найду! 🧸'
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        logging.info("Sent instruction text")
    elif data == 'ai':
        user_states[user_id] = 'awaiting_ai_question'
        result = greet()
        await callback.message.edit_text(result)
        logging.info("Switched user to AI mode and sent greeting")
    elif data.startswith('repeat_'):
        find_id = int(data.split('_')[1])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT search_string, patterns FROM finds WHERE id=?', (find_id,))
        row = c.fetchone()
        if not row:
            await callback.message.edit_text('Ничего не найдено!')
            logging.warning(f"Repeat: find_id {find_id} not found")
            return
        search_string, patterns = row
        c.execute(search_string)
        db_val = c.fetchone()
        if db_val:
            brand, aroma, description, url = db_val[1], db_val[2], db_val[3], db_val[4]
            matches = list(re.finditer(patterns, description, re.IGNORECASE))
            for match in set(m.group(0) for m in matches):
                description = re.sub(re.escape(match), f'<u><b>{match}</b></u>', description, flags=re.IGNORECASE)
            keyboard = [
                [InlineKeyboardButton(text='🚀 Подробнее', url=url), InlineKeyboardButton(text='♾️ Повторить', callback_data=f'repeat_{find_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await callback.message.edit_text(f'✨ {brand} {aroma}\n\n{description}', reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            logging.info(f"Repeat: sent aroma {brand} {aroma}")
        else:
            await callback.message.edit_text('К сожалению, я не смог ничего найти! Попробуйте поискать что-то другое! 🙈')
            logging.info(f"Repeat: no aroma found for find_id {find_id}")
        conn.close()
        logging.debug("DB connection closed (repeat)")
    await callback.answer()
    logging.debug("Callback answered")

# --- Настройка вебхука ---
async def on_startup(bot: Bot):
    logging.info("on_startup: setting webhook...")
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
    logging.info("Webhook set!")

async def on_shutdown(bot: Bot):
    logging.warning('Выключение бота...')
    await bot.delete_webhook()
    logging.warning('Бот выключен')

# --- Запуск приложения ---
def main():
    logging.info("Starting main()...")
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/", healthcheck)
    logging.info("Healthcheck endpoint added at /")
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    logging.info("SimpleRequestHandler created")
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    logging.info(f"Webhook handler registered at {WEBHOOK_PATH}")
    setup_application(app, dp, bot=bot)
    logging.info("Application setup complete")
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logging.info(f"Running app on {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

if __name__ == "__main__":
    main()
# -*- coding: utf8 -*-
import random
from random import randint
import string
import telebot
from telebot import types
from telebot.types import InputMediaPhoto
import requests
import sqlite3
import json
import os
import time
import logging
from PIL import Image
from config import token, admin

bot = telebot.TeleBot(token)

# ============ ЛОГИРОВАНИЕ ============
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============ ПОДКЛЮЧЕНИЕ К БД ============
def get_cursor():
    conn = sqlite3.connect("data.db", check_same_thread=False)
    return conn, conn.cursor()

# ============ СОЗДАНИЕ ТАБЛИЦ ============
conn_init = sqlite3.connect("data.db")
cur_init = conn_init.cursor()

cur_init.execute('''CREATE TABLE if not exists users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT,
    balance INTEGER,
    city TEXT,
    total_spent INTEGER DEFAULT 0
)''')
cur_init.execute('''CREATE TABLE if not exists goods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    name TEXT,
    price INTEGER,
    description TEXT,
    status INTEGER DEFAULT 1
)''')
cur_init.execute('''CREATE TABLE if not exists promocode (
    summa INTEGER,
    code TEXT
)''')
cur_init.execute('''CREATE TABLE if not exists oplata (
    id INTEGER,
    code INTEGER
)''')
cur_init.execute('''CREATE TABLE if not exists card (
    num INTEGER
)''')
cur_init.execute('''CREATE TABLE if not exists orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER,
    good_id INTEGER,
    quantity INTEGER,
    total_price INTEGER,
    status TEXT DEFAULT 'pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
cur_init.execute('''CREATE TABLE if not exists pending_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT DEFAULT 'pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')

try:
    cur_init.execute("ALTER TABLE goods ADD COLUMN city TEXT DEFAULT ''")
    logger.info("Колонка city добавлена в таблицу goods")
except:
    logger.info("Колонка city уже существует")

cur_init.execute("SELECT count(*) FROM card")
if cur_init.fetchone()[0] == 0:
    cur_init.execute("INSERT INTO card (num) VALUES (7777777777)")
conn_init.commit()
conn_init.close()

logger.info("База данных инициализирована")

# ============ ТОВАРЫ ПО ГОРОДАМ ============
CITY_GOODS = {
    "Москва": [
        {"name": "🍃 Трава", "price": 1500, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 3000, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2500, "desc": "Лирика 300мг, оригинал"},
        {"name": "❄️ Кокаин", "price": 5000, "desc": "Чистый продукт, быстрая доставка"},
        {"name": "🔮 МДМА", "price": 3500, "desc": "Кристаллы, танцевальный"},
        {"name": "🌵 2C-B", "price": 4000, "desc": "Дизайнерский трип"},
    ],
    "Санкт-Петербург": [
        {"name": "🍃 Трава", "price": 1400, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2800, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2300, "desc": "Лирика 300мг, оригинал"},
        {"name": "🌀 Кетамин", "price": 3500, "desc": "Чистый кетамин, визуалы"},
        {"name": "💎 Амфетамин", "price": 2000, "desc": "Скорость, качественный продукт"},
        {"name": "🍬 Экстази", "price": 2500, "desc": "Таблетки, проверено"},
    ],
    "Новосибирск": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "🔥 Альфа-PVP", "price": 3500, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "💎 Амфетамин", "price": 1900, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3300, "desc": "Чистый кетамин, визуалы"},
    ],
    "Екатеринбург": [
        {"name": "🍃 Трава", "price": 1500, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 3000, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2500, "desc": "Лирика 300мг, оригинал"},
        {"name": "🍬 Экстази", "price": 2500, "desc": "Таблетки, проверено"},
        {"name": "❄️ Кокаин", "price": 5000, "desc": "Чистый продукт, быстрая доставка"},
        {"name": "🔥 Альфа-PVP", "price": 3500, "desc": "Кристаллы, мощный стимулятор"},
    ],
    "Казань": [
        {"name": "🍃 Трава", "price": 1400, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2900, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2400, "desc": "Лирика 300мг, оригинал"},
        {"name": "🌀 Кетамин", "price": 3400, "desc": "Чистый кетамин, визуалы"},
        {"name": "💎 Амфетамин", "price": 2000, "desc": "Скорость, качественный продукт"},
        {"name": "🔮 МДМА", "price": 3500, "desc": "Кристаллы, танцевальный"},
    ],
    "Нижний Новгород": [
        {"name": "🍃 Трава", "price": 1350, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2800, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2300, "desc": "Лирика 300мг, оригинал"},
        {"name": "🍬 Экстази", "price": 2500, "desc": "Таблетки, проверено"},
        {"name": "🔥 Альфа-PVP", "price": 3500, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "🌀 Кетамин", "price": 3300, "desc": "Чистый кетамин, визуалы"},
    ],
    "Челябинск": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 1900, "desc": "Скорость, качественный продукт"},
        {"name": "🔮 МДМА", "price": 3400, "desc": "Кристаллы, танцевальный"},
        {"name": "❄️ Кокаин", "price": 4800, "desc": "Чистый продукт, быстрая доставка"},
    ],
    "Самара": [
        {"name": "🍃 Трава", "price": 1400, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2900, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2400, "desc": "Лирика 300мг, оригинал"},
        {"name": "🌀 Кетамин", "price": 3500, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2500, "desc": "Таблетки, проверено"},
        {"name": "🔥 Альфа-PVP", "price": 3500, "desc": "Кристаллы, мощный стимулятор"},
    ],
    "Омск": [
        {"name": "🍃 Трава", "price": 1250, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2600, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2100, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 1800, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3200, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2400, "desc": "Таблетки, проверено"},
    ],
    "Ростов-на-Дону": [
        {"name": "🍃 Трава", "price": 1450, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 3000, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2500, "desc": "Лирика 300мг, оригинал"},
        {"name": "❄️ Кокаин", "price": 5000, "desc": "Чистый продукт, быстрая доставка"},
        {"name": "🔮 МДМА", "price": 3600, "desc": "Кристаллы, танцевальный"},
        {"name": "🔥 Альфа-PVP", "price": 3600, "desc": "Кристаллы, мощный стимулятор"},
    ],
    "Уфа": [
        {"name": "🍃 Трава", "price": 1350, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2800, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2300, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 2000, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3400, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2500, "desc": "Таблетки, проверено"},
    ],
    "Красноярск": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "🔥 Альфа-PVP", "price": 3400, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "🔮 МДМА", "price": 3500, "desc": "Кристаллы, танцевальный"},
        {"name": "❄️ Кокаин", "price": 4900, "desc": "Чистый продукт, быстрая доставка"},
    ],
    "Архангельск": [
        {"name": "🍃 Трава", "price": 1400, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 3000, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2500, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 2000, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3500, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2500, "desc": "Таблетки, проверено"},
    ],
    "Владивосток": [
        {"name": "🍃 Трава", "price": 1500, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 3100, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2600, "desc": "Лирика 300мг, оригинал"},
        {"name": "❄️ Кокаин", "price": 5200, "desc": "Чистый продукт, быстрая доставка"},
        {"name": "🔮 МДМА", "price": 3700, "desc": "Кристаллы, танцевальный"},
        {"name": "🌵 2C-B", "price": 4200, "desc": "Дизайнерский трип"},
    ],
    "Воронеж": [
        {"name": "🍃 Трава", "price": 1350, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2800, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2300, "desc": "Лирика 300мг, оригинал"},
        {"name": "🌀 Кетамин", "price": 3400, "desc": "Чистый кетамин, визуалы"},
        {"name": "💎 Амфетамин", "price": 1900, "desc": "Скорость, качественный продукт"},
        {"name": "🍬 Экстази", "price": 2400, "desc": "Таблетки, проверено"},
    ],
    "Сочи": [
        {"name": "🍃 Трава", "price": 1600, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 3200, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2700, "desc": "Лирика 300мг, оригинал"},
        {"name": "❄️ Кокаин", "price": 5500, "desc": "Чистый продукт, быстрая доставка"},
        {"name": "🔮 МДМА", "price": 3800, "desc": "Кристаллы, танцевальный"},
        {"name": "🔥 Альфа-PVP", "price": 3700, "desc": "Кристаллы, мощный стимулятор"},
    ],
    "Тула": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 1800, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3200, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2300, "desc": "Таблетки, проверено"},
    ],
    "Хабаровск": [
        {"name": "🍃 Трава", "price": 1450, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 3000, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2500, "desc": "Лирика 300мг, оригинал"},
        {"name": "🔥 Альфа-PVP", "price": 3600, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "🔮 МДМА", "price": 3600, "desc": "Кристаллы, танцевальный"},
        {"name": "❄️ Кокаин", "price": 5100, "desc": "Чистый продукт, быстрая доставка"},
    ],
    "Ярославль": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 1800, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3200, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2300, "desc": "Таблетки, проверено"},
    ],
    "Барнаул": [
        {"name": "🍃 Трава", "price": 1200, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2500, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2000, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 1700, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3000, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2200, "desc": "Таблетки, проверено"},
    ],
    "Волгоград": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "🔥 Альфа-PVP", "price": 3400, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "🔮 МДМА", "price": 3400, "desc": "Кристаллы, танцевальный"},
        {"name": "❄️ Кокаин", "price": 4800, "desc": "Чистый продукт, быстрая доставка"},
    ],
    "Киров": [
        {"name": "🍃 Трава", "price": 1250, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2600, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2100, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 1800, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3100, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2300, "desc": "Таблетки, проверено"},
    ],
    "Магнитогорск": [
        {"name": "🍃 Трава", "price": 1250, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2600, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2100, "desc": "Лирика 300мг, оригинал"},
        {"name": "🔥 Альфа-PVP", "price": 3300, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "🔮 МДМА", "price": 3300, "desc": "Кристаллы, танцевальный"},
        {"name": "💎 Амфетамин", "price": 1800, "desc": "Скорость, качественный продукт"},
    ],
    "Набережные Челны": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "🌀 Кетамин", "price": 3300, "desc": "Чистый кетамин, визуалы"},
        {"name": "💎 Амфетамин", "price": 1900, "desc": "Скорость, качественный продукт"},
        {"name": "🍬 Экстази", "price": 2400, "desc": "Таблетки, проверено"},
    ],
    "Саратов": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "🔥 Альфа-PVP", "price": 3400, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "🔮 МДМА", "price": 3400, "desc": "Кристаллы, танцевальный"},
        {"name": "❄️ Кокаин", "price": 4900, "desc": "Чистый продукт, быстрая доставка"},
    ],
    "Тверь": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "💎 Амфетамин", "price": 1800, "desc": "Скорость, качественный продукт"},
        {"name": "🌀 Кетамин", "price": 3200, "desc": "Чистый кетамин, визуалы"},
        {"name": "🍬 Экстази", "price": 2300, "desc": "Таблетки, проверено"},
    ],
    "Пермь": [
        {"name": "🍃 Трава", "price": 1300, "desc": "Качественная трава, приятный эффект"},
        {"name": "⚡️ Мефедрон", "price": 2700, "desc": "Кристаллы, высокая чистота"},
        {"name": "💊 Лирика (300мг)", "price": 2200, "desc": "Лирика 300мг, оригинал"},
        {"name": "🔥 Альфа-PVP", "price": 3400, "desc": "Кристаллы, мощный стимулятор"},
        {"name": "🔮 МДМА", "price": 3400, "desc": "Кристаллы, танцевальный"},
        {"name": "❄️ Кокаин", "price": 4900, "desc": "Чистый продукт, быстрая доставка"},
    ],
}

# ============ РАНГИ ============
def get_rank(amount):
    if amount >= 100000:
        return "👑 Платиновый"
    elif amount >= 50000:
        return "💎 Золотой"
    elif amount >= 20000:
        return "🥈 Серебряный"
    elif amount >= 5000:
        return "🥉 Бронзовый"
    else:
        return "🌱 Новичок"

# ============ ГЛАВНОЕ МЕНЮ ============
def main_menu():
    markup = types.ReplyKeyboardMarkup(True, False)
    markup.row("🛍 Магазин", "👤 Профиль")
    markup.row("💰 Пополнить баланс", "ℹ️ Информация")
    markup.row("📦 Мои покупки", "🚕 Доставка")
    markup.row("💼 Работа")
    return markup

# ============ МЕНЮ РАБОТЫ ============
def work_menu():
    markup = types.ReplyKeyboardMarkup(True, False)
    markup.row("🏃‍♂️ Курьер-раскладчик", "🖼 Трафаретчик")
    markup.row("🚛 Водитель")
    markup.row("◀️ Назад в главное меню")
    return markup

# ============ ТОВАРЫ ПО ГОРОДУ ============
def show_goods_by_city(chat_id, city):
    try:
        goods = CITY_GOODS.get(city, [])
        if not goods:
            bot.send_message(chat_id, "❌ Товаров в вашем городе пока нет")
            return
        
        text = f"🌿 Товары в {city}:\n\n"
        kb = types.InlineKeyboardMarkup(row_width=2)
        
        for i, good in enumerate(goods):
            text += f"{good['name']} | {good['price']}₽\n"
            kb.add(types.InlineKeyboardButton(f"🛒 {good['name']} - {good['price']}₽", callback_data=f"buy_{city}_{i}"))
        
        bot.send_message(chat_id, text, reply_markup=kb)
        logger.info(f"Показано {len(goods)} товаров для города {city}")
    except Exception as e:
        logger.error(f"Ошибка в show_goods_by_city: {e}")
        bot.send_message(chat_id, "❌ Ошибка загрузки товаров")

# ============ КОМАНДА /START ============
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    logger.info(f"Пользователь {user_id} запустил бота")
    
    try:
        conn, cur = get_cursor()
        cur.execute(f"SELECT count(*) FROM users WHERE id = {user_id}")
        if cur.fetchone()[0] == 0:
            name = f"{message.chat.first_name} | {message.chat.last_name}"
            user_name = message.chat.username
            cur.execute(f"INSERT INTO users (id, name, username, balance, city, total_spent) VALUES ({user_id}, \"{name}\", \"{user_name}\", 0, '', 0)")
            conn.commit()
            logger.info(f"Создан новый пользователь {user_id}")
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя {user_id}: {e}")
    
    welcome_text = (
        "⚡️ Добро пожаловать в магазин @NrczTrstBot! ⚡️\n\n"
        "▪️ Хотите быстро получить нужный товар? Мы поможем!\n"
        "▪️ Работаем 24/7.\n"
        "▪️ Внимательно проверяйте юзернейм оператора. МЫ НИКОГДА НЕ ПИШЕМ ПЕРВЫЕ!\n"
        "▪️ Если вашего города нет в каталоге, свяжитесь с оператором - мы поможем с предзаказом или доставкой.\n\n"
        "👇 Выберите свой город:"
    )
    
    cities = types.InlineKeyboardMarkup(row_width=2)
    city_list = list(CITY_GOODS.keys())
    for city in city_list:
        cities.add(types.InlineKeyboardButton(city, callback_data=f"city_{city}"))
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=cities)

@bot.callback_query_handler(func=lambda call: call.data.startswith("city_"))
def set_city(call):
    city = call.data.split("_")[1]
    logger.info(f"Пользователь {call.message.chat.id} выбрал город {city}")
    try:
        conn, cur = get_cursor()
        cur.execute(f"UPDATE users SET city = '{city}' WHERE id = {call.message.chat.id}")
        conn.commit()
        conn.close()
        bot.edit_message_text(f"✅ Город {city} выбран!", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Добро пожаловать в магазин!", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Ошибка при выборе города: {e}")

# ============ АДМИН ПАНЕЛЬ ============
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != admin:
        logger.warning(f"Пользователь {message.chat.id} попытался зайти в админку")
        bot.send_message(message.chat.id, "❌ Доступ запрещён")
        return
    
    logger.info(f"Админ {message.chat.id} зашёл в админ-панель")
    adm = types.InlineKeyboardMarkup(row_width=2)
    adm.add(types.InlineKeyboardButton("📦 Управление товарами", callback_data="manage_goods"))
    adm.add(types.InlineKeyboardButton("💳 Изменить карту", callback_data="cardcard"))
    adm.add(types.InlineKeyboardButton("📊 Статистика", callback_data="stat"))
    adm.add(types.InlineKeyboardButton("📨 Рассылка", callback_data="send"))
    adm.add(types.InlineKeyboardButton("💰 Проверить платежи", callback_data="check_payments"))
    adm.add(types.InlineKeyboardButton("❌ Закрыть", callback_data="esc"))
    bot.send_message(message.chat.id, "⚙️ Админ панель", reply_markup=adm)

# ============ ОСНОВНОЕ МЕНЮ ============
@bot.message_handler(content_types=['text'])
def main_message(message):
    if message.text == "🛍 Магазин":
        conn, cur = get_cursor()
        cur.execute(f"SELECT city FROM users WHERE id = {message.chat.id}")
        result = cur.fetchone()
        conn.close()
        if result and result[0]:
            show_goods_by_city(message.chat.id, result[0])
        else:
            bot.send_message(message.chat.id, "❌ Сначала выберите город через /start")
    
    elif message.text == "👤 Профиль":
        try:
            conn, cur = get_cursor()
            cur.execute("SELECT name, balance, city, total_spent FROM users WHERE id = ?", (message.chat.id,))
            user = cur.fetchone()
            conn.close()
            if user:
                name, balance, city, spent = user
                rank = get_rank(spent)
                text = f"👤 Профиль\n\n"
                text += f"▪️ Имя: {name.split('|')[0]}\n"
                text += f"▪️ Город: {city if city else 'Не выбран'}\n"
                text += f"💰 Баланс: {balance}₽\n"
                text += f"🏆 Ранг: {rank}\n"
                text += f"💸 Всего потрачено: {spent}₽"
                bot.send_message(message.chat.id, text, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Ошибка профиля: {e}")
    
    elif message.text == "💰 Пополнить баланс":
        try:
            conn, cur = get_cursor()
            cur.execute("SELECT num FROM card")
            card_num = cur.fetchone()[0]
            conn.close()
            text = f"💳 Пополнение баланса\n\n"
            text += f"📌 Реквизиты для оплаты:\n"
            text += f"{card_num}\n\n"
            text += f"❗️ Инструкция:\n"
            text += f"1. Переведите нужную сумму на карту\n"
            text += f"2. Нажмите кнопку «✅ Я оплатил»\n"
            text += f"3. Отправьте чек (скриншот перевода)\n"
            text += f"4. Ожидайте пополнения баланса администратором"
            
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("✅ Я оплатил", callback_data="send_receipt_payment"))
            bot.send_message(message.chat.id, text, reply_markup=kb)
        except Exception as e:
            logger.error(f"Ошибка пополнения баланса: {e}")
    
    elif message.text == "ℹ️ Информация":
        text = "ℹ️ ИНФОРМАЦИЯ ℹ️\n\n"
        text += "▪️ Мы заботимся о безопасности! Наши сотрудники проходят строгий отбор и обучение, чтобы обеспечить вам максимальную защиту.\n\n"
        text += "▪️ Надежные клады: Мы используем проверенные методы для размещения кладов, и риск их обнаружения сводится к минимуму (кроме форс-мажорных ситуаций, таких как перекопка земли).\n\n"
        text += "▪️ Качественная продукция: Каждый товар проходит двойную проверку - наши тестеры проверяют его перед покупкой, а затем еще раз после получения. Вы можете быть уверены в высочайшем качестве!\n\n"
        text += "▪️ Контроль качества: Работа каждого сотрудника находится под контролем.\n\n"
        text += "▪️ Удобное расположение: Клады в городе размещаются на магнитах, как правило, рядом с метро или крупными остановками общественного транспорта. В парках или малонаселенных районах клады закапываются.\n\n"
        text += "▪️ Быстрое исполнение: Персональные, комбинированные и оптовые заказы обрабатываются в течение 24 часов после оплаты.\n\n"
        text += "💬 Помощь/Доставка: @HizenSupport_bot"
        bot.send_message(message.chat.id, text, reply_markup=main_menu())
    
    elif message.text == "📦 Мои покупки":
        try:
            conn, cur = get_cursor()
            cur.execute("SELECT o.id, g.name, o.quantity, o.total_price, o.status, o.timestamp FROM orders o LEFT JOIN goods g ON o.good_id = g.id WHERE o.buyer_id = ? ORDER BY o.id DESC LIMIT 20", (message.chat.id,))
            orders = cur.fetchall()
            conn.close()
            if not orders:
                bot.send_message(message.chat.id, "📭 У вас пока нет покупок", reply_markup=main_menu())
                return
            text = "📦 Мои покупки:\n\n"
            for order in orders:
                status_emoji = "✅" if order[4] == "paid" else "⏳"
                text += f"{status_emoji} {order[1]}\n"
                text += f"   📦 Кол-во: {order[2]}\n"
                text += f"   💰 Сумма: {order[3]}₽\n"
                text += f"   📅 Дата: {order[5][:16]}\n\n"
            bot.send_message(message.chat.id, text, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Ошибка моих покупок: {e}")
    
    elif message.text == "🚕 Доставка":
        text = "🚕 Доставка 🚕\n\n"
        text += "▪️ Закажите доставку любого товара из нашего каталога!\n"
        text += "▪️ Полная анонимность и бесконтактность:\n"
        text += "Укажите адрес, и курьер оставит клад в радиусе 300 метров.\n"
        text += "После этого он пришлёт координаты с подробными фотографиями.\n\n"
        text += "💸 Стоимость доставки:\n"
        text += "⏳ Обычная: 2000 ₽ (доставка от 4 до 12 часов)\n"
        text += "⚡️ Ускоренная: 2800 ₽ (доставка от 1 до 2 часов)\n\n"
        text += "🎁 Бесплатная доставка:\n"
        text += "При заказе от 10 000 ₽ доставка за наш счет!\n\n"
        text += "⚠️ В исключительных случаях может потребоваться залог.\n\n"
        text += "💬 За доставкой - @HizenSupport_bot"
        bot.send_message(message.chat.id, text, reply_markup=main_menu())
    
    elif message.text == "💼 Работа":
        bot.send_message(message.chat.id, "💼 Выберите направление:", reply_markup=work_menu())
    
    elif message.text == "🏃‍♂️ Курьер-раскладчик":
        text = "🏃‍♂️ Курьер-раскладчик 🏃‍♂️\n\n"
        text += "Ваша задача:\n"
        text += "- Раскладывать заказы по назначенным адресам.\n\n"
        text += "💰 Выгоды для вас:\n"
        text += "▪️ Оплата за каждый выполненный адрес, не нужно ждать продажи!\n"
        text += "▪️ Оплата за день в день.\n"
        text += "▪️ Еженедельные премии и бонусы.\n"
        text += "▪️ Ежемесячные конкурсы с ценными призами.\n"
        text += "▪️ Доступ к обширной библиотеке обучающих материалов.\n"
        text += "▪️ Обучение от опытных сотрудников с многолетним стажем.\n"
        text += "▪️ Чат для курьеров - делитесь опытом и общайтесь!\n\n"
        text += "🚀 Заинтересованы?\n"
        text += "▪️ Для начала работы требуется залог в размере 5.000 ₽.\n"
        text += "▪️ Напишите ваш город оператору @HizenSupport_bot, чтобы начать трудоустройство!"
        bot.send_message(message.chat.id, text, reply_markup=work_menu())
    
    elif message.text == "🖼 Трафаретчик":
        text = "🖼 Трафаретчик 🖼\n\n"
        text += "Наносить трафаретные рисунки/наклейки на популярные места в вашем городе.\n"
        text += "Фотографировать свои работы через приложение NoteCam.\n\n"
        text += "💰 Выгоды:\n"
        text += "▪️ Заработок от 110 ₽ за граффити.\n"
        text += "▪️ Заработок от 50 ₽ за стикер.\n"
        text += "▪️ Выплата от 20 граффити / 50 стикеров.\n"
        text += "▪️ Мы предоставим вам текст для граффити.\n"
        text += "▪️ Компенсация затрат на краску при получении первой зарплаты (сохраняйте чек).\n\n"
        text += "🚀 Готовы к творчеству?\n"
        text += "Напишите свой город оператору @HizenSupport_bot, чтобы получить подробную информацию и приобрести краску!"
        bot.send_message(message.chat.id, text, reply_markup=work_menu())
    
    elif message.text == "🚛 Водитель":
        text = "🚛 Водитель 🚛\n\n"
        text += "Основная задача - транспортировка товаров (нелегальных химических веществ) между городами.\n\n"
        text += "График работы ненормированный, маршруты могут быть разной длины. Заработная плата составляет от 70.000 ₽ за рейс, работа связана с перемещением крупных грузов.\n\n"
        text += "▪️ Все расходы (топливо, аренда жилья при необходимости) оплачиваются отдельно.\n"
        text += "▪️ Выплата происходит после доставки и проверки товара, также возмещаются все расходы из заработной платы.\n"
        text += "▪️ Заработная плата выплачивается на биткоин-кошелек; в случае незнания работы с ним, предоставляется инструкция.\n"
        text += "▪️ После трудоустройства куратор проведёт полный инструктаж по обязанностям и технике безопасности. Вам будет предоставлен один оплачиваемый стажировочный рейс для практической работы.\n\n"
        text += "Трудоустройство возможно только при внесении залога от 60.000 ₽. Для начала процесса устройства, свяжитесь с оператором и укажите свой город.\n\n"
        text += "💬 За работой - @HizenSupport_bot"
        bot.send_message(message.chat.id, text, reply_markup=work_menu())
    
    elif message.text == "◀️ Назад в главное меню":
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_menu())
    
    elif message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())
    
    else:
        bot.send_message(message.chat.id, "❌ Неизвестная команда. Используйте кнопки меню.", reply_markup=main_menu())

# ============ ВРЕМЕННЫЕ ДАННЫЕ ============
temp_cart = {}
admin_temp_data = {}

# ============ КОЛБЭКИ ============
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    logger.info(f"Колбэк: {call.data} от пользователя {call.message.chat.id}")
    
    if call.data == "add_good":
        try:
            logger.info(f"Админ {call.message.chat.id} начал добавление товара")
            admin_temp_data[call.message.chat.id] = {}
            admin_temp_data[call.message.chat.id]['step'] = 'name'
            bot.send_message(call.message.chat.id, "📝 Введите название товара:")
            bot.register_next_step_handler(call.message, add_good_name)
            bot.answer_callback_query(call.id)
            return
        except Exception as e:
            logger.error(f"Ошибка в add_good: {e}")
            return
    
    elif call.data == "cancel_buy":
        try:
            if call.message.chat.id in temp_cart:
                del temp_cart[call.message.chat.id]
            bot.edit_message_text("❌ Покупка отменена", call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=main_menu())
            bot.answer_callback_query(call.id)
            return
        except Exception as e:
            logger.error(f"Ошибка в cancel_buy: {e}")
            return
    
    elif call.data == "send_receipt_payment":
        try:
            bot.send_message(call.message.chat.id, "📸 Отправьте скриншот/чек об оплате\n\nПосле проверки администратор пополнит ваш баланс.")
            bot.register_next_step_handler(call.message, receive_receipt_payment)
            bot.answer_callback_query(call.id)
            return
        except Exception as e:
            logger.error(f"Ошибка в send_receipt_payment: {e}")
            return
    
    elif call.data == "manage_goods":
        try:
            logger.info(f"Админ {call.message.chat.id} открыл управление товарами")
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("➕ Добавить товар", callback_data="add_good"))
            kb.add(types.InlineKeyboardButton("📋 Список товаров", callback_data="list_goods"))
            kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_admin"))
            bot.edit_message_text("📦 Управление товарами", call.message.chat.id, call.message.message_id, reply_markup=kb)
            bot.answer_callback_query(call.id)
            return
        except Exception as e:
            logger.error(f"Ошибка в manage_goods: {e}")
            return
    
    elif call.data == "list_goods":
        try:
            conn, cur = get_cursor()
            cur.execute("SELECT id, name, price, status FROM goods")
            goods = cur.fetchall()
            conn.close()
            if not goods:
                bot.send_message(call.message.chat.id, "📭 Нет товаров")
                bot.answer_callback_query(call.id)
                return
            text = "📋 Список товаров:\n\n"
            for g in goods:
                status = "✅" if g[3] == 1 else "❌"
                text += f"{status} ID:{g[0]} | {g[1]} | {g[2]}₽\n"
            bot.send_message(call.message.chat.id, text)
            bot.answer_callback_query(call.id)
            return
        except Exception as e:
            logger.error(f"Ошибка в list_goods: {e}")
            return
    
    elif call.data == "cardcard":
        bot.send_message(call.message.chat.id, "💳 Введите новый номер карты для приёма платежей:")
        bot.register_next_step_handler(call.message, replacecard)
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "stat":
        try:
            conn, cur = get_cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            users_count = cur.fetchone()[0]
            cur.execute("SELECT SUM(total_price) FROM orders WHERE status = 'paid'")
            total_profit = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'")
            orders_count = cur.fetchone()[0]
            conn.close()
            bot.send_message(call.message.chat.id, f"📊 Статистика:\n\n👥 Пользователей: {users_count}\n🛒 Заказов: {orders_count}\n💰 Общий доход: {total_profit}₽")
            bot.answer_callback_query(call.id)
            return
        except Exception as e:
            logger.error(f"Ошибка в stat: {e}")
            return
    
    elif call.data == "send":
        bot.send_message(call.message.chat.id, "📨 Введите текст рассылки:")
        bot.register_next_step_handler(call.message, rass)
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "check_payments":
        try:
            conn, cur = get_cursor()
            cur.execute("SELECT id, user_id, amount, timestamp FROM pending_payments WHERE status = 'pending' ORDER BY timestamp DESC")
            payments = cur.fetchall()
            conn.close()
            if not payments:
                bot.send_message(call.message.chat.id, "📭 Нет ожидающих платежей")
                bot.answer_callback_query(call.id)
                return
            for p in payments:
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("✅ Выдать баланс", callback_data=f"give_balance_{p[1]}_{p[2]}"))
                kb.add(types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_payment_{p[1]}"))
                bot.send_message(call.message.chat.id, f"💰 Платёж от пользователя ID: {p[1]}\nСумма: {p[2]}₽\nДата: {p[3]}", reply_markup=kb)
            bot.answer_callback_query(call.id)
            return
        except Exception as e:
            logger.error(f"Ошибка в check_payments: {e}")
            return
    
    elif call.data == "back_to_admin":
        adm = types.InlineKeyboardMarkup(row_width=2)
        adm.add(types.InlineKeyboardButton("📦 Управление товарами", callback_data="manage_goods"))
        adm.add(types.InlineKeyboardButton("💳 Изменить карту", callback_data="cardcard"))
        adm.add(types.InlineKeyboardButton("📊 Статистика", callback_data="stat"))
        adm.add(types.InlineKeyboardButton("📨 Рассылка", callback_data="send"))
        adm.add(types.InlineKeyboardButton("💰 Проверить платежи", callback_data="check_payments"))
        adm.add(types.InlineKeyboardButton("❌ Закрыть", callback_data="esc"))
        bot.edit_message_text("⚙️ Админ панель", call.message.chat.id, call.message.message_id, reply_markup=adm)
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "esc":
        bot.edit_message_text("Админ панель закрыта", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return
    
    elif call.data.startswith("buy_"):
        try:
            parts = call.data.split("_")
            if len(parts) < 3:
                logger.error(f"Неверный формат buy_: {call.data}")
                bot.answer_callback_query(call.id, "Ошибка формата")
                return
            
            city = parts[1]
            good_index = int(parts[2])
            
            goods = CITY_GOODS.get(city, [])
            if good_index >= len(goods):
                bot.answer_callback_query(call.id, "Товар не найден")
                return
            
            good = goods[good_index]
            name = good['name']
            price = good['price']
            desc = good['desc']
            
            logger.info(f"Пользователь {call.message.chat.id} выбрал товар {name} в городе {city}")
            
            text = f"🌿 {name}\n💰 Цена: {price}₽\n📦 {desc}\n\nВыберите количество:"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("➕ 1", callback_data=f"add_1_{city}_{good_index}"))
            kb.add(types.InlineKeyboardButton("➕ 5", callback_data=f"add_5_{city}_{good_index}"))
            kb.add(types.InlineKeyboardButton("➕ 10", callback_data=f"add_10_{city}_{good_index}"))
            kb.add(types.InlineKeyboardButton("✅ Готово", callback_data=f"ready_{city}_{good_index}"))
            kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_buy"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Ошибка в buy_: {e}")
    
    elif call.data.startswith("add_"):
        try:
            parts = call.data.split("_")
            if len(parts) != 4:
                logger.error(f"Неверный формат add_: {call.data}")
                bot.answer_callback_query(call.id, "Ошибка формата")
                return
            
            qty = int(parts[1])
            city = parts[2]
            good_index = int(parts[3])
            
            if call.message.chat.id not in temp_cart:
                temp_cart[call.message.chat.id] = {'city': city, 'good_index': good_index, 'qty': 0}
            temp_cart[call.message.chat.id]['qty'] += qty
            temp_cart[call.message.chat.id]['city'] = city
            temp_cart[call.message.chat.id]['good_index'] = good_index
            
            bot.answer_callback_query(call.id, f"✅ Добавлено {qty} шт. Всего: {temp_cart[call.message.chat.id]['qty']}")
        except Exception as e:
            logger.error(f"Ошибка в add_: {e}")
    
    elif call.data.startswith("ready_"):
        try:
            parts = call.data.split("_")
            if len(parts) != 3:
                logger.error(f"Неверный формат ready_: {call.data}")
                bot.answer_callback_query(call.id, "Ошибка формата")
                return
            
            city = parts[1]
            good_index = int(parts[2])
            
            cart = temp_cart.get(call.message.chat.id, {})
            qty = cart.get('qty', 0)
            
            if qty == 0:
                bot.answer_callback_query(call.id, "❌ Выберите количество")
                return
            
            goods = CITY_GOODS.get(city, [])
            if good_index >= len(goods):
                bot.answer_callback_query(call.id, "Товар не найден")
                return
            
            good = goods[good_index]
            name = good['name']
            price = good['price']
            total = price * qty
            
            conn, cur = get_cursor()
            cur.execute(f"SELECT balance FROM users WHERE id = {call.message.chat.id}")
            balance = cur.fetchone()[0]
            conn.close()
            
            if balance >= total:
                conn2, cur2 = get_cursor()
                cur2.execute(f"UPDATE users SET balance = {balance - total}, total_spent = total_spent + {total} WHERE id = {call.message.chat.id}")
                conn2.commit()
                conn2.close()
                
                conn3, cur3 = get_cursor()
                cur3.execute("INSERT INTO goods (city, name, price, description, status) VALUES (?, ?, ?, ?, 1)", 
                             (city, name, price, good['desc']))
                conn3.commit()
                good_id = cur3.lastrowid
                conn3.close()
                
                conn4, cur4 = get_cursor()
                cur4.execute("INSERT INTO orders (buyer_id, good_id, quantity, total_price, status) VALUES (?, ?, ?, ?, 'paid')", 
                             (call.message.chat.id, good_id, qty, total))
                conn4.commit()
                conn4.close()
                
                bot.edit_message_text(f"✅ Заказ оформлен!\n\n🌿 Товар: {name}\n📦 Количество: {qty}\n💰 Сумма: {total}₽\n\nОжидайте, с вами свяжутся.", call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=main_menu())
                bot.answer_callback_query(call.id)
            else:
                need = total - balance
                bot.edit_message_text(f"❌ Недостаточно средств!\n\n🌿 Товар: {name}\n📦 Количество: {qty}\n💰 Сумма: {total}₽\n💳 Ваш баланс: {balance}₽\n\nНе хватает: {need}₽\nПополните баланс через кнопку «💰 Пополнить баланс»", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)
            
            if call.message.chat.id in temp_cart:
                del temp_cart[call.message.chat.id]
        except Exception as e:
            logger.error(f"Ошибка в ready_: {e}")
    
    elif call.data.startswith("give_balance_"):
        try:
            parts = call.data.split("_")
            if len(parts) < 4:
                logger.error(f"Неверный формат give_balance_: {call.data}")
                bot.answer_callback_query(call.id, "Ошибка формата")
                return
            user_id = int(parts[2])
            amount = int(parts[3])
            conn, cur = get_cursor()
            cur.execute(f"UPDATE users SET balance = balance + {amount} WHERE id = {user_id}")
            conn.commit()
            cur.execute(f"UPDATE pending_payments SET status = 'approved' WHERE user_id = {user_id} AND amount = {amount}")
            conn.commit()
            conn.close()
            bot.send_message(user_id, f"✅ Ваш баланс пополнен на {amount}₽!", reply_markup=main_menu())
            bot.answer_callback_query(call.id, "Баланс выдан")
        except Exception as e:
            logger.error(f"Ошибка в give_balance_: {e}")
    
    elif call.data.startswith("reject_payment_"):
        try:
            user_id = int(call.data.split("_")[2])
            conn, cur = get_cursor()
            cur.execute(f"UPDATE pending_payments SET status = 'rejected' WHERE user_id = {user_id}")
            conn.commit()
            conn.close()
            bot.send_message(user_id, "❌ Ваш платёж отклонён. Проверьте правильность перевода и отправьте чек заново.")
            bot.answer_callback_query(call.id, "Платёж отклонён")
        except Exception as e:
            logger.error(f"Ошибка в reject_payment_: {e}")
    
    elif call.data.startswith("enter_amount_"):
        try:
            parts = call.data.split("_")
            if len(parts) < 4:
                logger.error(f"Неверный формат enter_amount_: {call.data}")
                bot.answer_callback_query(call.id, "Ошибка формата")
                return
            pending_id = int(parts[2])
            user_id = int(parts[3])
            
            admin_temp_data[call.message.chat.id] = {'pending_id': pending_id, 'user_id': user_id}
            bot.send_message(call.message.chat.id, "💰 Введите сумму пополнения для этого пользователя:")
            bot.register_next_step_handler(call.message, set_payment_amount)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Ошибка в enter_amount_: {e}")
    
    elif call.data.startswith("confirm_payment_"):
        try:
            parts = call.data.split("_")
            user_id = int(parts[2])
            amount = int(parts[3])
            
            conn, cur = get_cursor()
            cur.execute(f"UPDATE users SET balance = balance + {amount} WHERE id = {user_id}")
            conn.commit()
            cur.execute(f"UPDATE pending_payments SET status = 'approved' WHERE user_id = {user_id} AND amount = {amount}")
            conn.commit()
            conn.close()
            
            bot.send_message(user_id, f"✅ Ваш баланс пополнен на {amount}₽!", reply_markup=main_menu())
            bot.edit_message_text(f"✅ Баланс пользователя {user_id} пополнен на {amount}₽", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Баланс выдан")
        except Exception as e:
            logger.error(f"Ошибка в confirm_payment_: {e}")

# ============ ПРИЁМ ЧЕКА НА ПОПОЛНЕНИЕ ============
def receive_receipt_payment(message):
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())
        return
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ Отправьте фото чека!")
        bot.register_next_step_handler(message, receive_receipt_payment)
        return
    
    if not os.path.exists('receipts'):
        os.makedirs('receipts')
    
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    receipt_path = f'receipts/{message.chat.id}_{int(time.time())}.jpg'
    with open(receipt_path, 'wb') as f:
        f.write(downloaded_file)
    
    conn, cur = get_cursor()
    cur.execute("INSERT INTO pending_payments (user_id, amount) VALUES (?, ?)", (message.chat.id, 0))
    conn.commit()
    conn.close()
    
    admin_kb = types.InlineKeyboardMarkup()
    admin_kb.add(types.InlineKeyboardButton("💰 Ввести сумму", callback_data=f"enter_amount_{message.chat.id}_{message.chat.id}"))
    
    bot.send_photo(admin, open(receipt_path, 'rb'), caption=f"📨 Новый чек от пользователя {message.chat.id}\n👤 {message.chat.first_name}", reply_markup=admin_kb)
    bot.send_message(message.chat.id, "✅ Чек отправлен на проверку. Ожидайте пополнения баланса.", reply_markup=main_menu())

def set_payment_amount(message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "❌ Введите число!")
        bot.register_next_step_handler(message, set_payment_amount)
        return
    
    amount = int(message.text)
    user_id = admin_temp_data[message.chat.id]['user_id']
    
    conn, cur = get_cursor()
    cur.execute(f"UPDATE pending_payments SET amount = {amount} WHERE user_id = {user_id}")
    conn.commit()
    conn.close()
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_payment_{user_id}_{amount}"))
    kb.add(types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_payment_{user_id}"))
    bot.send_message(message.chat.id, f"💰 Сумма: {amount}₽\nПодтвердите действие:", reply_markup=kb)

# ============ ДОБАВЛЕНИЕ ТОВАРА (АДМИН) ============
def add_good_name(message):
    logger.info(f"add_good_name: получил сообщение '{message.text}' от {message.chat.id}")
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())
        return
    admin_temp_data[message.chat.id]['name'] = message.text
    admin_temp_data[message.chat.id]['step'] = 'price'
    bot.send_message(message.chat.id, "💰 Введите цену за единицу (только число):")
    bot.register_next_step_handler(message, add_good_price)

def add_good_price(message):
    logger.info(f"add_good_price: получил сообщение '{message.text}' от {message.chat.id}")
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())
        return
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "❌ Введите число!")
        bot.register_next_step_handler(message, add_good_price)
        return
    admin_temp_data[message.chat.id]['price'] = int(message.text)
    admin_temp_data[message.chat.id]['step'] = 'desc'
    bot.send_message(message.chat.id, "📝 Введите описание товара:")
    bot.register_next_step_handler(message, add_good_desc)

def add_good_desc(message):
    logger.info(f"add_good_desc: получил сообщение '{message.text}' от {message.chat.id}")
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())
        return
    data = admin_temp_data[message.chat.id]
    
    try:
        conn, cur = get_cursor()
        cur.execute("INSERT INTO goods (city, name, price, description, status) VALUES (?, ?, ?, ?, 1)",
                    ('', data['name'], data['price'], message.text))
        conn.commit()
        conn.close()
        logger.info(f"Товар '{data['name']}' успешно добавлен админом {message.chat.id}")
        
        del admin_temp_data[message.chat.id]
        
        bot.send_message(message.chat.id, f"✅ Товар «{data['name']}» добавлен в каталог!")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        bot.send_message(message.chat.id, f"❌ Ошибка при добавлении товара: {e}")

# ============ ЗАМЕНА КАРТЫ ============
def replacecard(message):
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())
        return
    if message.text.isdigit():
        conn, cur = get_cursor()
        cur.execute("UPDATE card SET num = ?", (int(message.text),))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Номер карты обновлён", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "❌ Введите число")
        bot.register_next_step_handler(message, replacecard)

# ============ РАССЫЛКА ============
def rass(message):
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())
        return
    conn, cur = get_cursor()
    cur.execute("SELECT id FROM users")
    users = cur.fetchall()
    conn.close()
    ok = 0
    for u in users:
        try:
            bot.send_message(u[0], message.text)
            ok += 1
            time.sleep(0.05)
        except:
            pass
    bot.send_message(message.chat.id, f"📨 Рассылка завершена. Отправлено {ok} пользователям", reply_markup=main_menu())

# ============ ЗАПУСК ============
if __name__ == '__main__':
    conn, cur = get_cursor()
    cur.execute("SELECT count(*) FROM goods WHERE city != ''")
    if cur.fetchone()[0] == 0:
        for city, goods in CITY_GOODS.items():
            for good in goods:
                cur.execute("INSERT INTO goods (city, name, price, description, status) VALUES (?, ?, ?, ?, 1)",
                            (city, good['name'], good['price'], good['desc']))
        conn.commit()
        logger.info("Добавлены товары для всех городов")
    conn.close()
    
    logger.info("Бот запущен!")
    logger.info(f"Админ панель: /admin")
    logger.info(f"ID админа: {admin}")
    print("🤖 Бот запущен! Логи пишутся в bot.log")
    print("👨‍💼 Админ панель: /admin")
    print("🆔 ID админа:", admin)
    bot.polling(none_stop=True)
import os
from dotenv import dotenv_values

env_values = dotenv_values('.env')

# Данные бота @AldanLiverisBot (захардкожены по просьбе пользователя)
BOT_TOKEN = os.getenv("BOT_TOKEN") or env_values.get(
    "BOT_TOKEN", "") or "сюда токен бота"
NOTIFICATION_CHANNEL_ID = int(
    os.getenv("NOTIFICATION_CHANNEL_ID")
    or env_values.get("NOTIFICATION_CHANNEL_ID", "") or "-сюда ID  группы для уведомлений")
SUPER_ADMIN_IDS = [
    int(id_str.strip())
    for id_str in (os.getenv("SUPER_ADMIN_IDS") or env_values.get(
        "SUPER_ADMIN_IDS", "") or "сюда ID админа").split(",") if id_str.strip()
]

DATABASE_NAME = "shop_q.db"

PAYMENT_METHODS = {
    'bitcoin': {
        'enabled': True,
        'wallet': '',
        'name': 'Bitcoin (BTC)'
    },
    'ethereum': {
        'enabled': True,
        'wallet': '',
        'name': 'Ethereum (ETH)'
    },
    'card': {
        'enabled': True,
        'name': 'Карта курьеру'
    },
    'cash': {
        'enabled': True,
        'name': 'Наличные'
    }
}

REFERRAL_BONUS_INVITER = 100
REFERRAL_BONUS_INVITED = 50

ANTI_FLOOD_LIMIT = 5
ANTI_FLOOD_TIMEOUT = 60

DELIVERY_TIME_MINUTES = 60

WELCOME_MESSAGE = """Торжественное открытие! 🎉

Теперь в одном сервисе:
🥗 Продукты питания • 🍔 Фастфуд • 💄 Косметика • 🛠 Инструменты • 💊 Аптечные товары • 👗 Одежда

Доставляем всё — от хлеба до гардероба! Не нашли нужный товар? Позвоните нам, и мы найдём всё, что вам необходимо.

Ваш город становится ближе!
📞 8-914-101-71-89

🛍️ Выберите свою роль для начала работы:"""

WELCOME_IMAGE = "attached_assets/9c720c54-09f6-419e-84a9-c30a281b9e8d_1763431398593.jpg"

MIN_RATING = 1.1
MAX_RATING = 5.5

DEFAULT_LANGUAGE = 'ru'

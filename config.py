import os
from dotenv import dotenv_values

env_values = dotenv_values('.env')

admin_ids_str = os.getenv("SUPER_ADMIN_IDS") or env_values.get("SUPER_ADMIN_IDS", "сюда ID админа")
if admin_ids_str and admin_ids_str.strip():
    SUPER_ADMIN_IDS = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
else:
    SUPER_ADMIN_IDS = []

notification_channel = os.getenv("NOTIFICATION_CHANNEL_ID") or env_values.get("NOTIFICATION_CHANNEL_ID", "сюда ID админа группы для уведомлений")
NOTIFICATION_CHANNEL_ID = int(notification_channel) if notification_channel and notification_channel.strip() and notification_channel != "0" else 0

BOT_TOKEN = os.getenv("BOT_TOKEN") or env_values.get("BOT_TOKEN", "сюда токен бота")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Укажите его в переменных окружения.")



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

WELCOME_MESSAGE = """🎉 *ДОБРО ПОЖАЛОВАТЬ В SHOP-Q!*

Здесь вы можете покупать и продавать виртуальные товары с доставкой в вашем регионе.

🛍️ Выберите свою роль для начала работы:"""

MIN_RATING = 1.1
MAX_RATING = 5.5

DEFAULT_LANGUAGE = 'ru'

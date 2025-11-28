import random
import string
from datetime import datetime
import config
from telegram.helpers import escape_markdown

def generate_referral_code(user_id: int) -> str:
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"REF{user_id}_{random_part}"

def generate_order_number() -> str:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"SQ-{timestamp}-{random_part}"

def check_admin(user_id: int) -> bool:
    return user_id in config.SUPER_ADMIN_IDS

def check_manager(user_role: str) -> bool:
    return user_role == 'manager'

def format_price(price: float) -> str:
    return f"{price:.2f} руб"

def format_rating(rating: float) -> str:
    if rating is None:
        return "Нет оценок"
    stars = int(rating)
    return "⭐" * stars + f" {rating:.1f}"

def safe_name(name: str) -> str:
    """Безопасно экранирует имя для использования в Markdown"""
    if not name:
        return escape_markdown('Пользователь')
    return escape_markdown(name)

def safe_username(username: str) -> str:
    """Безопасно экранирует username для использования в Markdown"""
    if not username:
        return escape_markdown('не указан')
    return escape_markdown(username)

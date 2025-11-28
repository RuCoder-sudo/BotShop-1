from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import config
from database import Database
from utils import generate_referral_code, check_admin
import logging
import os

logger = logging.getLogger(__name__)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    user = update.message.from_user
    referral_code = generate_referral_code(user.id)
    
    db_user = db.get_user(user.id)
    
    if not db_user:
        db.add_user(user.id, user.username or '', user.first_name or '', referral_code)
        db_user = db.get_user(user.id)
    
    if check_admin(user.id):
        db.update_user_role(user.id, 'admin')
        await show_admin_menu(update, context)
    elif db_user['role'] == 'pending':
        await show_role_selection(update, context)
    elif db_user['role'] == 'manager':
        await show_manager_menu(update, context)
    elif db_user['role'] == 'buyer':
        await show_buyer_menu(update, context)
    else:
        await show_role_selection(update, context)

async def show_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Я покупатель", callback_data="role_buyer")],
        [InlineKeyboardButton("💼 Я продавец", callback_data="role_seller")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if os.path.exists(config.WELCOME_IMAGE):
        try:
            with open(config.WELCOME_IMAGE, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=config.WELCOME_MESSAGE,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending welcome image: {e}")
            await update.message.reply_text(
                config.WELCOME_MESSAGE,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            config.WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_role_selection_callback(query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Я покупатель", callback_data="role_buyer")],
        [InlineKeyboardButton("💼 Я продавец", callback_data="role_seller")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if os.path.exists(config.WELCOME_IMAGE):
        try:
            with open(config.WELCOME_IMAGE, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=config.WELCOME_MESSAGE,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending welcome image: {e}")
            await query.message.reply_text(
                config.WELCOME_MESSAGE,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    else:
        await query.message.reply_text(
            config.WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, bot):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    role = query.data.split('_')[1]
    
    if role == 'buyer':
        db.update_user_role(user.id, 'buyer')
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Вы зарегистрированы как покупатель!"
        )
        await show_buyer_menu_callback(query, context)
    
    elif role == 'seller':
        existing_request = db.conn.cursor()
        existing_request.execute(
            'SELECT * FROM verification_requests WHERE user_id = ? AND status = "pending"',
            (user.id,)
        )
        if existing_request.fetchone():
            keyboard = [
                [InlineKeyboardButton("◀️ Назад к выбору роли", callback_data="back_to_role_selection")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="⏳ Ваша заявка на верификацию уже отправлена и ожидает рассмотрения.",
                reply_markup=reply_markup
            )
            return
        
        db.create_verification_request(user.id)
        
        first_name_esc = escape_markdown(user.first_name or 'Пользователь')
        username_esc = escape_markdown(user.username or 'не указан')
        
        notification_text = (
            f"📢 *НОВАЯ ЗАЯВКА НА ВЕРИФИКАЦИЮ*\n\n"
            f"👤 Пользователь: {first_name_esc}\n"
            f"🆔 ID: `{user.id}`\n"
            f"👥 Username: @{username_esc}\n\n"
            f"Заявка ожидает вашего решения в панели администратора."
        )
        
        # Отправляем уведомление в канал
        if config.NOTIFICATION_CHANNEL_ID:
            try:
                await bot.send_message(
                    chat_id=config.NOTIFICATION_CHANNEL_ID,
                    text=notification_text,
                    parse_mode='Markdown'
                )
                logger.info(f"✅ Уведомление о верификации отправлено в канал {config.NOTIFICATION_CHANNEL_ID}")
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке в канал: {e}")
        
        # Отправляем уведомление всем администраторам (независимо от результата отправки в канал)
        if config.SUPER_ADMIN_IDS:
            for admin_id in config.SUPER_ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=notification_text,
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ Уведомление о верификации отправлено админу {admin_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке админу {admin_id}: {e}")
        
        keyboard = [
            [InlineKeyboardButton("◀️ Назад к выбору роли", callback_data="back_to_role_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Ваша заявка на верификацию отправлена администратору!\n"
            "⏳ Ожидайте подтверждения.",
            reply_markup=reply_markup
        )

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["👥 Пользователи", "🛠️ Инструменты"],
        ["🌍 Локации", "📁 Категории"],
        ["📦 Товары", "➕ Создать товар"],
        ["📣 Рассылка", "✅ Верификация"],
        ["📚 Каталог", "📊 Статистика"],
        ["🚚 Доставка", "👤 Профиль"],
        ["⚙️ Настройки"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔐 *ПАНЕЛЬ АДМИНИСТРАТОРА*\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["➕ Создать товар", "📦 Мои товары"],
        ["🧾 Продажи", "📊 Статистика"],
        ["📚 Каталог", "👤 Профиль"],
        ["🚚 Доставка", "💬 Поддержка"],
        ["🌍 Локации и категории", "ℹ️ Информация"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "💼 *ПАНЕЛЬ ПРОДАВЦА*\n\nУправляйте своими товарами:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_back_to_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db.update_user_role(user_id, 'pending')
    
    await show_role_selection_callback(query, context)

async def show_buyer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📚 Каталог"],
        ["🏪 Магазины", "🔍 Поиск"],
        ["📦 Мои заказы", "🛒 Корзина"],
        ["⭐ Избранное", "👤 Профиль"],
        ["📞 Контакты", "❓ FAQ"],
        ["💬 Поддержка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🛍️ *ГЛАВНОЕ МЕНЮ*\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_buyer_menu_callback(query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📚 Каталог"],
        ["🏪 Магазины", "🔍 Поиск"],
        ["📦 Мои заказы", "🛒 Корзина"],
        ["⭐ Избранное", "👤 Профиль"],
        ["📞 Контакты", "❓ FAQ"],
        ["💬 Поддержка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🛍️ *ГЛАВНОЕ МЕНЮ*\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

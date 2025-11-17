from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import Database
from utils import generate_referral_code, check_admin

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
        await query.edit_message_text("✅ Вы зарегистрированы как покупатель!")
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
            await query.edit_message_text(
                "⏳ Ваша заявка на верификацию уже отправлена и ожидает рассмотрения.",
                reply_markup=reply_markup
            )
            return
        
        db.create_verification_request(user.id)
        
        notification_text = (
            f"📢 *НОВАЯ ЗАЯВКА НА ВЕРИФИКАЦИЮ*\n\n"
            f"👤 Пользователь: {user.first_name}\n"
            f"🆔 ID: `{user.id}`\n"
            f"👥 Username: @{user.username or 'не указан'}\n\n"
            f"Заявка ожидает вашего решения в панели администратора."
        )
        
        try:
            await bot.send_message(
                chat_id=config.NOTIFICATION_CHANNEL_ID,
                text=notification_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            for admin_id in config.SUPER_ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=notification_text,
                        parse_mode='Markdown'
                    )
                except:
                    pass
        
        keyboard = [
            [InlineKeyboardButton("◀️ Назад к выбору роли", callback_data="back_to_role_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✅ Ваша заявка на верификацию отправлена администратору!\n"
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
        ["👤 Профиль", "⚙️ Настройки"]
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
        ["🌍 Локации и категории", "💬 Поддержка"],
        ["ℹ️ Информация"]
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
        ["🏪 Магазины", "🔍 Поиск"],
        ["📚 Каталог", "🛒 Корзина"],
        ["📦 Мои заказы", "👤 Профиль"],
        ["⭐ Избранное", "💬 Поддержка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🛍️ *ГЛАВНОЕ МЕНЮ*\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_buyer_menu_callback(query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏪 Магазины", "🔍 Поиск"],
        ["📚 Каталог", "🛒 Корзина"],
        ["📦 Мои заказы", "👤 Профиль"],
        ["⭐ Избранное", "💬 Поддержка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await query.message.reply_text(
        "🛍️ *ГЛАВНОЕ МЕНЮ*\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

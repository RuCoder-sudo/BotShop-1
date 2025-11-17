from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database import Database
from utils import check_admin
import config
from datetime import datetime
import logging
import sqlite3

logger = logging.getLogger(__name__)

class AdminStates:
    ADD_COUNTRY = 1
    SELECT_COUNTRY_CITY = 2
    ADD_CITY = 3
    SELECT_CITY_DISTRICT = 4
    ADD_DISTRICT = 5
    ADD_CATEGORY = 6
    ADD_SUBCATEGORY = 7
    BROADCAST_MESSAGE = 8
    CHANGE_BALANCE = 9
    SEND_MESSAGE_TO_USER = 10
    EDIT_COUNTRY = 11
    EDIT_CITY = 12
    EDIT_DISTRICT = 13
    EDIT_CATEGORY = 14
    BALANCE_USER_ID = 15
    BALANCE_ACTION = 16
    BALANCE_AMOUNT = 17
    BLOCK_USER_ID = 18
    SEND_MESSAGE_USER_ID = 19
    SEND_MESSAGE_TEXT = 20
    SELECT_PARENT_CATEGORY = 21
    ADD_SUBCATEGORY_NAME = 22
    PROMOTE_USER_ID = 23
    EDIT_CATEGORY_NAME = 24
    ADMIN_PRODUCT_NAME = 25
    ADMIN_PRODUCT_DESC = 26
    ADMIN_PRODUCT_PRICE = 27
    ADMIN_PRODUCT_STOCK = 28
    ADMIN_PRODUCT_CATEGORY = 29
    ADMIN_PRODUCT_COUNTRY = 30
    ADMIN_PRODUCT_CITY = 31
    ADMIN_PRODUCT_DISTRICT = 32
    ADMIN_PRODUCT_IMAGE = 33
    ADMIN_PRODUCT_SELLER = 34
    BROADCAST_PHOTO = 35

def setup_admin_handlers(application):
    
    country_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_add_country_start, pattern="^add_country$")],
        states={
            AdminStates.ADD_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_country_name)]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        per_message=False
    )
    
    city_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_select_country_for_city, pattern="^select_country_city$")],
        states={
            AdminStates.SELECT_COUNTRY_CITY: [CallbackQueryHandler(handle_city_country_selected, pattern="^add_city_")],
            AdminStates.ADD_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_city_name)]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        per_message=False
    )
    
    district_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_select_city_for_district, pattern="^select_country_district$")],
        states={
            AdminStates.SELECT_CITY_DISTRICT: [CallbackQueryHandler(handle_district_city_selected, pattern="^add_district_")],
            AdminStates.ADD_DISTRICT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_district_name)]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        per_message=False
    )
    
    category_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_add_category_start, pattern="^add_category$")],
        states={
            AdminStates.ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_category_name)]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        per_message=False
    )
    
    subcategory_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_add_subcategory_start, pattern="^add_subcategory$")],
        states={
            AdminStates.SELECT_PARENT_CATEGORY: [CallbackQueryHandler(handle_subcategory_parent_selected, pattern="^select_parent_cat_")],
            AdminStates.ADD_SUBCATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_subcategory_name)]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        per_message=False
    )
    
    broadcast_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📣 Рассылка$"), handle_broadcast_start)],
        states={
            AdminStates.BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_text)],
            AdminStates.BROADCAST_PHOTO: [
                MessageHandler(filters.PHOTO, handle_broadcast_send),
                MessageHandler(filters.Regex("^Пропустить$"), handle_broadcast_send)
            ]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        per_message=False
    )
    
    balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_manage_balance_start, pattern="^manage_balance$")],
        states={
            AdminStates.BALANCE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_balance_user_id)],
            AdminStates.BALANCE_ACTION: [CallbackQueryHandler(handle_balance_action, pattern="^(balance_credit|balance_debit|balance_history_|cancel_balance).*")],
            AdminStates.BALANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_balance_amount)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_balance)],
        per_message=False
    )
    
    block_user_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_block_user_start, pattern="^block_user_start$")],
        states={
            AdminStates.BLOCK_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block_user_id)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel)],
        per_message=False
    )
    
    send_message_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_send_message_start, pattern="^send_message_start$")],
        states={
            AdminStates.SEND_MESSAGE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_send_message_user_id)],
            AdminStates.SEND_MESSAGE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_send_message_text)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_send_message)],
        per_message=False
    )
    
    promote_seller_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_promote_seller_start, pattern="^promote_seller$")],
        states={
            AdminStates.PROMOTE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_promote_seller_user_id)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel)],
        per_message=False
    )
    
    edit_category_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_edit_category_start, pattern="^edit_cat_")],
        states={
            AdminStates.EDIT_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_category_name)]
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        per_message=False
    )
    
    admin_product_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_admin_add_product_start, pattern="^admin_add_product$")],
        states={
            AdminStates.ADMIN_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_product_name)],
            AdminStates.ADMIN_PRODUCT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_product_description)],
            AdminStates.ADMIN_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_product_price)],
            AdminStates.ADMIN_PRODUCT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_product_stock)],
            AdminStates.ADMIN_PRODUCT_CATEGORY: [CallbackQueryHandler(handle_admin_select_category, pattern="^admin_cat_")],
            AdminStates.ADMIN_PRODUCT_COUNTRY: [CallbackQueryHandler(handle_admin_select_country, pattern="^admin_country_")],
            AdminStates.ADMIN_PRODUCT_CITY: [CallbackQueryHandler(handle_admin_select_city, pattern="^admin_city_")],
            AdminStates.ADMIN_PRODUCT_DISTRICT: [CallbackQueryHandler(handle_admin_select_district, pattern="^admin_district_")],
            AdminStates.ADMIN_PRODUCT_SELLER: [CallbackQueryHandler(handle_admin_select_seller, pattern="^admin_seller_")],
            AdminStates.ADMIN_PRODUCT_IMAGE: [
                MessageHandler(filters.PHOTO, handle_admin_product_image),
                MessageHandler(filters.Regex("^Пропустить$"), handle_admin_product_image)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel)],
        per_message=False
    )
    
    application.add_handler(MessageHandler(filters.Regex("^👥 Пользователи$"), handle_users_menu))
    application.add_handler(MessageHandler(filters.Regex("^✅ Верификация$"), handle_verification_menu))
    application.add_handler(MessageHandler(filters.Regex("^🌍 Локации$"), handle_locations_menu))
    application.add_handler(MessageHandler(filters.Regex("^📁 Категории$"), handle_categories_menu))
    application.add_handler(MessageHandler(filters.Regex("^📦 Товары$"), handle_products_menu))
    application.add_handler(MessageHandler(filters.Regex("^📊 Статистика$"), handle_statistics))
    application.add_handler(MessageHandler(filters.Regex("^🛠️ Инструменты$"), handle_tools_menu))
    application.add_handler(MessageHandler(filters.Regex("^⚙️ Настройки$"), handle_settings_menu))
    application.add_handler(MessageHandler(filters.Regex("^📋 Правила$"), handle_admin_rules))
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), handle_admin_contacts))
    application.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), handle_admin_faq))
    
    
    application.add_handler(CallbackQueryHandler(handle_approve_verification, pattern="^approve_ver_"))
    application.add_handler(CallbackQueryHandler(handle_reject_verification, pattern="^reject_ver_"))
    application.add_handler(CallbackQueryHandler(handle_edit_countries, pattern="^edit_countries$"))
    application.add_handler(CallbackQueryHandler(handle_edit_cities, pattern="^edit_cities$"))
    application.add_handler(CallbackQueryHandler(handle_edit_districts, pattern="^edit_districts$"))
    application.add_handler(CallbackQueryHandler(handle_edit_categories_list, pattern="^edit_categories$"))
    application.add_handler(CallbackQueryHandler(handle_delete_country, pattern="^del_country_"))
    application.add_handler(CallbackQueryHandler(handle_delete_city, pattern="^del_city_"))
    application.add_handler(CallbackQueryHandler(handle_delete_district, pattern="^del_district_"))
    application.add_handler(CallbackQueryHandler(handle_delete_category, pattern="^del_cat_"))
    
    application.add_handler(CallbackQueryHandler(handle_complaints_menu, pattern="^complaints$"))
    application.add_handler(CallbackQueryHandler(handle_view_complaints, pattern="^view_(pending|resolved)_complaints$"))
    application.add_handler(CallbackQueryHandler(handle_complaint_detail, pattern="^complaint_detail_"))
    application.add_handler(CallbackQueryHandler(handle_resolve_complaint, pattern="^resolve_complaint_"))
    
    application.add_handler(CallbackQueryHandler(handle_block_user_menu, pattern="^block_user_menu$"))
    application.add_handler(CallbackQueryHandler(handle_view_blocked_users, pattern="^view_blocked_users$"))
    application.add_handler(CallbackQueryHandler(handle_unblock_user_start, pattern="^unblock_user_start$"))
    application.add_handler(CallbackQueryHandler(handle_unblock_user, pattern="^unblock_user_"))
    
    application.add_handler(CallbackQueryHandler(handle_view_all_products, pattern="^admin_view_.*_products$"))
    application.add_handler(CallbackQueryHandler(handle_admin_product_detail, pattern="^admin_product_"))
    application.add_handler(CallbackQueryHandler(handle_moderate_product, pattern="^moderate_product_"))
    application.add_handler(CallbackQueryHandler(handle_delete_product_admin, pattern="^admin_delete_product_"))
    application.add_handler(CallbackQueryHandler(handle_confirm_delete_product_admin, pattern="^admin_confirm_delete_"))
    
    application.add_handler(CallbackQueryHandler(handle_list_all_users, pattern="^list_all_users$"))
    application.add_handler(CallbackQueryHandler(handle_list_buyers, pattern="^list_buyers$"))
    application.add_handler(CallbackQueryHandler(handle_list_managers, pattern="^list_managers$"))
    application.add_handler(CallbackQueryHandler(handle_promo_codes_menu, pattern="^promo_codes$"))
    
    application.add_handler(country_conv)
    application.add_handler(city_conv)
    application.add_handler(district_conv)
    application.add_handler(category_conv)
    application.add_handler(subcategory_conv)
    application.add_handler(broadcast_conv)
    application.add_handler(balance_conv)
    application.add_handler(block_user_conv)
    application.add_handler(send_message_conv)
    application.add_handler(promote_seller_conv)
    application.add_handler(edit_category_conv)
    application.add_handler(admin_product_conv)

async def handle_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    users = db.get_all_users()
    blocked_users = db.get_blocked_users()
    
    text = "👥 *УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ*\n\n"
    text += f"Всего пользователей: {len(users)}\n"
    text += f"🚫 Заблокированных: {len(blocked_users)}\n\n"
    
    buyers = [u for u in users if u['role'] == 'buyer']
    managers = [u for u in users if u['role'] == 'manager']
    pending = [u for u in users if u['role'] == 'pending']
    
    text += f"🛍️ Покупателей: {len(buyers)}\n"
    text += f"💼 Продавцов: {len(managers)}\n"
    text += f"⏳ Ожидают выбора роли: {len(pending)}\n"
    
    keyboard = [
        [InlineKeyboardButton("📋 Список всех пользователей", callback_data="list_all_users")],
        [InlineKeyboardButton("🛍️ Покупатели", callback_data="list_buyers"),
         InlineKeyboardButton("💼 Продавцы", callback_data="list_managers")],
        [InlineKeyboardButton("💰 Управление балансом", callback_data="manage_balance"),
         InlineKeyboardButton("💬 Отправить сообщение", callback_data="send_message_start")],
        [InlineKeyboardButton("⬆️ Повысить до продавца", callback_data="promote_seller")],
        [InlineKeyboardButton("🚫 Блокировка пользователей", callback_data="block_user_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_verification_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    requests = db.get_pending_verifications()
    
    if not requests:
        await update.message.reply_text("✅ Нет заявок на верификацию")
        return
    
    text = "✅ *ЗАЯВКИ НА ВЕРИФИКАЦИЮ*\n\n"
    keyboard = []
    
    for req in requests:
        text += f"👤 {req['first_name']} (@{req['username'] or 'нет'})\n"
        text += f"🆔 ID: `{req['user_id']}`\n"
        text += f"📅 Дата: {req['requested_at'][:10]}\n"
        text += "─────────────\n"
        
        keyboard.append([
            InlineKeyboardButton(f"✅ Одобрить {req['first_name']}", callback_data=f"approve_ver_{req['id']}"),
            InlineKeyboardButton(f"❌ Отклонить", callback_data=f"reject_ver_{req['id']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_approve_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    request_id = int(query.data.split('_')[-1])
    
    user_id = db.approve_verification(request_id, query.from_user.id)
    
    if user_id:
        keyboard = [
            ["➕ Создать товар", "📦 Мои товары"],
            ["🧾 Продажи", "📊 Статистика"],
            ["🌍 Локации и категории", "👤 Профиль"],
            ["ℹ️ Информация", "💬 Поддержка"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 *ПОЗДРАВЛЯЕМ!*\n\n"
                     "Ваша заявка одобрена! Теперь вы можете добавлять товары.\n\n"
                     "💼 *ПАНЕЛЬ ПРОДАВЦА*\n"
                     "Используйте меню ниже для управления товарами:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send menu to approved seller {user_id}: {e}")
        
        await query.edit_message_text("✅ Верификация одобрена!")
    else:
        await query.edit_message_text("❌ Ошибка при обработке заявки")

async def handle_reject_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    request_id = int(query.data.split('_')[-1])
    
    db.reject_verification(request_id, query.from_user.id)
    await query.edit_message_text("❌ Заявка отклонена")

async def handle_locations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    countries = db.get_countries()
    
    text = "🌍 *УПРАВЛЕНИЕ ЛОКАЦИЯМИ*\n\n"
    
    if countries:
        text += "Доступные страны:\n"
        for country in countries:
            cities = db.get_cities(country['id'])
            text += f"🌍 {country['name']} ({len(cities)} городов)\n"
    else:
        text += "Стран пока нет\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить страну", callback_data="add_country")],
        [InlineKeyboardButton("➕ Добавить город", callback_data="select_country_city")],
        [InlineKeyboardButton("➕ Добавить район", callback_data="select_country_district")],
        [InlineKeyboardButton("✏️ Редактировать страны", callback_data="edit_countries")],
        [InlineKeyboardButton("✏️ Редактировать города", callback_data="edit_cities")],
        [InlineKeyboardButton("✏️ Редактировать районы", callback_data="edit_districts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_add_country_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    await query.edit_message_text("🌍 Введите название страны:")
    return AdminStates.ADD_COUNTRY

async def handle_add_country_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    country_name = update.message.text.strip()
    
    if len(country_name) > 100:
        await update.message.reply_text("❌ Название слишком длинное (максимум 100 символов)")
        return ConversationHandler.END
    
    try:
        db.add_country(country_name, update.message.from_user.id)
        await update.message.reply_text(f"✅ Страна '{country_name}' добавлена!")
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            await update.message.reply_text(f"❌ Страна '{country_name}' уже существует!")
        elif "FOREIGN KEY constraint failed" in str(e):
            await update.message.reply_text(f"❌ Ошибка связи в базе данных. Проверьте корректность данных.")
        else:
            await update.message.reply_text(f"❌ Ошибка базы данных: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding country: {e}")
        await update.message.reply_text(f"❌ Ошибка при добавлении страны. Попробуйте использовать простое название без специальных символов.")
    
    return ConversationHandler.END

async def handle_select_country_for_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data['db']
    countries = db.get_countries()
    
    if not countries:
        await query.edit_message_text("❌ Сначала добавьте страну")
        return ConversationHandler.END
    
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(country['name'], callback_data=f"add_city_{country['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите страну:", reply_markup=reply_markup)
    
    return AdminStates.SELECT_COUNTRY_CITY

async def handle_city_country_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    country_id = int(query.data.split('_')[-1])
    context.user_data['selected_country_id'] = country_id
    
    await query.edit_message_text("🏙️ Введите название города:")
    return AdminStates.ADD_CITY

async def handle_add_city_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    city_name = update.message.text.strip()
    country_id = context.user_data.get('selected_country_id')
    
    if not country_id:
        await update.message.reply_text("❌ Ошибка: страна не выбрана")
        return ConversationHandler.END
    
    try:
        db.add_city(country_id, city_name, update.message.from_user.id)
        await update.message.reply_text(f"✅ Город '{city_name}' добавлен!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END

async def handle_select_city_for_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data['db']
    countries = db.get_countries()
    
    if not countries:
        await query.edit_message_text("❌ Сначала добавьте страну и город")
        return ConversationHandler.END
    
    keyboard = []
    for country in countries:
        cities = db.get_cities(country['id'])
        for city in cities:
            keyboard.append([InlineKeyboardButton(
                f"{country['name']} - {city['name']}", 
                callback_data=f"add_district_{city['id']}"
            )])
    
    if not keyboard:
        await query.edit_message_text("❌ Сначала добавьте города")
        return ConversationHandler.END
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите город:", reply_markup=reply_markup)
    
    return AdminStates.SELECT_CITY_DISTRICT

async def handle_district_city_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    city_id = int(query.data.split('_')[-1])
    context.user_data['selected_city_id'] = city_id
    
    await query.edit_message_text("🏘️ Введите название района:")
    return AdminStates.ADD_DISTRICT

async def handle_add_district_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    district_name = update.message.text.strip()
    city_id = context.user_data.get('selected_city_id')
    
    if not city_id:
        await update.message.reply_text("❌ Ошибка: город не выбран")
        return ConversationHandler.END
    
    try:
        db.add_district(city_id, district_name, update.message.from_user.id)
        await update.message.reply_text(f"✅ Район '{district_name}' добавлен!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END

async def handle_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    categories = db.get_categories()
    
    text = "📁 *УПРАВЛЕНИЕ КАТЕГОРИЯМИ*\n\n"
    
    if categories:
        text += "Доступные категории (3 уровня):\n\n"
        for cat in categories:
            subcats = db.get_categories(cat['id'])
            text += f"📁 {cat['name']}\n"
            for subcat in subcats:
                subsubcats = db.get_categories(subcat['id'])
                text += f"  └ 📂 {subcat['name']}\n"
                for subsubcat in subsubcats:
                    text += f"    └ 📄 {subsubcat['name']}\n"
            text += "\n"
    else:
        text += "Категорий пока нет\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить категорию", callback_data="add_category")],
        [InlineKeyboardButton("➕ Добавить подкатегорию", callback_data="add_subcategory")],
        [InlineKeyboardButton("✏️ Редактировать/Удалить категории", callback_data="edit_categories")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    await query.edit_message_text("📁 Введите название категории:")
    return AdminStates.ADD_CATEGORY

async def handle_add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    category_name = update.message.text.strip()
    
    try:
        db.add_category(category_name, None, update.message.from_user.id)
        await update.message.reply_text(f"✅ Категория '{category_name}' добавлена!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END

async def handle_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    stats = db.get_statistics()
    
    text = f"""📊 *СТАТИСТИКА БОТА*

👥 Всего пользователей: {stats['total_users']}
📦 Всего заказов: {stats['total_orders']}
💰 Общая выручка: {stats['total_revenue']:.2f} руб
🛍️ Активных товаров: {stats['total_products']}
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📣 *СОЗДАНИЕ РАССЫЛКИ*\n\n"
        "Шаг 1/2: Введите текст сообщения для рассылки:",
        parse_mode='Markdown'
    )
    return AdminStates.BROADCAST_MESSAGE

async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_text'] = update.message.text
    
    await update.message.reply_text(
        "📸 Шаг 2/2: Отправьте фото для рассылки или напишите 'Пропустить'\n\n"
        "Фото будет отправлено вместе с текстом сообщения."
    )
    return AdminStates.BROADCAST_PHOTO

async def handle_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    message_text = context.user_data.get('broadcast_text', '')
    photo = None
    
    if update.message.photo:
        photo = update.message.photo[-1].file_id
    
    users = db.get_all_users()
    success = 0
    failed = 0
    
    await update.message.reply_text("📤 Начинаю рассылку...")
    
    for user in users:
        try:
            if photo:
                await context.bot.send_photo(
                    chat_id=user['user_id'],
                    photo=photo,
                    caption=f"📢 *Сообщение от администрации:*\n\n{message_text}",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 *Сообщение от администрации:*\n\n{message_text}",
                    parse_mode='Markdown'
                )
            success += 1
        except:
            failed += 1
    
    await update.message.reply_text(
        f"✅ Рассылка завершена!\n\n"
        f"Успешно: {success}\n"
        f"Ошибок: {failed}"
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено")
    return ConversationHandler.END

async def handle_tools_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    text = """🛠️ *ИНСТРУМЕНТЫ АДМИНИСТРАТОРА*

Доступные инструменты для управления ботом:

• Управление промо-кодами
• Система жалоб
• Управление балансом

Выберите нужный инструмент из меню ниже."""
    
    keyboard = [
        [InlineKeyboardButton("🎫 Промо-коды", callback_data="promo_codes")],
        [InlineKeyboardButton("⚠️ Жалобы", callback_data="complaints")],
        [InlineKeyboardButton("💰 Управление балансом", callback_data="manage_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    text = f"""⚙️ *НАСТРОЙКИ БОТА*

Текущие настройки системы:

💰 **Реферальная программа:**
• Бонус приглашающему: {config.REFERRAL_BONUS_INVITER} руб
• Бонус приглашенному: {config.REFERRAL_BONUS_INVITED} руб

💳 **Платежные системы:**
• Bitcoin: {'✅' if config.PAYMENT_METHODS['bitcoin']['enabled'] else '❌'}
• Ethereum: {'✅' if config.PAYMENT_METHODS['ethereum']['enabled'] else '❌'}
• Карта курьеру: {'✅' if config.PAYMENT_METHODS['card']['enabled'] else '❌'}
• Наличные: {'✅' if config.PAYMENT_METHODS['cash']['enabled'] else '❌'}

🛡️ **Анти-флуд:**
• Лимит запросов: {config.ANTI_FLOOD_LIMIT}
• Таймаут: {config.ANTI_FLOOD_TIMEOUT} сек

📊 **Рейтинговая система:**
• Минимальный рейтинг: {config.MIN_RATING}
• Максимальный рейтинг: {config.MAX_RATING}

Для изменения настроек отредактируйте файл config.py"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_edit_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    countries = db.get_countries()
    
    if not countries:
        await query.edit_message_text("❌ Нет стран для редактирования")
        return
    
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ Удалить: {country['name']}", 
            callback_data=f"del_country_{country['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_locations")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Выберите страну для удаления:",
        reply_markup=reply_markup
    )

async def handle_edit_cities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    countries = db.get_countries()
    
    if not countries:
        await query.edit_message_text("❌ Нет стран")
        return
    
    keyboard = []
    for country in countries:
        cities = db.get_cities(country['id'])
        for city in cities:
            keyboard.append([InlineKeyboardButton(
                f"🗑️ {country['name']} - {city['name']}", 
                callback_data=f"del_city_{city['id']}"
            )])
    
    if not keyboard:
        await query.edit_message_text("❌ Нет городов для удаления")
        return
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_locations")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Выберите город для удаления:",
        reply_markup=reply_markup
    )

async def handle_edit_districts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    countries = db.get_countries()
    
    keyboard = []
    for country in countries:
        cities = db.get_cities(country['id'])
        for city in cities:
            districts = db.get_districts(city['id'])
            for district in districts:
                keyboard.append([InlineKeyboardButton(
                    f"🗑️ {country['name']} / {city['name']} / {district['name']}", 
                    callback_data=f"del_district_{district['id']}"
                )])
    
    if not keyboard:
        await query.edit_message_text("❌ Нет районов для удаления")
        return
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_locations")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Выберите район для удаления:",
        reply_markup=reply_markup
    )

async def handle_edit_categories_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    categories = db.get_categories()
    
    if not categories:
        await query.edit_message_text("❌ Нет категорий для редактирования")
        return
    
    keyboard = []
    for cat in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ Редактировать: {cat['name']}", 
                callback_data=f"edit_cat_{cat['id']}"
            ),
            InlineKeyboardButton(
                f"🗑️ Удалить: {cat['name']}", 
                callback_data=f"del_cat_{cat['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Выберите категорию для редактирования или удаления:",
        reply_markup=reply_markup
    )

async def handle_delete_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    country_id = int(query.data.split('_')[-1])
    
    country = db.get_country(country_id)
    if country:
        db.delete_country(country_id)
        await query.edit_message_text(f"✅ Страна '{country['name']}' удалена!")
    else:
        await query.edit_message_text("❌ Страна не найдена")

async def handle_delete_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    city_id = int(query.data.split('_')[-1])
    
    city = db.get_city(city_id)
    if city:
        db.delete_city(city_id)
        await query.edit_message_text(f"✅ Город '{city['name']}' удален!")
    else:
        await query.edit_message_text("❌ Город не найден")

async def handle_delete_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    district_id = int(query.data.split('_')[-1])
    
    district = db.get_district(district_id)
    if district:
        db.delete_district(district_id)
        await query.edit_message_text(f"✅ Район '{district['name']}' удален!")
    else:
        await query.edit_message_text("❌ Район не найден")

async def handle_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    category_id = int(query.data.split('_')[-1])
    
    category = db.get_category(category_id)
    if category:
        db.delete_category(category_id)
        await query.edit_message_text(f"✅ Категория '{category['name']}' удалена!")
    else:
        await query.edit_message_text("❌ Категория не найдена")

async def handle_edit_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    category_id = int(query.data.split('_')[-1])
    context.user_data['edit_category_id'] = category_id
    
    db = context.bot_data['db']
    category = db.get_category(category_id)
    
    if not category:
        await query.edit_message_text("❌ Категория не найдена")
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"📁 Текущее название категории: *{category['name']}*\n\n"
        f"Введите новое название категории:",
        parse_mode='Markdown'
    )
    return AdminStates.EDIT_CATEGORY_NAME

async def handle_edit_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    new_name = update.message.text.strip()
    category_id = context.user_data.get('edit_category_id')
    
    if not category_id:
        await update.message.reply_text("❌ Ошибка: категория не выбрана")
        return ConversationHandler.END
    
    try:
        db.update_category(category_id, new_name)
        await update.message.reply_text(f"✅ Категория успешно переименована в '{new_name}'!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении: {str(e)}")
    
    return ConversationHandler.END

async def handle_complaints_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    pending_complaints = db.get_complaints('pending')
    resolved_complaints = db.get_complaints('resolved')
    
    keyboard = [
        [InlineKeyboardButton(f"⚠️ Активные жалобы ({len(pending_complaints)})", callback_data="view_pending_complaints")],
        [InlineKeyboardButton(f"✅ Решенные жалобы ({len(resolved_complaints)})", callback_data="view_resolved_complaints")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""⚠️ *УПРАВЛЕНИЕ ЖАЛОБАМИ*

📊 Статистика:
• Активных: {len(pending_complaints)}
• Решенных: {len(resolved_complaints)}
• Всего: {len(pending_complaints) + len(resolved_complaints)}

Выберите категорию жалоб:"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_view_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    status = 'pending' if 'pending' in query.data else 'resolved'
    complaints = db.get_complaints(status)
    
    if not complaints:
        await query.edit_message_text(
            f"✅ Нет жалоб со статусом '{status}'\n\n"
            "Это хорошая новость!"
        )
        return
    
    keyboard = []
    for complaint in complaints[:20]:
        complainant = complaint['complainant_name'] or complaint['complainant_fname'] or f"ID{complaint['complainant_id']}"
        target = complaint['target_name'] or complaint['target_fname'] or f"ID{complaint['target_id']}"
        
        keyboard.append([InlineKeyboardButton(
            f"📋 {complainant} → {target}",
            callback_data=f"complaint_detail_{complaint['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="complaints")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"⚠️ *{'АКТИВНЫЕ' if status == 'pending' else 'РЕШЕННЫЕ'} ЖАЛОБЫ*\n\n"
    text += f"Всего жалоб: {len(complaints)}\n\n"
    text += "Выберите жалобу для просмотра деталей:"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_complaint_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    complaint_id = int(query.data.split('_')[-1])
    
    complaints = db.get_complaints()
    complaint = next((c for c in complaints if c['id'] == complaint_id), None)
    
    if not complaint:
        await query.edit_message_text("❌ Жалоба не найдена")
        return
    
    complainant = complaint['complainant_name'] or complaint['complainant_fname'] or f"ID{complaint['complainant_id']}"
    target = complaint['target_name'] or complaint['target_fname'] or f"ID{complaint['target_id']}"
    
    text = f"""⚠️ *ЖАЛОБА #{complaint['id']}*

👤 *Жалобщик:* {complainant}
🎯 *На кого:* {target}
📦 *Товар:* {complaint['product_name'] or 'не указан'}

📝 *Причина:*
{complaint['reason']}

📅 *Дата:* {complaint['created_at'][:10]}
🏷️ *Статус:* {complaint['status']}
"""
    
    if complaint['resolved_at']:
        text += f"✅ *Решено:* {complaint['resolved_at'][:10]}\n"
    
    keyboard = []
    if complaint['status'] == 'pending':
        keyboard.append([InlineKeyboardButton("✅ Решить жалобу", callback_data=f"resolve_complaint_{complaint_id}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"view_{complaint['status']}_complaints")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_resolve_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    complaint_id = int(query.data.split('_')[-1])
    
    db.resolve_complaint(complaint_id, query.from_user.id)
    
    await query.answer("✅ Жалоба решена!", show_alert=True)
    await query.edit_message_text(
        f"✅ *ЖАЛОБА #{complaint_id} РЕШЕНА*\n\n"
        f"Администратор: {query.from_user.first_name}\n"
        f"Дата решения: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        parse_mode='Markdown'
    )

async def handle_manage_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "💰 *УПРАВЛЕНИЕ БАЛАНСОМ ПОЛЬЗОВАТЕЛЯ*\n\n"
        "Введите ID пользователя:",
        parse_mode='Markdown'
    )
    return AdminStates.BALANCE_USER_ID

async def handle_balance_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. Введите число:")
        return AdminStates.BALANCE_USER_ID
    
    db = context.bot_data['db']
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден. Введите другой ID:")
        return AdminStates.BALANCE_USER_ID
    
    context.user_data['balance_target_user_id'] = user_id
    
    keyboard = [
        [InlineKeyboardButton("➕ Пополнить", callback_data="balance_credit")],
        [InlineKeyboardButton("➖ Списать", callback_data="balance_debit")],
        [InlineKeyboardButton("📜 История", callback_data=f"balance_history_{user_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👤 *ПОЛЬЗОВАТЕЛЬ*\n\n"
        f"ID: `{user['user_id']}`\n"
        f"Имя: {user['first_name']}\n"
        f"Username: @{user['username'] or 'не указан'}\n"
        f"💰 Текущий баланс: {user['balance']} руб\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return AdminStates.BALANCE_ACTION

async def handle_balance_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel_balance':
        await query.edit_message_text("❌ Операция отменена")
        context.user_data.clear()
        return ConversationHandler.END
    
    if query.data.startswith('balance_history_'):
        user_id = int(query.data.split('_')[-1])
        db = context.bot_data['db']
        transactions = db.get_user_transactions(user_id, 10)
        
        if not transactions:
            await query.edit_message_text("📜 История операций пуста")
            return ConversationHandler.END
        
        text = f"📜 *ИСТОРИЯ ОПЕРАЦИЙ*\n\n"
        for tx in transactions:
            text += f"{'➕' if tx['amount'] > 0 else '➖'} {abs(tx['amount'])} руб\n"
            text += f"   {tx['description']}\n"
            text += f"   {tx['created_at'][:16]}\n\n"
        
        await query.edit_message_text(text, parse_mode='Markdown')
        context.user_data.clear()
        return ConversationHandler.END
    
    action = query.data.split('_')[1]
    context.user_data['balance_action'] = action
    
    await query.edit_message_text(
        f"💰 *{'ПОПОЛНЕНИЕ' if action == 'credit' else 'СПИСАНИЕ'} БАЛАНСА*\n\n"
        f"Введите сумму (только положительное число):",
        parse_mode='Markdown'
    )
    return AdminStates.BALANCE_AMOUNT

async def handle_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace(',', '.'))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("❌ Неверная сумма. Введите положительное число:")
        return AdminStates.BALANCE_AMOUNT
    
    db = context.bot_data['db']
    user_id = context.user_data['balance_target_user_id']
    action = context.user_data['balance_action']
    admin_id = update.message.from_user.id
    
    try:
        description = f"{'Пополнение' if action == 'credit' else 'Списание'} админом ID{admin_id}"
        new_balance = db.adjust_user_balance(user_id, amount, action, description, admin_id)
        
        await update.message.reply_text(
            f"✅ *ОПЕРАЦИЯ ВЫПОЛНЕНА*\n\n"
            f"{'➕ Пополнение' if action == 'credit' else '➖ Списание'}: {amount} руб\n"
            f"💰 Новый баланс: {new_balance} руб\n\n"
            f"Операция записана в историю транзакций.",
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin {admin_id} adjusted balance for user {user_id}: {action} {amount}")
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_cancel_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Операция отменена")
    context.user_data.clear()
    return ConversationHandler.END

async def handle_block_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    blocked_users = db.get_blocked_users()
    
    keyboard = [
        [InlineKeyboardButton("🚫 Заблокировать пользователя", callback_data="block_user_start")],
        [InlineKeyboardButton("✅ Разблокировать пользователя", callback_data="unblock_user_start")],
        [InlineKeyboardButton(f"📋 Заблокированные ({len(blocked_users)})", callback_data="view_blocked_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""🚫 *УПРАВЛЕНИЕ БЛОКИРОВКАМИ*

📊 Статистика:
• Заблокированных пользователей: {len(blocked_users)}

Выберите действие:"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_view_blocked_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    blocked_users = db.get_blocked_users()
    
    if not blocked_users:
        await query.edit_message_text("✅ Нет заблокированных пользователей")
        return
    
    text = "🚫 *ЗАБЛОКИРОВАННЫЕ ПОЛЬЗОВАТЕЛИ*\n\n"
    keyboard = []
    
    for user in blocked_users[:20]:
        text += f"👤 {user['first_name']} (@{user['username'] or 'нет'})\n"
        text += f"🆔 ID: `{user['user_id']}`\n"
        text += f"📅 Дата регистрации: {user['created_at'][:10]}\n"
        text += "─────────────\n"
        
        keyboard.append([InlineKeyboardButton(
            f"✅ Разблокировать {user['first_name']}", 
            callback_data=f"unblock_user_{user['user_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="block_user_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_block_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "🚫 *БЛОКИРОВКА ПОЛЬЗОВАТЕЛЯ*\n\n"
        "Введите ID пользователя для блокировки:",
        parse_mode='Markdown'
    )
    return AdminStates.BLOCK_USER_ID

async def handle_block_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. Введите число:")
        return AdminStates.BLOCK_USER_ID
    
    admin_id = update.message.from_user.id
    if user_id == admin_id:
        await update.message.reply_text("❌ Вы не можете заблокировать самого себя!")
        return ConversationHandler.END
    
    db = context.bot_data['db']
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден. Введите другой ID:")
        return AdminStates.BLOCK_USER_ID
    
    if user['blocked'] == 1:
        await update.message.reply_text(f"⚠️ Пользователь {user['first_name']} уже заблокирован!")
        return ConversationHandler.END
    
    db.block_user(user_id)
    
    await update.message.reply_text(
        f"✅ *ПОЛЬЗОВАТЕЛЬ ЗАБЛОКИРОВАН*\n\n"
        f"👤 {user['first_name']}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📛 Username: @{user['username'] or 'не указан'}\n\n"
        f"Пользователь не сможет использовать бота.",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🚫 *ВАШ АККАУНТ ЗАБЛОКИРОВАН*\n\n"
                 "Вы были заблокированы администратором.\n"
                 "Для разблокировки обратитесь в поддержку.",
            parse_mode='Markdown'
        )
    except:
        pass
    
    logger.info(f"Admin {admin_id} blocked user {user_id}")
    return ConversationHandler.END

async def handle_unblock_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    blocked_users = db.get_blocked_users()
    
    if not blocked_users:
        await query.edit_message_text("✅ Нет заблокированных пользователей для разблокировки")
        return
    
    keyboard = []
    for user in blocked_users[:20]:
        keyboard.append([InlineKeyboardButton(
            f"✅ {user['first_name']} (@{user['username'] or 'нет'})",
            callback_data=f"unblock_user_{user['user_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="block_user_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ *РАЗБЛОКИРОВКА ПОЛЬЗОВАТЕЛЯ*\n\n"
        "Выберите пользователя для разблокировки:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    user_id = int(query.data.split('_')[-1])
    db = context.bot_data['db']
    user = db.get_user(user_id)
    
    if not user:
        await query.edit_message_text("❌ Пользователь не найден")
        return
    
    db.unblock_user(user_id)
    
    await query.edit_message_text(
        f"✅ *ПОЛЬЗОВАТЕЛЬ РАЗБЛОКИРОВАН*\n\n"
        f"👤 {user['first_name']}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📛 Username: @{user['username'] or 'не указан'}\n\n"
        f"Пользователь может снова использовать бота.",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ *ВАШ АККАУНТ РАЗБЛОКИРОВАН*\n\n"
                 "Вы можете снова пользоваться ботом.",
            parse_mode='Markdown'
        )
    except:
        pass
    
    logger.info(f"Admin {query.from_user.id} unblocked user {user_id}")

async def handle_send_message_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "💬 *ОТПРАВКА СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЮ*\n\n"
        "Введите ID пользователя:",
        parse_mode='Markdown'
    )
    return AdminStates.SEND_MESSAGE_USER_ID

async def handle_send_message_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. Введите число:")
        return AdminStates.SEND_MESSAGE_USER_ID
    
    db = context.bot_data['db']
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден. Введите другой ID:")
        return AdminStates.SEND_MESSAGE_USER_ID
    
    context.user_data['message_target_user_id'] = user_id
    context.user_data['message_target_user_name'] = user['first_name']
    
    await update.message.reply_text(
        f"👤 *Получатель:* {user['first_name']} (@{user['username'] or 'нет'})\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"💬 Введите текст сообщения:",
        parse_mode='Markdown'
    )
    return AdminStates.SEND_MESSAGE_TEXT

async def handle_send_message_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    user_id = context.user_data.get('message_target_user_id')
    user_name = context.user_data.get('message_target_user_name', 'Пользователь')
    
    if not user_id:
        await update.message.reply_text("❌ Ошибка: получатель не выбран")
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📨 *Сообщение от администратора:*\n\n{message_text}",
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            f"✅ *СООБЩЕНИЕ ОТПРАВЛЕНО*\n\n"
            f"👤 Получатель: {user_name}\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"📝 Текст:\n{message_text}",
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin {update.message.from_user.id} sent message to user {user_id}")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка отправки сообщения: {str(e)}\n\n"
            f"Возможно, пользователь заблокировал бота."
        )
        logger.error(f"Failed to send message to user {user_id}: {e}")
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_cancel_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отправка сообщения отменена")
    context.user_data.clear()
    return ConversationHandler.END

async def handle_promote_seller_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "⬆️ *ПОВЫШЕНИЕ ДО ПРОДАВЦА*\n\n"
        "Введите ID пользователя, которого хотите повысить до продавца:",
        parse_mode='Markdown'
    )
    return AdminStates.PROMOTE_USER_ID

async def handle_promote_seller_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. Введите число:")
        return AdminStates.PROMOTE_USER_ID
    
    admin_id = update.message.from_user.id
    db = context.bot_data['db']
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден. Введите другой ID:")
        return AdminStates.PROMOTE_USER_ID
    
    if user['role'] == 'manager':
        await update.message.reply_text(
            f"⚠️ Пользователь {user['first_name']} уже является продавцом!"
        )
        return ConversationHandler.END
    
    old_role = user['role']
    db.update_user_role(user_id, 'manager')
    
    await update.message.reply_text(
        f"✅ *ПОЛЬЗОВАТЕЛЬ ПОВЫШЕН ДО ПРОДАВЦА*\n\n"
        f"👤 {user['first_name']}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📛 Username: @{user['username'] or 'не указан'}\n\n"
        f"Прежняя роль: {old_role}\n"
        f"Новая роль: manager (продавец)\n\n"
        f"Пользователь теперь может добавлять товары.",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 *ПОЗДРАВЛЯЕМ!*\n\n"
                 "Вы были повышены до продавца!\n"
                 "Теперь вы можете добавлять свои товары на платформу.\n\n"
                 "Используйте меню для управления товарами.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id} about promotion: {e}")
    
    logger.info(f"Admin {admin_id} promoted user {user_id} to seller (manager)")
    context.user_data.clear()
    return ConversationHandler.END

async def handle_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    all_products = db.get_all_products()
    active_products = [p for p in all_products if p['status'] == 'active']
    pending_products = [p for p in all_products if p['status'] == 'pending']
    
    text = f"""📦 *УПРАВЛЕНИЕ ТОВАРАМИ*

📊 Статистика товаров:
• Всего товаров: {len(all_products)}
• Активных: {len(active_products)}
• На модерации: {len(pending_products)}

Выберите действие:"""
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton("📋 Все товары", callback_data="admin_view_all_products")],
        [InlineKeyboardButton("✅ Активные", callback_data="admin_view_active_products")],
        [InlineKeyboardButton("⏳ На модерации", callback_data="admin_view_pending_products")],
        [InlineKeyboardButton("❌ Неактивные", callback_data="admin_view_inactive_products")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_view_all_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    
    if query.data == "admin_view_all_products":
        products = db.get_all_products(limit=50)
        title = "ВСЕ ТОВАРЫ"
    elif query.data == "admin_view_active_products":
        products = db.get_all_products(status='active', limit=50)
        title = "АКТИВНЫЕ ТОВАРЫ"
    elif query.data == "admin_view_pending_products":
        products = db.get_all_products(status='pending', limit=50)
        title = "ТОВАРЫ НА МОДЕРАЦИИ"
    elif query.data == "admin_view_inactive_products":
        products = db.get_all_products(status='inactive', limit=50)
        title = "НЕАКТИВНЫЕ ТОВАРЫ"
    else:
        products = db.get_all_products(limit=50)
        title = "ВСЕ ТОВАРЫ"
    
    if not products:
        await query.edit_message_text("📦 Товаров не найдено")
        return
    
    text = f"📦 *{title}*\n\n"
    text += f"Найдено: {len(products)}\n\n"
    text += "Выберите товар для просмотра:\n"
    
    keyboard = []
    for product in products[:30]:
        status_emoji = {
            'active': '✅',
            'inactive': '❌',
            'pending': '⏳',
            'rejected': '🚫'
        }.get(product['status'], '❓')
        
        seller_name = product.get('seller_username') or product.get('seller_name') or product.get('seller_first_name') or f"ID{product.get('seller_id', 'unknown')}"
        
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {product['name']} | {seller_name} | {product['price']} руб", 
            callback_data=f"admin_product_{product['id']}"
        )])
    
    if len(products) > 30:
        text += f"\n_Показано 30 из {len(products)} товаров_"
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_products_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    product_id = int(query.data.split('_')[-1])
    db = context.bot_data['db']
    
    product = db.get_product(product_id)
    
    if not product:
        await query.edit_message_text("❌ Товар не найден")
        return
    
    seller_name = product['seller_username'] or product['seller_first_name'] or f"ID{product['seller_id']}"
    
    status_text = {
        'active': '✅ Активен',
        'inactive': '❌ Неактивен',
        'pending': '⏳ На модерации',
        'rejected': '🚫 Отклонен'
    }.get(product['status'], product['status'])
    
    text = f"""📦 *ТОВАР #{product_id}*

📝 Название: {product['name']}
📄 Описание: {product['description']}

💰 Цена: {product['price']} руб
📊 Остаток: {product['stock']} шт
📁 Категория: {product['category_name'] or 'Нет'}
📍 Локация: {product['country_name']}, {product['city_name']}, {product['district_name']}

👤 Продавец: {seller_name} (ID: {product['seller_id']})
📌 Статус: {status_text}
⭐ Рейтинг: {product['avg_rating'] or 0:.1f} ({product['rating_count']} отзывов)

🕐 Создан: {product['created_at'][:16]}
🕑 Обновлен: {product['updated_at'][:16]}"""
    
    keyboard = []
    
    if product['status'] == 'pending':
        keyboard.append([
            InlineKeyboardButton("✅ Одобрить", callback_data=f"moderate_product_{product_id}_active"),
            InlineKeyboardButton("🚫 Отклонить", callback_data=f"moderate_product_{product_id}_rejected")
        ])
    elif product['status'] == 'active':
        keyboard.append([InlineKeyboardButton("❌ Деактивировать", callback_data=f"moderate_product_{product_id}_inactive")])
    elif product['status'] == 'inactive':
        keyboard.append([InlineKeyboardButton("✅ Активировать", callback_data=f"moderate_product_{product_id}_active")])
    
    keyboard.append([InlineKeyboardButton("🗑️ Удалить товар", callback_data=f"admin_delete_product_{product_id}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_view_all_products")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    import os
    if product['image_path'] and os.path.exists(product['image_path']):
        try:
            with open(product['image_path'], 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            await query.message.delete()
            return
        except:
            pass
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_moderate_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    parts = query.data.split('_')
    product_id = int(parts[2])
    new_status = parts[3]
    
    db = context.bot_data['db']
    product = db.get_product(product_id)
    
    if not product:
        await query.edit_message_text("❌ Товар не найден")
        return
    
    seller_name = product['seller_username'] or product['seller_first_name'] or f"ID{product['seller_id']}"
    
    success = db.moderate_product(product_id, new_status, query.from_user.id)
    
    status_names = {
        'active': 'активирован',
        'inactive': 'деактивирован',
        'rejected': 'отклонен',
        'pending': 'отправлен на модерацию'
    }
    
    if success:
        await query.edit_message_text(
            f"✅ *ТОВАР {status_names.get(new_status, new_status).upper()}*\n\n"
            f"📦 {product['name']}\n"
            f"👤 Продавец: {seller_name}\n"
            f"🆔 ID товара: {product_id}",
            parse_mode='Markdown'
        )
        
        try:
            status_messages = {
                'active': '✅ Ваш товар одобрен и активирован!',
                'inactive': '❌ Ваш товар деактивирован администратором.',
                'rejected': '🚫 Ваш товар отклонен модератором.',
            }
            
            if new_status in status_messages:
                await context.bot.send_message(
                    chat_id=product['seller_id'],
                    text=f"📦 *Обновление статуса товара*\n\n"
                         f"Товар: {product['name']}\n\n"
                         f"{status_messages[new_status]}",
                    parse_mode='Markdown'
                )
        except:
            pass
        
        logger.info(f"Admin {query.from_user.id} moderated product {product_id} to {new_status}")
    else:
        await query.edit_message_text("❌ Ошибка при изменении статуса товара")

async def handle_delete_product_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    product_id = int(query.data.split('_')[-1])
    context.user_data['deleting_product_id'] = product_id
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"admin_confirm_delete_yes_{product_id}"),
         InlineKeyboardButton("❌ Отмена", callback_data=f"admin_confirm_delete_no_{product_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚠️ *ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ*\n\n"
        "Вы уверены, что хотите удалить этот товар?\n"
        "Это действие нельзя отменить!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_confirm_delete_product_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    action = query.data.split('_')[3]
    product_id = int(query.data.split('_')[-1])
    
    db = context.bot_data['db']
    
    if action == 'yes':
        product = db.get_product(product_id)
        
        if not product:
            await query.edit_message_text("❌ Товар не найден")
            return
        
        seller_name = product['seller_username'] or product['seller_first_name'] or f"ID{product['seller_id']}"
        
        if db.delete_product(product_id):
            await query.edit_message_text(
                f"✅ *ТОВАР УДАЛЕН*\n\n"
                f"📦 {product['name']}\n"
                f"👤 Продавец: {seller_name}\n"
                f"🆔 ID: {product_id}",
                parse_mode='Markdown'
            )
            
            try:
                await context.bot.send_message(
                    chat_id=product['seller_id'],
                    text=f"🗑️ *Ваш товар удален*\n\n"
                         f"Товар \"{product['name']}\" был удален администратором.",
                    parse_mode='Markdown'
                )
            except:
                pass
            
            logger.info(f"Admin {query.from_user.id} deleted product {product_id}")
        else:
            await query.edit_message_text("❌ Ошибка при удалении товара")
    else:
        await handle_admin_product_detail(update, context)

async def handle_list_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    all_users = db.get_all_users()
    
    if not all_users:
        await query.edit_message_text("📋 Пользователей не найдено")
        return
    
    text = f"📋 *СПИСОК ВСЕХ ПОЛЬЗОВАТЕЛЕЙ*\n\n"
    text += f"Всего пользователей: {len(all_users)}\n\n"
    
    for user in all_users[:50]:
        role_emoji = {
            'buyer': '🛍️',
            'manager': '💼',
            'pending': '⏳',
            'admin': '👑'
        }.get(user['role'], '👤')
        
        blocked_mark = '🚫 ' if user['blocked'] == 1 else ''
        text += f"{role_emoji} {blocked_mark}{user['first_name']} (@{user['username'] or 'нет'}) - ID: `{user['user_id']}`\n"
    
    if len(all_users) > 50:
        text += f"\n_Показано 50 из {len(all_users)} пользователей_"
    
    await query.edit_message_text(text, parse_mode='Markdown')

async def handle_list_buyers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    buyers = db.get_all_users(role='buyer')
    
    if not buyers:
        await query.edit_message_text("🛍️ Покупателей не найдено")
        return
    
    text = f"🛍️ *СПИСОК ПОКУПАТЕЛЕЙ*\n\n"
    text += f"Всего покупателей: {len(buyers)}\n\n"
    
    for user in buyers[:30]:
        blocked_mark = '🚫 ' if user['blocked'] == 1 else ''
        text += f"{blocked_mark}{user['first_name']} (@{user['username'] or 'нет'}) - ID: `{user['user_id']}`\n"
    
    if len(buyers) > 30:
        text += f"\n_Показано 30 из {len(buyers)} покупателей_"
    
    await query.edit_message_text(text, parse_mode='Markdown')

async def handle_list_managers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    db = context.bot_data['db']
    managers = db.get_all_users(role='manager')
    
    if not managers:
        await query.edit_message_text("💼 Продавцов не найдено")
        return
    
    text = f"💼 *СПИСОК ПРОДАВЦОВ*\n\n"
    text += f"Всего продавцов: {len(managers)}\n\n"
    
    for user in managers[:30]:
        blocked_mark = '🚫 ' if user['blocked'] == 1 else ''
        
        products_count = len(db.get_seller_products(user['user_id']))
        rating = db.get_seller_rating(user['user_id'])
        rating_text = f"⭐ {rating['avg_rating']:.1f}" if rating and rating['avg_rating'] else "⭐ 0.0"
        
        text += f"{blocked_mark}{user['first_name']} - {products_count} товаров - {rating_text} - ID: `{user['user_id']}`\n"
    
    if len(managers) > 30:
        text += f"\n_Показано 30 из {len(managers)} продавцов_"
    
    await query.edit_message_text(text, parse_mode='Markdown')

async def handle_promo_codes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    text = """🎫 *УПРАВЛЕНИЕ ПРОМО-КОДАМИ*

⚠️ Функция находится в разработке

Промо-коды позволят предоставлять скидки пользователям.

В будущих версиях будут доступны:
• Создание промо-кодов
• Управление скидками
• Отслеживание использования

Функционал будет добавлен в ближайшее время."""
    
    await query.edit_message_text(text, parse_mode='Markdown')

async def handle_add_subcategory_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    db = context.bot_data['db']
    parent_categories = db.get_categories()
    
    if not parent_categories:
        await query.edit_message_text("❌ Сначала добавьте основную категорию")
        return ConversationHandler.END
    
    keyboard = []
    for category in parent_categories:
        keyboard.append([InlineKeyboardButton(
            category['name'],
            callback_data=f"select_parent_cat_{category['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_subcategory")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📁 *ДОБАВЛЕНИЕ ПОДКАТЕГОРИИ*\n\nВыберите родительскую категорию:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return AdminStates.SELECT_PARENT_CATEGORY

async def handle_subcategory_parent_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parent_id = int(query.data.split('_')[-1])
    context.user_data['parent_category_id'] = parent_id
    
    db = context.bot_data['db']
    categories = db.get_categories()
    parent_category = next((c for c in categories if c['id'] == parent_id), None)
    
    if parent_category:
        await query.edit_message_text(
            f"📁 *ДОБАВЛЕНИЕ ПОДКАТЕГОРИИ*\n\n"
            f"Родительская категория: *{parent_category['name']}*\n\n"
            f"Введите название подкатегории:",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ Категория не найдена")
        return ConversationHandler.END
    
    return AdminStates.ADD_SUBCATEGORY_NAME

async def handle_add_subcategory_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    subcategory_name = update.message.text.strip()
    parent_id = context.user_data.get('parent_category_id')
    
    if not parent_id:
        await update.message.reply_text("❌ Ошибка: родительская категория не выбрана")
        return ConversationHandler.END
    
    try:
        db.add_category(subcategory_name, parent_id, update.message.from_user.id)
        
        categories = db.get_categories()
        parent_category = next((c for c in categories if c['id'] == parent_id), None)
        parent_name = parent_category['name'] if parent_category else 'Неизвестная'
        
        await update.message.reply_text(
            f"✅ Подкатегория '{subcategory_name}' добавлена в категорию '{parent_name}'!"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_admin_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        return
    
    text = """📋 *ПРАВИЛА АДМИНИСТРАТОРА*

*1. МОДЕРАЦИЯ:*
• Проверяйте все новые товары в течение 24 часов
• Отклоняйте запрещенные товары
• Следите за качеством контента

*2. УПРАВЛЕНИЕ:*
• Реагируйте на жалобы пользователей
• Блокируйте нарушителей
• Поддерживайте порядок на платформе

*3. КОНФИДЕНЦИАЛЬНОСТЬ:*
• Не разглашайте данные пользователей
• Соблюдайте этику и справедливость
• Документируйте важные решения

*4. ПОДДЕРЖКА:*
• Помогайте пользователям с проблемами
• Отвечайте на вопросы своевременно
• Решайте споры справедливо"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_admin_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        return
    
    text = """📞 *КОНТАКТЫ АДМИНИСТРАЦИИ*

*Техническая поддержка:*
• Dev team: dev@shop-q.com (пример)
• Telegram: @shop_q_dev (пример)

*Главный администратор:*
• Email: admin@shop-q.com (пример)
• Telegram: @shop_q_admin (пример)

*Модераторы:*
• Email: moderators@shop-q.com (пример)
• Чат модераторов: @shop_q_mods (пример)

*Экстренная связь:*
• Hotline: +X-XXX-XXX-XXXX (пример)"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_admin_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        return
    
    text = """❓ *FAQ ДЛЯ АДМИНИСТРАТОРОВ*

*1. Как модерировать товары?*
"📦 Товары" → "⏳ На модерации" → выберите товар → "✅ Одобрить" или "🚫 Отклонить".

*2. Как заблокировать пользователя?*
"👥 Пользователи" → найдите пользователя → "🚫 Заблокировать".

*3. Как добавить локацию?*
"🌍 Локации" → выберите тип (страна/город/район) → "➕ Добавить".

*4. Как добавить категорию?*
"📁 Категории" → введите название категории.

*5. Как посмотреть статистику?*
Нажмите "📊 Статистика" в главном меню.

*6. Как сделать рассылку?*
"🛠️ Инструменты" → "📣 Рассылка" → введите текст.

*7. Как решить спор?*
"🛠️ Инструменты" → "⚠️ Жалобы" → выберите жалобу → примите решение.

*8. Как удалить товар?*
"📦 Товары" → найдите товар → "🗑️ Удалить товар"."""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_admin_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.message.from_user.id):
        return
    
    user = update.message.from_user
    db = context.bot_data['db']
    
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("❌ Профиль не найден")
        return
    
    users_count = len(db.get_all_users())
    stats = db.get_statistics()
    products_count = stats['total_products']
    
    text = f"""👤 *ПРОФИЛЬ АДМИНИСТРАТОРА*

*Личная информация:*
• Имя: {user_data['first_name']}
• Username: @{user_data['username'] or 'не указан'}
• ID: `{user.id}`
• Статус: Администратор 🔐

*Статистика системы:*
• Пользователей: {users_count}
• Активных товаров: {products_count}
• Баланс: {user_data['balance']:.2f} руб

*Аккаунт создан:* {user_data['created_at'][:10] if user_data.get('created_at') else 'неизвестно'}
*Последняя активность:* {user_data['last_active'][:16] if user_data.get('last_active') else 'неизвестно'}

💼 Продолжайте эффективно управлять платформой!"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_admin_add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not check_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📝 *СОЗДАНИЕ ТОВАРА ОТ ИМЕНИ ПРОДАВЦА*\n\n"
        "Шаг 1/9: Введите название товара:",
        parse_mode='Markdown'
    )
    return AdminStates.ADMIN_PRODUCT_NAME

async def handle_admin_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    
    if len(name) < 3:
        await update.message.reply_text("❌ Название слишком короткое. Минимум 3 символа.")
        return AdminStates.ADMIN_PRODUCT_NAME
    
    context.user_data['admin_product_name'] = name
    
    await update.message.reply_text(
        f"✅ Название: {name}\n\n"
        "Шаг 2/9: Введите описание товара:"
    )
    return AdminStates.ADMIN_PRODUCT_DESC

async def handle_admin_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    
    if len(desc) < 10:
        await update.message.reply_text("❌ Описание слишком короткое. Минимум 10 символов.")
        return AdminStates.ADMIN_PRODUCT_DESC
    
    context.user_data['admin_product_desc'] = desc
    
    await update.message.reply_text(
        "Шаг 3/9: Введите цену товара (только число):"
    )
    return AdminStates.ADMIN_PRODUCT_PRICE

async def handle_admin_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.strip())
        if price <= 0:
            raise ValueError()
    except:
        await update.message.reply_text("❌ Неверная цена. Введите положительное число.")
        return AdminStates.ADMIN_PRODUCT_PRICE
    
    context.user_data['admin_product_price'] = price
    
    await update.message.reply_text(
        f"✅ Цена: {price} руб\n\n"
        "Шаг 4/9: Введите количество товара (остаток):"
    )
    return AdminStates.ADMIN_PRODUCT_STOCK

async def handle_admin_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stock = int(update.message.text.strip())
        if stock < 0:
            raise ValueError()
    except:
        await update.message.reply_text("❌ Неверное количество. Введите целое число.")
        return AdminStates.ADMIN_PRODUCT_STOCK
    
    context.user_data['admin_product_stock'] = stock
    
    db = context.bot_data['db']
    categories = db.get_categories()
    
    if not categories:
        await update.message.reply_text("❌ Нет доступных категорий. Сначала создайте категорию.")
        context.user_data.clear()
        return ConversationHandler.END
    
    keyboard = []
    for cat in categories:
        subcats = db.get_categories(cat['id'])
        count_text = f" ({len(subcats)})" if subcats else ""
        keyboard.append([InlineKeyboardButton(f"📁 {cat['name']}{count_text}", callback_data=f"admin_cat_{cat['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Шаг 5/9: Выберите категорию товара:",
        reply_markup=reply_markup
    )
    return AdminStates.ADMIN_PRODUCT_CATEGORY

async def handle_admin_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_cat_back":
        db = context.bot_data['db']
        categories = db.get_categories()
        
        keyboard = []
        for cat in categories:
            subcats = db.get_categories(cat['id'])
            count_text = f" ({len(subcats)})" if subcats else ""
            keyboard.append([InlineKeyboardButton(f"📁 {cat['name']}{count_text}", callback_data=f"admin_cat_{cat['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Шаг 5/9: Выберите категорию товара:",
            reply_markup=reply_markup
        )
        return AdminStates.ADMIN_PRODUCT_CATEGORY
    
    if query.data.startswith("admin_cat_final_"):
        category_id = int(query.data.split('_')[3])
    else:
        category_id = int(query.data.split('_')[2])
    
    db = context.bot_data['db']
    
    if query.data.startswith("admin_cat_final_"):
        context.user_data['admin_product_category'] = category_id
        
        countries = db.get_countries()
        
        if not countries:
            await query.edit_message_text("❌ Нет доступных стран. Обратитесь к администратору.")
            context.user_data.clear()
            return ConversationHandler.END
        
        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(country['name'], callback_data=f"admin_country_{country['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        path = db.get_category_path(category_id)
        path_text = " / ".join([c['name'] for c in path])
        
        await query.edit_message_text(
            f"✅ Категория: {path_text}\n\nШаг 6/9: Выберите страну:",
            reply_markup=reply_markup
        )
        return AdminStates.ADMIN_PRODUCT_COUNTRY
    
    subcategories = db.get_categories(category_id)
    
    if subcategories:
        keyboard = []
        path = db.get_category_path(category_id)
        path_text = " / ".join([c['name'] for c in path])
        
        for subcat in subcategories:
            subsubcats = db.get_categories(subcat['id'])
            count_text = f" ({len(subsubcats)})" if subsubcats else ""
            keyboard.append([InlineKeyboardButton(f"📁 {subcat['name']}{count_text}", callback_data=f"admin_cat_{subcat['id']}")])
        
        keyboard.append([InlineKeyboardButton("✅ Выбрать эту категорию", callback_data=f"admin_cat_final_{category_id}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_cat_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📁 Текущий путь: {path_text}\n\nВыберите подкатегорию или завершите выбор:",
            reply_markup=reply_markup
        )
        return AdminStates.ADMIN_PRODUCT_CATEGORY
    else:
        context.user_data['admin_product_category'] = category_id
        
        countries = db.get_countries()
        
        if not countries:
            await query.edit_message_text("❌ Нет доступных стран. Обратитесь к администратору.")
            context.user_data.clear()
            return ConversationHandler.END
        
        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(country['name'], callback_data=f"admin_country_{country['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        path = db.get_category_path(category_id)
        path_text = " / ".join([c['name'] for c in path])
        
        await query.edit_message_text(
            f"✅ Категория: {path_text}\n\nШаг 6/9: Выберите страну:",
            reply_markup=reply_markup
        )
        return AdminStates.ADMIN_PRODUCT_COUNTRY

async def handle_admin_select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    country_id = int(query.data.split('_')[2])
    context.user_data['admin_product_country'] = country_id
    
    db = context.bot_data['db']
    cities = db.get_cities(country_id)
    
    if not cities:
        await query.edit_message_text("❌ В этой стране нет городов.")
        context.user_data.clear()
        return ConversationHandler.END
    
    keyboard = []
    for city in cities:
        keyboard.append([InlineKeyboardButton(city['name'], callback_data=f"admin_city_{city['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Шаг 7/9: Выберите город:",
        reply_markup=reply_markup
    )
    return AdminStates.ADMIN_PRODUCT_CITY

async def handle_admin_select_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    city_id = int(query.data.split('_')[2])
    context.user_data['admin_product_city'] = city_id
    
    db = context.bot_data['db']
    districts = db.get_districts(city_id)
    
    if not districts:
        await query.edit_message_text("❌ В этом городе нет районов.")
        context.user_data.clear()
        return ConversationHandler.END
    
    keyboard = []
    for district in districts:
        keyboard.append([InlineKeyboardButton(district['name'], callback_data=f"admin_district_{district['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Шаг 8/9: Выберите район:",
        reply_markup=reply_markup
    )
    return AdminStates.ADMIN_PRODUCT_DISTRICT

async def handle_admin_select_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    district_id = int(query.data.split('_')[2])
    context.user_data['admin_product_district'] = district_id
    
    db = context.bot_data['db']
    managers = db.get_all_users(role='manager')
    
    admin_user = db.get_user(query.from_user.id)
    if admin_user:
        if admin_user not in managers:
            managers.insert(0, admin_user)
    
    if not managers:
        await query.edit_message_text("❌ Нет продавцов. Сначала создайте продавца.")
        context.user_data.clear()
        return ConversationHandler.END
    
    keyboard = []
    for manager in managers[:30]:
        username = manager['username'] or manager['first_name']
        role_mark = " (Админ)" if manager['role'] == 'admin' else ""
        keyboard.append([InlineKeyboardButton(
            f"{username}{role_mark} (ID: {manager['user_id']})",
            callback_data=f"admin_seller_{manager['user_id']}"
        )])
    
    if len(managers) > 30:
        keyboard.append([InlineKeyboardButton("Показано 30 из {}".format(len(managers)), callback_data="noop")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Шаг 9/9: Выберите продавца для товара:",
        reply_markup=reply_markup
    )
    return AdminStates.ADMIN_PRODUCT_SELLER

async def handle_admin_select_seller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    seller_id = int(query.data.split('_')[2])
    context.user_data['admin_product_seller'] = seller_id
    
    await query.edit_message_text(
        "Шаг 10/10 (опционально): Отправьте фото товара или напишите 'Пропустить'"
    )
    return AdminStates.ADMIN_PRODUCT_IMAGE

async def handle_admin_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    
    image_path = None
    
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        os.makedirs('images/products', exist_ok=True)
        seller_id = context.user_data['admin_product_seller']
        image_path = f"images/products/{seller_id}_{photo.file_id}.jpg"
        await file.download_to_drive(image_path)
    
    try:
        product_id = db.add_product(
            seller_id=context.user_data['admin_product_seller'],
            name=context.user_data['admin_product_name'],
            description=context.user_data['admin_product_desc'],
            price=context.user_data['admin_product_price'],
            stock=context.user_data['admin_product_stock'],
            category_id=context.user_data['admin_product_category'],
            country_id=context.user_data['admin_product_country'],
            city_id=context.user_data['admin_product_city'],
            district_id=context.user_data['admin_product_district'],
            image_path=image_path
        )
        
        seller_id = context.user_data['admin_product_seller']
        seller = db.get_user(seller_id)
        seller_name = seller['username'] or seller['first_name']
        
        await update.message.reply_text(
            f"✅ *ТОВАР СОЗДАН!*\n\n"
            f"📦 ID: {product_id}\n"
            f"📝 Название: {context.user_data['admin_product_name']}\n"
            f"💰 Цена: {context.user_data['admin_product_price']} руб\n"
            f"📊 Остаток: {context.user_data['admin_product_stock']} шт\n"
            f"👤 Продавец: {seller_name} (ID: {seller_id})",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                chat_id=seller_id,
                text=f"📦 *Новый товар добавлен админом*\n\n"
                     f"Название: {context.user_data['admin_product_name']}\n"
                     f"Цена: {context.user_data['admin_product_price']} руб\n"
                     f"ID: {product_id}",
                parse_mode='Markdown'
            )
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error creating admin product: {e}")
        await update.message.reply_text(f"❌ Ошибка при создании товара: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

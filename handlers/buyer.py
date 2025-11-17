from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from database import Database
from utils import format_price, format_rating
import config
import os

class BuyerStates:
    SELECT_COUNTRY = 1
    SELECT_CITY = 2
    SELECT_DISTRICT = 3
    VIEW_SELLERS = 4
    VIEW_PRODUCTS = 5
    SEARCH_QUERY = 6
    COMPLAINT_REASON = 7
    RATING_VALUE = 8
    RATING_COMMENT = 9
    ADVANCED_SEARCH_CATEGORY = 10
    ADVANCED_SEARCH_LOCATION = 11
    ADVANCED_SEARCH_PRICE_MIN = 12
    ADVANCED_SEARCH_PRICE_MAX = 13
    ADD_BALANCE_AMOUNT = 14

def setup_buyer_handlers(application):
    
    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 Поиск$"), handle_search_start)],
        states={
            BuyerStates.SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_action)],
        per_message=False
    )
    
    advanced_search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔎 Расширенный поиск$"), handle_advanced_search_start)],
        states={
            BuyerStates.ADVANCED_SEARCH_CATEGORY: [
                CallbackQueryHandler(handle_advanced_search_category, pattern="^adv_cat_|^adv_skip_category$")
            ],
            BuyerStates.ADVANCED_SEARCH_PRICE_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_advanced_search_price_min)
            ],
            BuyerStates.ADVANCED_SEARCH_PRICE_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_advanced_search_price_max)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_action)],
        per_message=False
    )
    
    complaint_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_complaint, pattern="^complaint_")],
        states={
            BuyerStates.COMPLAINT_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complaint_reason)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_action)],
        per_message=False
    )
    
    rating_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_leave_rating_start, pattern="^leave_rating_")],
        states={
            BuyerStates.RATING_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rating_value)],
            BuyerStates.RATING_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rating_comment)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_action)],
        per_message=False
    )
    
    add_balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_add_balance_start, pattern="^add_balance$")],
        states={
            BuyerStates.ADD_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_balance_amount)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_action)],
        per_message=False
    )
    
    application.add_handler(search_conv)
    application.add_handler(advanced_search_conv)
    application.add_handler(complaint_conv)
    application.add_handler(rating_conv)
    application.add_handler(add_balance_conv)
    
    application.add_handler(MessageHandler(filters.Regex("^🏪 Магазины$"), handle_shops))
    application.add_handler(CallbackQueryHandler(handle_select_country, pattern="^shop_country_"))
    application.add_handler(CallbackQueryHandler(handle_select_city, pattern="^shop_city_"))
    application.add_handler(CallbackQueryHandler(handle_select_district, pattern="^shop_district_"))
    application.add_handler(CallbackQueryHandler(handle_shops, pattern="^back_to_countries$"))
    application.add_handler(CallbackQueryHandler(handle_view_seller_products, pattern="^seller_"))
    application.add_handler(CallbackQueryHandler(handle_view_product, pattern="^view_product_"))
    application.add_handler(CallbackQueryHandler(handle_add_to_cart, pattern="^add_cart_"))
    application.add_handler(CallbackQueryHandler(handle_add_to_favorites, pattern="^add_fav_"))
    application.add_handler(CallbackQueryHandler(handle_msg_seller, pattern="^msg_seller_"))
    application.add_handler(CallbackQueryHandler(handle_subscribe, pattern="^subscribe_"))
    application.add_handler(CallbackQueryHandler(handle_unsubscribe, pattern="^unsubscribe_"))
    application.add_handler(CallbackQueryHandler(handle_view_reviews, pattern="^reviews_"))
    application.add_handler(CallbackQueryHandler(handle_request_seller_verification, pattern="^request_seller_verification$"))
    
    application.add_handler(MessageHandler(filters.Regex("^🛒 Корзина$"), handle_view_cart))
    application.add_handler(MessageHandler(filters.Regex("^📦 Мои заказы$"), handle_my_orders))
    application.add_handler(MessageHandler(filters.Regex("^👤 Профиль$"), handle_profile_router))
    application.add_handler(MessageHandler(filters.Regex("^⭐ Избранное$"), handle_favorites))
    application.add_handler(MessageHandler(filters.Regex("^👥 Мои подписки$"), handle_view_subscriptions))
    application.add_handler(MessageHandler(filters.Regex("^💬 Поддержка$"), handle_support))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ Информация$"), handle_info))
    application.add_handler(MessageHandler(filters.Regex("^📋 Правила$"), handle_rules))
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), handle_contacts))
    application.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), handle_faq))
    application.add_handler(MessageHandler(filters.Regex("^📚 Каталог$"), handle_catalog))
    application.add_handler(CallbackQueryHandler(handle_catalog_category, pattern="^catalog_cat_|^catalog_all$"))
    application.add_handler(CallbackQueryHandler(handle_catalog_back, pattern="^catalog_back$"))

async def handle_shops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    countries = db.get_countries()
    
    if not countries:
        text = "🌍 Пока нет доступных локаций"
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return
    
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(
            f"🌍 {country['name']}", 
            callback_data=f"shop_country_{country['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🏪 *ВЫБОР МАГАЗИНА*\n\nШаг 1/3: Выберите страну:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    country_id = int(query.data.split('_')[-1])
    context.user_data['selected_country'] = country_id
    
    db = context.bot_data['db']
    cities = db.get_cities(country_id)
    
    if not cities:
        await query.edit_message_text("❌ В этой стране нет доступных городов")
        return
    
    keyboard = []
    for city in cities:
        keyboard.append([InlineKeyboardButton(
            f"🏙️ {city['name']}", 
            callback_data=f"shop_city_{city['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_countries")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Шаг 2/3: Выберите город:",
        reply_markup=reply_markup
    )

async def handle_select_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    city_id = int(query.data.split('_')[-1])
    context.user_data['selected_city'] = city_id
    
    db = context.bot_data['db']
    districts = db.get_districts(city_id)
    
    if not districts:
        await query.edit_message_text("❌ В этом городе нет доступных районов")
        return
    
    keyboard = []
    for district in districts:
        keyboard.append([InlineKeyboardButton(
            f"📍 {district['name']}", 
            callback_data=f"shop_district_{district['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"shop_country_{context.user_data['selected_country']}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Шаг 3/3: Выберите район:",
        reply_markup=reply_markup
    )

async def handle_select_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    district_id = int(query.data.split('_')[-1])
    context.user_data['selected_district'] = district_id
    
    db = context.bot_data['db']
    country_id = context.user_data['selected_country']
    city_id = context.user_data['selected_city']
    
    sellers = db.get_sellers_by_location(country_id, city_id, district_id)
    
    if not sellers:
        await query.edit_message_text("❌ В этом районе нет продавцов с товарами")
        return
    
    keyboard = []
    for seller in sellers:
        rating = seller['avg_rating'] if seller['avg_rating'] else 0
        keyboard.append([InlineKeyboardButton(
            f"🛍️ {seller['username'] or seller['first_name']} | ⭐{rating:.1f} | 📦{seller['product_count']}", 
            callback_data=f"seller_{seller['user_id']}_{country_id}_{city_id}_{district_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"shop_city_{city_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🛍️ *ПРОДАВЦЫ В ВЫБРАННОМ РАЙОНЕ*\n\n"
        f"Найдено продавцов: {len(sellers)}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_view_seller_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    seller_id = int(parts[1])
    country_id = int(parts[2])
    city_id = int(parts[3])
    district_id = int(parts[4])
    
    db = context.bot_data['db']
    products = db.get_products_by_location(country_id, city_id, district_id)
    
    seller_products = [p for p in products if p['seller_id'] == seller_id]
    
    if not seller_products:
        await query.edit_message_text("❌ У этого продавца нет товаров")
        return
    
    keyboard = []
    for product in seller_products[:20]:
        keyboard.append([InlineKeyboardButton(
            f"📦 {product['name']} - {product['price']} руб", 
            callback_data=f"view_product_{product['id']}"
        )])
    
    subscriptions = db.get_user_subscriptions(query.from_user.id)
    is_subscribed = any(sub['seller_id'] == seller_id for sub in subscriptions)
    
    if is_subscribed:
        keyboard.append([InlineKeyboardButton("❌ Отписаться", callback_data=f"unsubscribe_{seller_id}")])
    else:
        keyboard.append([InlineKeyboardButton("➕ Подписаться", callback_data=f"subscribe_{seller_id}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"shop_district_{district_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    seller_data = db.get_user(seller_id)
    rating_data = db.get_seller_rating(seller_id)
    avg_rating = rating_data['avg_rating'] if rating_data['avg_rating'] else 0
    
    subs_count = len(db.get_seller_subscribers(seller_id))
    
    await query.edit_message_text(
        f"🛍️ *МАГАЗИН: {seller_data['username'] or seller_data['first_name']}*\n\n"
        f"⭐ Рейтинг: {avg_rating:.1f}\n"
        f"📦 Товаров: {len(seller_products)}\n"
        f"👥 Подписчиков: {subs_count}\n\n"
        f"Выберите товар:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_view_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[-1])
    
    db = context.bot_data['db']
    product = db.get_product(product_id)
    
    if not product:
        await query.edit_message_text("❌ Товар не найден")
        return
    
    seller_rating = db.get_seller_rating(product['seller_id'])
    seller_avg_rating = seller_rating['avg_rating'] if seller_rating['avg_rating'] else 0
    
    text = f"""📦 *{product['name']}*

📝 {product['description']}

📁 Категория: {product['category_name'] or 'Нет'}
📍 Локация: {product['country_name']}, {product['city_name']}, {product['district_name']}

⭐ Рейтинг товара: {product['avg_rating'] or 0:.1f} ({product['rating_count']} отзывов)
⭐ Рейтинг продавца: {seller_avg_rating:.1f}

📊 Остаток: {product['stock']} шт
💵 Цена: {product['price']} руб
"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 В корзину", callback_data=f"add_cart_{product_id}")],
        [InlineKeyboardButton("⭐ В избранное", callback_data=f"add_fav_{product_id}")],
        [InlineKeyboardButton("📝 Отзывы", callback_data=f"reviews_{product_id}")],
        [InlineKeyboardButton("✉️ Написать продавцу", callback_data=f"msg_seller_{product['seller_id']}")],
        [InlineKeyboardButton("⚠️ Пожаловаться", callback_data=f"complaint_{product_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"seller_{product['seller_id']}_{product['country_id']}_{product['city_id']}_{product['district_id']}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    product_id = int(query.data.split('_')[-1])
    user_id = query.from_user.id
    
    db = context.bot_data['db']
    db.add_to_cart(user_id, product_id, 1)
    
    await query.answer("✅ Товар добавлен в корзину!", show_alert=True)

async def handle_add_to_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    product_id = int(query.data.split('_')[-1])
    user_id = query.from_user.id
    
    db = context.bot_data['db']
    cursor = db.conn.cursor()
    
    try:
        cursor.execute('''INSERT INTO favorites (user_id, product_id, added_at)
                     VALUES (?, ?, datetime('now'))''',
                     (user_id, product_id))
        db.conn.commit()
        await query.answer("⭐ Добавлено в избранное!", show_alert=True)
    except:
        await query.answer("❌ Уже в избранном", show_alert=True)

async def handle_msg_seller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    seller_id = int(query.data.split('_')[-1])
    db = context.bot_data['db']
    
    seller = db.get_user(seller_id)
    
    if not seller:
        await query.answer("❌ Продавец не найден", show_alert=True)
        return
    
    seller_username = seller['username']
    seller_name = seller['first_name']
    
    if seller_username:
        text = f"✉️ *НАПИСАТЬ ПРОДАВЦУ*\n\n"
        text += f"Продавец: {seller_name}\n"
        text += f"Username: @{seller_username}\n\n"
        text += f"Вы можете написать продавцу напрямую в Telegram: @{seller_username}"
    else:
        text = f"✉️ *НАПИСАТЬ ПРОДАВЦУ*\n\n"
        text += f"Продавец: {seller_name}\n"
        text += f"ID: `{seller_id}`\n\n"
        text += f"К сожалению, у продавца не указан username.\n"
        text += f"Вы можете связаться с ним через поддержку."
    
    await query.answer("ℹ️ Информация о продавце", show_alert=False)
    await query.edit_message_text(text, parse_mode='Markdown')

async def handle_view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    cart_items = db.get_cart(user_id)
    
    if not cart_items:
        await update.message.reply_text("🛒 Ваша корзина пуста")
        return
    
    text = "🛒 *ВАША КОРЗИНА*\n\n"
    total = 0
    
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        total += item_total
        seller_name = item.get('seller_username') or item.get('seller_name') or item.get('seller_first_name') or f"ID{item.get('seller_id', 'unknown')}"
        text += f"📦 {item['name']}\n"
        text += f"   {item['quantity']} x {item['price']} = {item_total} руб\n"
        text += f"   Продавец: {seller_name}\n"
        text += "─────────────\n"
    
    text += f"\n💰 *Итого: {total} руб*"
    
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout_cart")],
        [InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 *ПОИСК ТОВАРОВ*\n\n"
        "Введите название товара для поиска:",
        parse_mode='Markdown'
    )
    return BuyerStates.SEARCH_QUERY

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    db = context.bot_data['db']
    
    products = db.search_products(query)
    
    if not products:
        await update.message.reply_text(
            f"❌ По запросу '{query}' ничего не найдено.\n\n"
            "Попробуйте изменить запрос."
        )
        return ConversationHandler.END
    
    text = f"🔍 *Результаты поиска: '{query}'*\n\n"
    text += f"Найдено товаров: {len(products)}\n\n"
    
    keyboard = []
    for product in products[:10]:
        seller_name = product['seller_username'] or f"ID{product['seller_id']}"
        button_text = f"📦 {product['name']} - {product['price']} руб ({seller_name})"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"view_product_{product['id']}"
        )])
    
    if len(products) > 10:
        text += f"_Показаны первые 10 из {len(products)} результатов_"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return ConversationHandler.END

async def handle_profile_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    user_data = db.get_user(user_id)
    
    if not user_data:
        await update.message.reply_text("❌ Профиль не найден")
        return
    
    role = user_data['role']
    
    if role == 'admin':
        from handlers.admin import handle_admin_profile
        await handle_admin_profile(update, context)
    elif role == 'manager':
        from handlers.manager import handle_manager_profile
        await handle_manager_profile(update, context)
    else:
        await handle_profile(update, context)

async def handle_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    orders = db.get_user_orders(user_id, role='buyer')
    
    if not orders:
        await update.message.reply_text("📦 У вас пока нет заказов")
        return
    
    text = f"📦 *МОИ ЗАКАЗЫ* ({len(orders)})\n\n"
    
    for order in orders[:10]:
        text += f"📋 Заказ #{order['order_number']}\n"
        text += f"🛍️ {order['product_name']}\n"
        text += f"💰 {order['total_price']} руб x {order['quantity']}\n"
        text += f"📊 Статус: {order['status']}\n"
        text += f"📅 {order['created_at'][:10]}\n"
        text += "─────────────\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db = context.bot_data['db']
    
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("❌ Профиль не найден")
        return
    
    orders = db.get_user_orders(user.id, role='buyer')
    
    text = f"""👤 *МОЙ ПРОФИЛЬ*

👤 Имя: {user_data['first_name']}
🆔 ID: `{user_data['user_id']}`
📞 Телефон: {user_data['phone'] or 'не указан'}

💰 Баланс: {user_data['balance']:.2f} руб
📦 Заказов: {len(orders)}

🎁 Реферальный код: `{user_data['referral_code']}`
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Пополнить баланс", callback_data="add_balance")]
    ]
    
    if user_data['role'] == 'buyer':
        keyboard.append([InlineKeyboardButton("🎯 Стать продавцом", callback_data="request_seller_verification")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💳 *ПОПОЛНЕНИЕ БАЛАНСА*\n\n"
        "Введите сумму для пополнения (в рублях):",
        parse_mode='Markdown'
    )
    
    return BuyerStates.ADD_BALANCE_AMOUNT

async def handle_add_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Неверная сумма. Введите положительное число (например: 500):"
        )
        return BuyerStates.ADD_BALANCE_AMOUNT
    
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    user_data = db.get_user(user_id)
    
    await update.message.reply_text(
        f"✅ *ЗАПРОС НА ПОПОЛНЕНИЕ БАЛАНСА*\n\n"
        f"Сумма: {amount:.2f} руб\n\n"
        f"Ваш запрос отправлен администраторам.\n"
        f"Ожидайте подтверждения.",
        parse_mode='Markdown'
    )
    
    user_name = user_data['username'] or user_data['first_name']
    notification_text = (
        f"💳 *НОВЫЙ ЗАПРОС НА ПОПОЛНЕНИЕ БАЛАНСА*\n\n"
        f"👤 Пользователь: {user_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Сумма: {amount:.2f} руб\n\n"
        f"Текущий баланс: {user_data['balance']:.2f} руб"
    )
    
    for admin_id in config.SUPER_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=notification_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            pass
    
    if config.NOTIFICATION_CHANNEL_ID:
        try:
            await context.bot.send_message(
                chat_id=config.NOTIFICATION_CHANNEL_ID,
                text=notification_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            pass
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_request_seller_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    cursor = db.conn.cursor()
    cursor.execute('''SELECT * FROM verification_requests 
                      WHERE user_id = ? AND status = 'pending' ''', (user_id,))
    pending_request = cursor.fetchone()
    
    if pending_request:
        await query.edit_message_text(
            "⏳ *ЗАЯВКА УЖЕ ОТПРАВЛЕНА*\n\n"
            "У вас уже есть заявка на верификацию в обработке.\n"
            "Пожалуйста, дождитесь решения администратора.",
            parse_mode='Markdown'
        )
        return
    
    db.create_verification_request(user_id)
    
    user_data = db.get_user(user_id)
    user_name = user_data['username'] or user_data['first_name']
    
    await query.edit_message_text(
        "✅ *ЗАЯВКА ОТПРАВЛЕНА*\n\n"
        "Ваша заявка на получение статуса продавца отправлена администраторам.\n"
        "Мы рассмотрим её в ближайшее время и уведомим вас о результате.",
        parse_mode='Markdown'
    )
    
    notification_text = (
        f"🎯 *НОВАЯ ЗАЯВКА НА СТАТУС ПРОДАВЦА*\n\n"
        f"👤 Пользователь: {user_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📞 Телефон: {user_data['phone'] or 'не указан'}\n\n"
        f"Используйте панель администратора для одобрения или отклонения заявки."
    )
    
    for admin_id in config.SUPER_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=notification_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            pass
    
    if config.NOTIFICATION_CHANNEL_ID:
        try:
            await context.bot.send_message(
                chat_id=config.NOTIFICATION_CHANNEL_ID,
                text=notification_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            pass

async def handle_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    cursor = db.conn.cursor()
    cursor.execute('''SELECT p.*, u.username as seller_name
                      FROM favorites f
                      JOIN products p ON f.product_id = p.id
                      JOIN users u ON p.seller_id = u.user_id
                      WHERE f.user_id = ?
                      ORDER BY f.added_at DESC''', (user_id,))
    favorites = cursor.fetchall()
    
    if not favorites:
        await update.message.reply_text("⭐ У вас нет избранных товаров")
        return
    
    text = f"⭐ *ИЗБРАННОЕ* ({len(favorites)})\n\n"
    
    keyboard = []
    for fav in favorites[:20]:
        keyboard.append([InlineKeyboardButton(
            f"📦 {fav['name']} - {fav['price']} руб",
            callback_data=f"view_product_{fav['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """💬 *ТЕХНИЧЕСКАЯ ПОДДЕРЖКА*

Здесь вы можете получить помощь по любым вопросам.

Напишите ваш вопрос, и мы ответим в ближайшее время."""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """ℹ️ *ИНФОРМАЦИЯ О SHOP-Q*

🛍️ SHOP-Q - это маркетплейс виртуальных товаров с привязкой к географическим локациям.

*Основные возможности:*
• Покупка товаров в вашем регионе
• Поиск по каталогу
• Корзина и избранное
• Система рейтингов
• Техподдержка

*Для продавцов:*
• Создание своего магазина
• Добавление товаров
• Управление заказами
• Статистика продаж

По всем вопросам обращайтесь в поддержку."""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    product_id = int(query.data.split('_')[1])
    context.user_data['complaint_product_id'] = product_id
    
    db = context.bot_data['db']
    product = db.get_product(product_id)
    
    if not product:
        await query.answer("❌ Товар не найден", show_alert=True)
        return ConversationHandler.END
    
    seller_name = product['seller_username'] or f"ID{product['seller_id']}"
    await query.edit_message_text(
        f"⚠️ *ЖАЛОБА НА ТОВАР*\n\n"
        f"Товар: {product['name']}\n"
        f"Продавец: {seller_name}\n\n"
        f"Опишите причину жалобы:",
        parse_mode='Markdown'
    )
    return BuyerStates.COMPLAINT_REASON

async def handle_complaint_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text.strip()
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    product_id = context.user_data.get('complaint_product_id')
    product = db.get_product(product_id)
    
    if not product:
        await update.message.reply_text("❌ Товар не найден")
        return ConversationHandler.END
    
    db.add_complaint(
        complainant_id=user_id,
        target_id=product['seller_id'],
        product_id=product_id,
        reason=reason
    )
    
    await update.message.reply_text(
        "✅ *ЖАЛОБА ОТПРАВЛЕНА*\n\n"
        "Ваша жалоба принята и будет рассмотрена администратором.\n"
        "Мы уведомим вас о результатах.",
        parse_mode='Markdown'
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    seller_id = int(query.data.split('_')[1])
    user_id = query.from_user.id
    
    db = context.bot_data['db']
    
    try:
        db.add_subscription(user_id, seller_id)
        await query.answer("✅ Вы подписались на продавца!", show_alert=True)
    except Exception as e:
        await query.answer("❌ Вы уже подписаны на этого продавца", show_alert=True)

async def handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    seller_id = int(query.data.split('_')[1])
    user_id = query.from_user.id
    
    db = context.bot_data['db']
    db.remove_subscription(user_id, seller_id)
    
    await query.answer("✅ Вы отписались от продавца", show_alert=True)

async def handle_view_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    subscriptions = db.get_user_subscriptions(user_id)
    
    if not subscriptions:
        await update.message.reply_text("👥 У вас нет подписок на продавцов")
        return
    
    text = f"👥 *МОИ ПОДПИСКИ* ({len(subscriptions)})\n\n"
    
    keyboard = []
    for sub in subscriptions:
        seller_name = sub['username'] or f"ID{sub['seller_id']}"
        rating = sub.get('avg_rating', 0) or 0
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {seller_name} (⭐ {rating:.1f})",
                callback_data=f"view_seller_{sub['seller_id']}"
            ),
            InlineKeyboardButton("❌ Отписаться", callback_data=f"unsubscribe_{sub['seller_id']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_leave_rating_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.split('_')[-1])
    context.user_data['rating_order_id'] = order_id
    
    db = context.bot_data['db']
    order = db.get_order(order_id)
    
    if not order:
        await query.edit_message_text("❌ Заказ не найден")
        return ConversationHandler.END
    
    if order['buyer_id'] != query.from_user.id:
        await query.edit_message_text("❌ Это не ваш заказ")
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"⭐ *ОСТАВИТЬ ОТЗЫВ*\n\n"
        f"Заказ №{order['order_number']}\n"
        f"Товар: {order['product_name']}\n\n"
        f"Введите оценку от 1.1 до 5.5 (например: 4.5):",
        parse_mode='Markdown'
    )
    return BuyerStates.RATING_VALUE

async def handle_rating_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rating = float(update.message.text.strip().replace(',', '.'))
        if rating < 1.1 or rating > 5.5:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Неверная оценка. Введите число от 1.1 до 5.5\n"
            "Например: 4.5"
        )
        return BuyerStates.RATING_VALUE
    
    context.user_data['rating_value'] = rating
    
    await update.message.reply_text(
        f"✅ Оценка: {rating}\n\n"
        f"Теперь напишите комментарий к отзыву (или напишите 'Пропустить'):"
    )
    return BuyerStates.RATING_COMMENT

async def handle_rating_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comment = update.message.text.strip()
    
    if comment.lower() == 'пропустить':
        comment = ''
    
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    order_id = context.user_data.get('rating_order_id')
    rating_value = context.user_data.get('rating_value')
    
    order = db.get_order(order_id)
    
    if not order:
        await update.message.reply_text("❌ Заказ не найден")
        return ConversationHandler.END
    
    try:
        db.add_rating(
            order_id=order_id,
            buyer_id=user_id,
            seller_id=order['seller_id'],
            product_id=order['product_id'],
            rating=rating_value,
            comment=comment
        )
        
        await update.message.reply_text(
            f"✅ *ОТЗЫВ ОПУБЛИКОВАН*\n\n"
            f"Оценка: {rating_value} ⭐\n"
            f"Комментарий: {comment if comment else '(без комментария)'}\n\n"
            f"Спасибо за отзыв!",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_view_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    product_id = int(query.data.split('_')[1])
    db = context.bot_data['db']
    await query.answer()
    
    cursor = db.conn.cursor()
    cursor.execute('''SELECT r.*, u.username, u.first_name
                      FROM ratings r
                      JOIN users u ON r.buyer_id = u.user_id
                      WHERE r.product_id = ?
                      ORDER BY r.created_at DESC
                      LIMIT 10''', (product_id,))
    reviews = cursor.fetchall()
    
    product = db.get_product(product_id)
    
    if not reviews:
        await query.edit_message_text(
            f"📦 {product['name']}\n\n"
            f"⭐ Пока нет отзывов на этот товар"
        )
        return
    
    text = f"📦 *{product['name']}*\n\n"
    text += f"⭐ Средний рейтинг: {product.get('avg_rating', 0):.1f} ({len(reviews)} отзывов)\n\n"
    
    for idx, review in enumerate(reviews, 1):
        reviewer_name = review['username'] or review['first_name'] or f"Покупатель {review['buyer_id']}"
        text += f"{idx}. *{reviewer_name}*\n"
        text += f"   ⭐ {review['rating']:.1f}\n"
        if review['comment']:
            text += f"   💬 {review['comment']}\n"
        text += "\n"
    
    await query.edit_message_text(text, parse_mode='Markdown')

async def handle_cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено")
    context.user_data.clear()
    return ConversationHandler.END

async def handle_advanced_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    context.user_data.clear()
    
    categories = db.get_categories()
    
    text = """🔎 *РАСШИРЕННЫЙ ПОИСК*

Настройте фильтры для поиска товаров:

Шаг 1/3: Выберите категорию
(или пропустите, чтобы искать во всех категориях)"""
    
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat['name'], callback_data=f"adv_cat_{cat['id']}")])
    
    keyboard.append([InlineKeyboardButton("⏭️ Пропустить", callback_data="adv_skip_category")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return BuyerStates.ADVANCED_SEARCH_CATEGORY

async def handle_advanced_search_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "adv_skip_category":
        context.user_data['search_category_id'] = None
    else:
        category_id = int(query.data.split('_')[2])
        context.user_data['search_category_id'] = category_id
    
    await query.edit_message_text(
        "🔎 *РАСШИРЕННЫЙ ПОИСК*\n\n"
        "Шаг 2/3: Введите минимальную цену (в рублях)\n"
        "Или напишите '0' чтобы не устанавливать минимум:",
        parse_mode='Markdown'
    )
    
    return BuyerStates.ADVANCED_SEARCH_PRICE_MIN

async def handle_advanced_search_price_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price_min = float(update.message.text.strip())
        if price_min < 0:
            raise ValueError()
    except:
        await update.message.reply_text("❌ Неверная цена. Введите число (например: 100):")
        return BuyerStates.ADVANCED_SEARCH_PRICE_MIN
    
    context.user_data['search_price_min'] = price_min if price_min > 0 else None
    
    await update.message.reply_text(
        "🔎 *РАСШИРЕННЫЙ ПОИСК*\n\n"
        "Шаг 3/3: Введите максимальную цену (в рублях)\n"
        "Или напишите '0' чтобы не устанавливать максимум:",
        parse_mode='Markdown'
    )
    
    return BuyerStates.ADVANCED_SEARCH_PRICE_MAX

async def handle_advanced_search_price_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price_max = float(update.message.text.strip())
        if price_max < 0:
            raise ValueError()
    except:
        await update.message.reply_text("❌ Неверная цена. Введите число (например: 1000):")
        return BuyerStates.ADVANCED_SEARCH_PRICE_MAX
    
    context.user_data['search_price_max'] = price_max if price_max > 0 else None
    
    db = context.bot_data['db']
    
    category_id = context.user_data.get('search_category_id')
    price_min = context.user_data.get('search_price_min')
    price_max = context.user_data.get('search_price_max')
    
    try:
        results = db.search_products_advanced(
            category_id=category_id,
            country_id=None,
            city_id=None,
            district_id=None,
            price_min=price_min,
            price_max=price_max,
            status='active'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при поиске товаров. Попробуйте позже.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    if not results:
        await update.message.reply_text(
            "❌ *Товары не найдены*\n\n"
            "Попробуйте изменить параметры поиска.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    text = f"🔎 *РЕЗУЛЬТАТЫ ПОИСКА*\n\n"
    text += f"Найдено товаров: {len(results)}\n\n"
    
    filters = []
    if category_id:
        try:
            cat = next((c for c in db.get_categories() if c['id'] == category_id), None)
            if cat:
                filters.append(f"Категория: {cat['name']}")
        except:
            pass
    if price_min:
        filters.append(f"Цена от {price_min} руб")
    if price_max:
        filters.append(f"Цена до {price_max} руб")
    
    if filters:
        text += "Фильтры: " + ", ".join(filters) + "\n\n"
    
    keyboard = []
    for product in results[:20]:
        keyboard.append([InlineKeyboardButton(
            f"📦 {product['name']} - {product['price']} руб ({product['stock']} шт)",
            callback_data=f"view_product_{product['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(results) > 20:
        text += f"\n_Показано 20 из {len(results)} товаров_"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📋 *ПРАВИЛА ИСПОЛЬЗОВАНИЯ БОТА*

*1. ОБЩИЕ ПРАВИЛА:*
• Запрещено размещение запрещенных товаров
• Запрещена продажа наркотиков, оружия, поддельных документов
• Запрещен обман покупателей и продавцов
• Все сделки должны быть честными

*2. ДЛЯ ПОКУПАТЕЛЕЙ:*
• Оплачивайте товары своевременно
• Оставляйте честные отзывы
• Не создавайте фейковые заказы
• Сообщайте о проблемах в поддержку

*3. ДЛЯ ПРОДАВЦОВ:*
• Размещайте только реальные товары
• Указывайте честные цены и описания
• Отправляйте товары вовремя
• Отвечайте на вопросы покупателей

*4. САНКЦИИ:*
• Предупреждение за первое нарушение
• Блокировка при повторных нарушениях
• Удаление товаров при нарушении правил

*5. СПОРЫ:*
• Обращайтесь в поддержку при конфликтах
• Предоставляйте доказательства
• Решение принимается администратором

❗ Администрация оставляет за собой право изменять правила без предупреждения."""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📞 *КОНТАКТНАЯ ИНФОРМАЦИЯ*

*Техническая поддержка:*
• Telegram: @shop_q_support (пример)
• Email: support@shop-q.com (пример)
• Время работы: 24/7

*Сотрудничество:*
• Email: partner@shop-q.com (пример)
• Telegram: @shop_q_business (пример)

*Реклама и промо:*
• Email: ads@shop-q.com (пример)
• Telegram: @shop_q_ads (пример)

*Юридическая информация:*
• Email: legal@shop-q.com (пример)

*Официальные каналы:*
• Telegram канал: @shop_q_news (пример)
• Чат поддержки: @shop_q_chat (пример)

⚡ Среднее время ответа: 1-24 часа
📧 Срочные вопросы отмечайте как "СРОЧНО"

_Примечание: Это примерные контакты для демонстрации. Замените их на реальные при запуске._"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """❓ *ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ (FAQ)*

*1. Как начать покупать?*
Просто выберите "🏪 Магазины", выберите регион и просматривайте товары продавцов.

*2. Как стать продавцом?*
Нажмите /start и выберите "Менеджер" при первом запуске. Если уже зарегистрированы как покупатель, обратитесь в поддержку.

*3. Как добавить товар?*
В меню менеджера выберите "➕ Добавить товар" и следуйте инструкциям.

*4. Почему мой товар на модерации?*
Все новые товары проходят проверку администратором перед публикацией. Обычно это занимает до 24 часов.

*5. Как оплатить товар?*
Бот поддерживает Bitcoin, Ethereum, карты и наличные. Выберите удобный способ при оформлении заказа.

*6. Что делать если товар не пришел?*
Откройте спор через раздел "📦 Мои заказы" → выберите заказ → "⚠️ Жалоба".

*7. Как вывести деньги?*
Менеджеры могут вывести средства через раздел "💰 Баланс" в меню.

*8. Почему меня заблокировали?*
За нарушение правил бота. Обратитесь в поддержку для разблокировки.

*9. Как связаться с продавцом?*
Через кнопку "💬 Написать" на странице товара или магазина продавца.

*10. Безопасно ли пользоваться ботом?*
Да, но будьте осторожны: проверяйте рейтинги продавцов, не переводите деньги напрямую, используйте функцию споров при проблемах.

_Не нашли ответ? Напишите в 💬 Поддержку!_"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    categories = db.get_categories()
    
    if not categories:
        await update.message.reply_text("📚 Каталог пуст - нет категорий")
        return
    
    text = f"📚 *КАТАЛОГ ТОВАРОВ*\n\n"
    text += f"Выберите категорию для просмотра товаров:\n\n"
    
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            f"📁 {category['name']}",
            callback_data=f"catalog_cat_{category['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("📋 Все товары", callback_data="catalog_all")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_catalog_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    user = db.get_user(user_id)
    
    if query.data == "catalog_all":
        if user['role'] == 'admin':
            products = db.get_all_products(limit=100)
        else:
            products = db.get_all_products(status='active', limit=100)
        category_name = "Все категории"
    else:
        category_id = int(query.data.split('_')[-1])
        
        subcategories = db.get_categories(parent_id=category_id)
        
        if subcategories:
            category = db.get_category_by_id(category_id)
            category_name = category['name'] if category else "Категория"
            
            text = f"📚 *КАТАЛОГ: {category_name.upper()}*\n\n"
            text += f"Выберите подкатегорию:\n\n"
            
            keyboard = []
            for subcat in subcategories:
                keyboard.append([InlineKeyboardButton(
                    f"📁 {subcat['name']}",
                    callback_data=f"catalog_cat_{subcat['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад к категориям", callback_data="catalog_back")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        category = db.conn.cursor()
        category.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
        cat_data = category.fetchone()
        category_name = cat_data['name'] if cat_data else "Неизвестная категория"
        
        if user['role'] == 'admin':
            products = db.conn.cursor().execute(
                'SELECT p.*, u.username as seller_username, u.first_name as seller_first_name FROM products p JOIN users u ON p.seller_id = u.user_id WHERE p.category_id = ? ORDER BY p.created_at DESC LIMIT 100',
                (category_id,)
            ).fetchall()
        else:
            products = db.conn.cursor().execute(
                'SELECT p.*, u.username as seller_username, u.first_name as seller_first_name FROM products p JOIN users u ON p.seller_id = u.user_id WHERE p.category_id = ? AND p.status = "active" ORDER BY p.created_at DESC LIMIT 100',
                (category_id,)
            ).fetchall()
    
    if not products:
        await query.edit_message_text(f"📚 В категории '{category_name}' нет товаров")
        return
    
    text = f"📚 *КАТАЛОГ: {category_name.upper()}*\n\n"
    text += f"Найдено товаров: {len(products)}\n\n"
    
    keyboard = []
    for product in products[:30]:
        status_emoji = ""
        if user['role'] == 'admin':
            status_emoji = {
                'active': '✅ ',
                'inactive': '❌ ',
                'pending': '⏳ ',
                'rejected': '🚫 '
            }.get(product.get('status'), '')
        
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji}{product['name']} - {product['price']} руб",
            callback_data=f"view_product_{product['id']}" if user['role'] in ['buyer', 'manager'] else f"admin_product_{product['id']}"
        )])
    
    if len(products) > 30:
        text += f"_Показано 30 из {len(products)} товаров_\n\n"
    
    keyboard.append([InlineKeyboardButton("◀️ Назад к категориям", callback_data="catalog_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_catalog_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data['db']
    categories = db.get_categories()
    
    if not categories:
        await query.edit_message_text("📚 Каталог пуст - нет категорий")
        return
    
    text = f"📚 *КАТАЛОГ ТОВАРОВ*\n\n"
    text += f"Выберите категорию для просмотра товаров:\n\n"
    
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            f"📁 {category['name']}",
            callback_data=f"catalog_cat_{category['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("📋 Все товары", callback_data="catalog_all")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

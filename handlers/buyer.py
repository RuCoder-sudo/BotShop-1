from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.helpers import escape_markdown
from database import Database
from utils import format_price, format_rating
import config
import os
import logging

logger = logging.getLogger(__name__)

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
    CHECKOUT_NAME = 15
    CHECKOUT_ADDRESS = 16
    CHECKOUT_PHONE = 17

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
            BuyerStates.ADD_BALANCE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_balance_amount),
                CallbackQueryHandler(handle_cancel_balance_input, pattern="^cancel_balance_input$")
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_action),
            CallbackQueryHandler(handle_cancel_balance_input, pattern="^cancel_balance_input$")
        ],
        per_message=False
    )
    
    checkout_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_checkout_start, pattern="^checkout_cart$")],
        states={
            BuyerStates.CHECKOUT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_checkout_name)],
            BuyerStates.CHECKOUT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_checkout_address)],
            BuyerStates.CHECKOUT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_checkout_phone)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel_action)],
        per_message=False
    )
    
    application.add_handler(search_conv)
    application.add_handler(advanced_search_conv)
    application.add_handler(complaint_conv)
    application.add_handler(rating_conv)
    application.add_handler(add_balance_conv)
    application.add_handler(checkout_conv)
    
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
    application.add_handler(CallbackQueryHandler(handle_clear_cart, pattern="^clear_cart$"))
    application.add_handler(CallbackQueryHandler(handle_checkout_confirm, pattern="^checkout_confirm$"))
    application.add_handler(CallbackQueryHandler(handle_checkout_cancel, pattern="^checkout_cancel$"))
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
    application.add_handler(CallbackQueryHandler(handle_balance_confirm, pattern="^balance_confirm_"))
    application.add_handler(CallbackQueryHandler(handle_balance_cancel, pattern="^balance_cancel_"))

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
        try:
            await query.edit_message_text("❌ У этого продавца нет товаров")
        except:
            await query.message.delete()
            await query.message.reply_text("❌ У этого продавца нет товаров")
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
    
    text = (
        f"🛍️ *МАГАЗИН: {seller_data['username'] or seller_data['first_name']}*\n\n"
        f"⭐ Рейтинг: {avg_rating:.1f}\n"
        f"📦 Товаров: {len(seller_products)}\n"
        f"👥 Подписчиков: {subs_count}\n\n"
        f"Выбрать товар!"
    )
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except:
        await query.message.delete()
        await query.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_view_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logger.info(f"handle_view_product called with callback_data: {query.data}")
    await query.answer()
    
    product_id = int(query.data.split('_')[-1])
    logger.info(f"Viewing product ID: {product_id}")
    
    db = context.bot_data['db']
    product = db.get_product(product_id)
    
    if not product:
        await query.edit_message_text("❌ Товар не найден")
        return
    
    seller_rating = db.get_seller_rating(product['seller_id'])
    seller_avg_rating = seller_rating['avg_rating'] if seller_rating['avg_rating'] else 0
    
    safe_name = escape_markdown(product['name'])
    safe_desc = escape_markdown(product['description'] or '')
    safe_category = escape_markdown(product['category_name'] or 'Нет')
    safe_country = escape_markdown(product['country_name'] or '')
    safe_city = escape_markdown(product['city_name'] or '')
    safe_district = escape_markdown(product['district_name'] or '')
    
    text = f"""📦 *{safe_name}*

📝 {safe_desc}

📁 Категория: {safe_category}
📍 Локация: {safe_country}, {safe_city}, {safe_district}

⭐ Рейтинг товара: {product['avg_rating'] or 0:.1f} ({product['rating_count']} отзывов)
⭐ Рейтинг продавца: {seller_avg_rating:.1f}

📊 Остаток: {product['stock']} шт
💵 Цена: {product['price']} руб
"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 В корзину", callback_data=f"add_cart_{product_id}")],
        [InlineKeyboardButton("⭐ В избранное", callback_data=f"add_fav_{product_id}")],
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
    seller_name = escape_markdown(seller['first_name'] or 'Продавец')
    
    if seller_username:
        seller_username_esc = escape_markdown(seller_username)
        text = f"✉️ *НАПИСАТЬ ПРОДАВЦУ*\n\n"
        text += f"Продавец: {seller_name}\n"
        text += f"Username: @{seller_username_esc}\n\n"
        text += f"Вы можете написать продавцу напрямую в Telegram: @{seller_username_esc}"
    else:
        text = f"✉️ *НАПИСАТЬ ПРОДАВЦУ*\n\n"
        text += f"Продавец: {seller_name}\n"
        text += f"ID: `{seller_id}`\n\n"
        text += f"К сожалению, у продавца не указан username.\n"
        text += f"Вы можете связаться с ним через поддержку."
    
    await query.answer("ℹ️ Информация о продавце", show_alert=False)
    try:
        await query.edit_message_text(text, parse_mode='Markdown')
    except:
        await query.message.delete()
        await query.message.reply_text(text, parse_mode='Markdown')

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
        seller_name = item['seller_username'] or item['seller_name'] or item['seller_first_name'] or f"ID{item['seller_id']}"
        text += f"📦 {item['name']}\n"
        text += f"   {item['quantity']} x {item['price']} = {item_total} руб\n"
        text += f"   Продавец: {seller_name}\n"
        text += "─────────────\n"
    
    delivery_price = db.get_delivery_price()
    total_with_delivery = total + delivery_price
    
    text += f"\n📦 *Товар: {total} руб*\n"
    text += f"🚚 *Доставка: {delivery_price} руб*\n"
    text += f"💰 *Итого: {total_with_delivery} руб*"
    
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout_cart")],
        [InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    db.clear_cart(user_id)
    
    await query.edit_message_text("🗑️ Корзина очищена")

async def handle_checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    cart_items = db.get_cart(user_id)
    
    if not cart_items:
        await query.edit_message_text("🛒 Ваша корзина пуста")
        return ConversationHandler.END
    
    user_data = db.get_user(user_id)
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    delivery_price = db.get_delivery_price()
    total_with_delivery = total + delivery_price
    
    if user_data['balance'] < total_with_delivery:
        await query.edit_message_text(
            f"❌ Недостаточно средств на балансе\n\n"
            f"💰 Ваш баланс: {user_data['balance']:.2f} руб\n"
            f"💳 Товар: {total:.2f} руб\n"
            f"🚚 Доставка: {delivery_price:.2f} руб\n"
            f"📉 Не хватает: {total_with_delivery - user_data['balance']:.2f} руб\n\n"
            f"Пополните баланс в профиле",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    context.user_data['checkout_total'] = total
    context.user_data['checkout_delivery'] = delivery_price
    context.user_data['checkout_cart_items'] = [dict(item) for item in cart_items]
    
    await query.edit_message_text(
        "📝 *ОФОРМЛЕНИЕ ЗАКАЗА*\n\n"
        "Шаг 1/3: Введите ваше имя:",
        parse_mode='Markdown'
    )
    
    return BuyerStates.CHECKOUT_NAME

async def handle_checkout_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    
    if len(name) < 2:
        await update.message.reply_text(
            "❌ Имя слишком короткое. Введите ваше имя (минимум 2 символа):"
        )
        return BuyerStates.CHECKOUT_NAME
    
    context.user_data['checkout_name'] = name
    
    await update.message.reply_text(
        f"✅ Имя: {name}\n\n"
        f"Шаг 2/3: Введите адрес доставки:"
    )
    
    return BuyerStates.CHECKOUT_ADDRESS

async def handle_checkout_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    
    if len(address) < 5:
        await update.message.reply_text(
            "❌ Адрес слишком короткий. Введите полный адрес доставки:"
        )
        return BuyerStates.CHECKOUT_ADDRESS
    
    context.user_data['checkout_address'] = address
    
    await update.message.reply_text(
        f"✅ Адрес: {address}\n\n"
        f"Шаг 3/3: Введите номер телефона для связи:"
    )
    
    return BuyerStates.CHECKOUT_PHONE

async def handle_checkout_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    
    if len(phone) < 10:
        await update.message.reply_text(
            "❌ Номер телефона слишком короткий. Введите номер телефона:"
        )
        return BuyerStates.CHECKOUT_PHONE
    
    context.user_data['checkout_phone'] = phone
    
    name = context.user_data.get('checkout_name')
    address = context.user_data.get('checkout_address')
    total = context.user_data.get('checkout_total')
    delivery_price = context.user_data.get('checkout_delivery', 0)
    cart_items = context.user_data.get('checkout_cart_items')
    
    text = (
        f"📋 *ПОДТВЕРЖДЕНИЕ ЗАКАЗА*\n\n"
        f"👤 Имя: {name}\n"
        f"📍 Адрес: {address}\n"
        f"📞 Телефон: {phone}\n\n"
        f"🛒 Товаров: {len(cart_items)} шт\n"
        f"💰 Товары: {total:.2f} руб\n"
        f"🚚 Доставка: {delivery_price:.2f} руб\n"
        f"💳 Итого: {total + delivery_price:.2f} руб\n\n"
        f"Подтвердите оформление заказа:"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="checkout_confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="checkout_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return ConversationHandler.END

async def handle_checkout_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    name = context.user_data.get('checkout_name')
    address = context.user_data.get('checkout_address')
    phone = context.user_data.get('checkout_phone')
    total = context.user_data.get('checkout_total')
    delivery_price = context.user_data.get('checkout_delivery', 0)
    cart_items = context.user_data.get('checkout_cart_items')
    
    if not all([name, address, phone, cart_items]):
        await query.edit_message_text("❌ Ошибка: данные заказа не найдены. Начните оформление заново.")
        context.user_data.clear()
        return
    
    total_with_delivery = total + delivery_price
    
    try:
        for idx, item in enumerate(cart_items):
            db.create_order(
                buyer_id=user_id,
                seller_id=item['seller_id'],
                product_id=item['product_id'],
                quantity=item['quantity'],
                total_price=item['price'] * item['quantity'],
                payment_method='balance',
                delivery_address=address,
                phone=phone,
                buyer_name=name,
                delivery_cost=delivery_price if idx == 0 else 0
            )
        
        db.adjust_user_balance(
            user_id=user_id,
            amount=total_with_delivery,
            transaction_type='debit',
            description='Оплата заказа'
        )
        
        db.clear_cart(user_id)
        
        user_data = db.get_user(user_id)
        
        await query.edit_message_text(
            f"✅ *ЗАКАЗ ПРИНЯТ!*\n\n"
            f"💰 Товары: {total:.2f} руб\n"
            f"🚚 Доставка: {delivery_price:.2f} руб\n"
            f"💳 Списано: {total_with_delivery:.2f} руб\n"
            f"💵 Остаток: {user_data['balance']:.2f} руб\n\n"
            f"Ваш заказ оформлен!\n"
            f"Менеджер свяжется с вами в ближайшее время.\n\n"
            f"Проверить статус можно в разделе '📦 Мои заказы'",
            parse_mode='Markdown'
        )
        
        notification_text = (
            f"🛒 *НОВЫЙ ЗАКАЗ*\n\n"
            f"👤 Покупатель: {name}\n"
            f"📞 Телефон: {phone}\n"
            f"📍 Адрес: {address}\n\n"
            f"🛍️ Товары:\n"
        )
        
        for item in cart_items:
            notification_text += f"  • {item['name']} x{item['quantity']} = {item['price'] * item['quantity']:.2f} руб\n"
        
        notification_text += f"\n💰 Товары: {total:.2f} руб\n"
        notification_text += f"🚚 Доставка: {delivery_price:.2f} руб\n"
        notification_text += f"💳 Итого: {total_with_delivery:.2f} руб"
        
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
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка при оформлении заказа: {str(e)}")
    
    context.user_data.clear()

async def handle_checkout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ Оформление заказа отменено")
    context.user_data.clear()

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
    keyboard = []
    
    for order in orders[:10]:
        text += f"📋 Заказ #{order['order_number']}\n"
        text += f"🛍️ {order['product_name']}\n"
        text += f"💰 {order['total_price']} руб x {order['quantity']}\n"
        text += f"📊 Статус: {order['status']}\n"
        text += f"📅 {order['created_at'][:10]}\n"
        text += "─────────────\n"
        
        if order['status'] in ['pending', 'processing', 'completed']:
            has_rating = db.check_order_has_rating(order['id'])
            if not has_rating:
                keyboard.append([InlineKeyboardButton(
                    f"⭐ Оставить отзыв на заказ #{order['order_number']}", 
                    callback_data=f"leave_rating_{order['id']}"
                )])
    
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
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
    
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_balance_input")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💳 *ПОПОЛНЕНИЕ БАЛАНСА*\n\n"
        "Введите сумму для пополнения (в рублях):\n\n"
        "_Или нажмите 'Отмена' для возврата_",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return BuyerStates.ADD_BALANCE_AMOUNT

async def handle_add_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError()
    except:
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_balance_input")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Неверная сумма. Введите положительное число (например: 500):\n\n"
            "_Или нажмите 'Отмена' для возврата_",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return BuyerStates.ADD_BALANCE_AMOUNT
    
    user_id = update.message.from_user.id
    db = context.bot_data['db']
    
    request_id = db.create_balance_request(user_id, amount)
    context.user_data['balance_request_id'] = request_id
    context.user_data['balance_request_amount'] = amount
    
    keyboard = [
        [InlineKeyboardButton("✅ Пополнил", callback_data=f"balance_confirm_{request_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"balance_cancel_{request_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"💳 *ПОПОЛНЕНИЕ БАЛАНСА*\n\n"
        f"Сумма к пополнению: {amount:.2f} руб\n\n"
        f"Произведите пополнение баланса по номеру карты:\n"
        f"📱 СПб 89246216296\n"
        f"🏦 Ozone Bank\n\n"
        f"После перевода нажмите кнопку '✅ Пополнил'\n"
        f"или '❌ Отмена' для отмены.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_balance_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    request_id = int(query.data.split('_')[-1])
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    request = db.get_balance_request(request_id)
    
    if not request or request['user_id'] != user_id:
        await query.edit_message_text("❌ Запрос не найден или недоступен")
        return
    
    if request['status'] != 'waiting_confirmation':
        await query.edit_message_text("❌ Этот запрос уже обработан")
        return
    
    db.confirm_balance_request(request_id)
    
    await query.edit_message_text(
        f"✅ *ЗАПРОС ОТПРАВЛЕН АДМИНИСТРАТОРУ*\n\n"
        f"Сумма: {request['amount']:.2f} руб\n\n"
        f"Ваш запрос отправлен администраторам на рассмотрение.\n"
        f"Ожидайте подтверждения.",
        parse_mode='Markdown'
    )
    
    user_data = db.get_user(user_id)
    user_name = user_data['username'] or user_data['first_name']
    
    keyboard = [
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_balance_approve_{request_id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_balance_reject_{request_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    notification_text = (
        f"💳 *НОВЫЙ ЗАПРОС НА ПОПОЛНЕНИЕ БАЛАНСА*\n\n"
        f"👤 Пользователь: {user_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Сумма: {request['amount']:.2f} руб\n"
        f"📋 Запрос: #{request_id}\n\n"
        f"Текущий баланс: {user_data['balance']:.2f} руб"
    )
    
    for admin_id in config.SUPER_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=notification_text,
                reply_markup=reply_markup,
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

async def handle_balance_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    request_id = int(query.data.split('_')[-1])
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    request = db.get_balance_request(request_id)
    
    if not request or request['user_id'] != user_id:
        await query.edit_message_text("❌ Запрос не найден")
        return
    
    db.cancel_balance_request(request_id)
    
    await query.edit_message_text("❌ Запрос на пополнение баланса отменен")

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
    safe_name = escape_markdown(product['name'], version=2)
    safe_seller = escape_markdown(str(seller_name), version=2)
    await query.edit_message_text(
        f"⚠️ *ЖАЛОБА НА ТОВАР*\n\n"
        f"Товар: {safe_name}\n"
        f"Продавец: {safe_seller}\n\n"
        f"Опишите причину жалобы:",
        parse_mode='MarkdownV2'
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
        rating = (sub['avg_rating'] if 'avg_rating' in sub and sub['avg_rating'] else 0) or 0
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
    
    safe_product_name = escape_markdown(product['name'], version=2)
    
    if not reviews:
        await query.edit_message_text(
            f"📦 {safe_product_name}\n\n"
            f"⭐ Пока нет отзывов на этот товар",
            parse_mode='MarkdownV2'
        )
        return
    
    text = f"📦 *{safe_product_name}*\n\n"
    avg_rating = product['avg_rating'] if 'avg_rating' in product and product['avg_rating'] else 0
    text += f"⭐ Средний рейтинг: {avg_rating:.1f} \\({len(reviews)} отзывов\\)\n\n"
    
    for idx, review in enumerate(reviews, 1):
        reviewer_name = review['username'] or review['first_name'] or f"Покупатель {review['buyer_id']}"
        safe_reviewer = escape_markdown(str(reviewer_name), version=2)
        text += f"{idx}\\. *{safe_reviewer}*\n"
        text += f"   ⭐ {review['rating']:.1f}\n"
        if review['comment']:
            safe_comment = escape_markdown(str(review['comment']), version=2)
            text += f"   💬 {safe_comment}\n"
        text += "\n"
    
    await query.edit_message_text(text, parse_mode='MarkdownV2')

async def handle_cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено")
    context.user_data.clear()
    return ConversationHandler.END

async def handle_cancel_balance_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Пополнение баланса отменено")
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
    text = """📞 *КОНТАКТЫ*

🥗 Продукты питания • 🍔 Фастфуд • 💄 Косметика • 🛠 Инструменты • 💊 Аптечные товары • 👗 Одежда

Доставляем всё — от хлеба до гардероба! Не нашли нужный товар? Позвоните нам, и мы найдём всё, что вам необходимо.

Ваш город становится ближе!
📞 8-914-101-71-89"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """❓ *ИНСТРУКЦИЯ БОТА - FAQ*

📋 *КАК ЗАКАЗАТЬ ТОВАР*

1️⃣ Выберите "📚 Каталог" или "🏪 Магазины" в главном меню
2️⃣ Просмотрите товары и выберите понравившийся
3️⃣ Нажмите "🛒 В корзину" на странице товара
4️⃣ Перейдите в "🛒 Корзина" из главного меню
5️⃣ Проверьте товары и нажмите "✅ Оформить заказ"
6️⃣ Введите ФИО, адрес доставки и номер телефона
7️⃣ Подтвердите заказ - готово!

💰 *КАК ПОПОЛНИТЬ БАЛАНС*

1️⃣ Перейдите в "👤 Профиль" из главного меню
2️⃣ Нажмите "💰 Пополнить баланс"
3️⃣ Введите сумму пополнения
4️⃣ Подтвердите операцию
5️⃣ Следуйте инструкциям для оплаты
6️⃣ После оплаты средства поступят на ваш баланс

⭐ *КАК ОСТАВИТЬ ОТЗЫВ*

1️⃣ Перейдите в "📦 Мои заказы"
2️⃣ Выберите выполненный заказ
3️⃣ Нажмите "⭐ Оставить отзыв"
4️⃣ Поставьте оценку от 1 до 5
5️⃣ Напишите комментарий (опционально)
6️⃣ Отзыв будет опубликован на странице продавца

🏪 *КАК НАЙТИ МАГАЗИН*

1️⃣ Выберите "🏪 Магазины" в меню
2️⃣ Выберите страну
3️⃣ Выберите город
4️⃣ Выберите район
5️⃣ Просмотрите список продавцов в вашем районе
6️⃣ Нажмите на продавца чтобы увидеть его товары

🔍 *КАК ИСПОЛЬЗОВАТЬ ПОИСК*

1️⃣ Выберите "🔍 Поиск" в меню
2️⃣ Введите название товара
3️⃣ Просмотрите результаты поиска
4️⃣ Выберите нужный товар

⭐ *ИЗБРАННОЕ И ПОДПИСКИ*

• "⭐ Избранное" - сохраняйте понравившиеся товары
• "👥 Мои подписки" - подписывайтесь на продавцов
• Получайте уведомления о новых товарах избранных продавцов

💼 *ДЛЯ ПРОДАВЦОВ*

• При первом запуске выберите "💼 Я продавец"
• Пройдите верификацию (ожидайте подтверждения админа)
• После одобрения получите доступ к панели продавца
• Создавайте товары через "➕ Создать товар"
• Все товары проходят модерацию перед публикацией

📞 *ПОДДЕРЖКА*

Если возникли вопросы или проблемы:
• Нажмите "💬 Поддержка" в меню
• Или позвоните: 8-914-101-71-89

_Приятных покупок!_"""
    
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
            product_status = product['status'] if 'status' in product else 'unknown'
            status_emoji = {
                'active': '✅ ',
                'inactive': '❌ ',
                'pending': '⏳ ',
                'rejected': '🚫 '
            }.get(product_status, '')
        
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji}{product['name']} - {product['price']} руб",
            callback_data=f"view_product_{product['id']}" if user['role'] in ['buyer', 'manager', 'seller'] else f"admin_product_{product['id']}"
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

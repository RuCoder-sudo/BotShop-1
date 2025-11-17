from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from database import Database
from utils import check_manager, format_price
import os

class ManagerStates:
    PRODUCT_NAME = 1
    PRODUCT_DESC = 2
    PRODUCT_PRICE = 3
    PRODUCT_STOCK = 4
    PRODUCT_CATEGORY = 5
    PRODUCT_COUNTRY = 6
    PRODUCT_CITY = 7
    PRODUCT_DISTRICT = 8
    PRODUCT_IMAGE = 9
    EDIT_SELECT_FIELD = 10
    EDIT_VALUE = 11

def setup_manager_handlers(application):
    
    create_product_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Создать товар$"), handle_create_product_start)],
        states={
            ManagerStates.PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_name)],
            ManagerStates.PRODUCT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_description)],
            ManagerStates.PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_price)],
            ManagerStates.PRODUCT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_stock)],
            ManagerStates.PRODUCT_CATEGORY: [CallbackQueryHandler(handle_select_category, pattern="^cat_")],
            ManagerStates.PRODUCT_COUNTRY: [CallbackQueryHandler(handle_select_country, pattern="^country_")],
            ManagerStates.PRODUCT_CITY: [CallbackQueryHandler(handle_select_city, pattern="^city_")],
            ManagerStates.PRODUCT_DISTRICT: [CallbackQueryHandler(handle_select_district, pattern="^district_")],
            ManagerStates.PRODUCT_IMAGE: [
                MessageHandler(filters.PHOTO, handle_product_image),
                MessageHandler(filters.Regex("^Пропустить$"), handle_product_image)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel)],
        per_message=False
    )
    
    edit_product_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_edit_product_start, pattern="^edit_product_")],
        states={
            ManagerStates.EDIT_SELECT_FIELD: [CallbackQueryHandler(handle_edit_field_select, pattern="^edit_field_")],
            ManagerStates.EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_field_value),
                MessageHandler(filters.PHOTO, handle_edit_field_value),
                CallbackQueryHandler(handle_edit_field_value, pattern="^(cat_|country_|city_|district_)")
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel)],
        per_message=False
    )
    
    application.add_handler(create_product_conv)
    application.add_handler(edit_product_conv)
    application.add_handler(MessageHandler(filters.Regex("^📦 Мои товары$"), handle_my_products))
    application.add_handler(CallbackQueryHandler(handle_view_my_product, pattern="^my_product_"))
    application.add_handler(CallbackQueryHandler(handle_delete_my_product, pattern="^delete_my_product_"))
    application.add_handler(CallbackQueryHandler(handle_confirm_delete_product, pattern="^confirm_delete_"))
    application.add_handler(MessageHandler(filters.Regex("^🧾 Продажи$"), handle_sales))
    application.add_handler(MessageHandler(filters.Regex("^📊 Статистика$"), handle_manager_statistics))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ Информация$"), handle_manager_info))
    application.add_handler(MessageHandler(filters.Regex("^💬 Поддержка$"), handle_manager_support))
    application.add_handler(MessageHandler(filters.Regex("^📋 Правила$"), handle_manager_rules))
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), handle_manager_contacts))
    application.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), handle_manager_faq))
    application.add_handler(MessageHandler(filters.Regex("^🌍 Локации и категории$"), handle_manager_locations_categories))
    

async def handle_create_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db = context.bot_data['db']
    
    user_data = db.get_user(user.id)
    if not user_data or (user_data['role'] != 'manager' and user_data['role'] != 'admin'):
        await update.message.reply_text("❌ У вас нет прав продавца или администратора")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 *СОЗДАНИЕ НОВОГО ТОВАРА*\n\n"
        "Шаг 1/8: Введите название товара:",
        parse_mode='Markdown'
    )
    return ManagerStates.PRODUCT_NAME

async def handle_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    
    if len(name) < 3:
        await update.message.reply_text("❌ Название слишком короткое. Минимум 3 символа.")
        return ManagerStates.PRODUCT_NAME
    
    context.user_data['product_name'] = name
    
    await update.message.reply_text(
        f"✅ Название: {name}\n\n"
        "Шаг 2/8: Введите описание товара:"
    )
    return ManagerStates.PRODUCT_DESC

async def handle_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    
    if len(desc) < 10:
        await update.message.reply_text("❌ Описание слишком короткое. Минимум 10 символов.")
        return ManagerStates.PRODUCT_DESC
    
    context.user_data['product_desc'] = desc
    
    await update.message.reply_text(
        "Шаг 3/8: Введите цену товара (только число):"
    )
    return ManagerStates.PRODUCT_PRICE

async def handle_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.strip())
        if price <= 0:
            raise ValueError()
    except:
        await update.message.reply_text("❌ Неверная цена. Введите положительное число.")
        return ManagerStates.PRODUCT_PRICE
    
    context.user_data['product_price'] = price
    
    await update.message.reply_text(
        f"✅ Цена: {price} руб\n\n"
        "Шаг 4/8: Введите количество товара (остаток):"
    )
    return ManagerStates.PRODUCT_STOCK

async def handle_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stock = int(update.message.text.strip())
        if stock < 0:
            raise ValueError()
    except:
        await update.message.reply_text("❌ Неверное количество. Введите целое число.")
        return ManagerStates.PRODUCT_STOCK
    
    context.user_data['product_stock'] = stock
    
    db = context.bot_data['db']
    categories = db.get_categories()
    
    if not categories:
        await update.message.reply_text("❌ Нет доступных категорий. Обратитесь к администратору.")
        return ConversationHandler.END
    
    keyboard = []
    for cat in categories:
        subcats = db.get_categories(cat['id'])
        count_text = f" ({len(subcats)})" if subcats else ""
        keyboard.append([InlineKeyboardButton(f"📁 {cat['name']}{count_text}", callback_data=f"cat_{cat['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Шаг 5/8: Выберите категорию товара:",
        reply_markup=reply_markup
    )
    return ManagerStates.PRODUCT_CATEGORY

async def handle_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cat_back":
        db = context.bot_data['db']
        categories = db.get_categories()
        
        keyboard = []
        for cat in categories:
            subcats = db.get_categories(cat['id'])
            count_text = f" ({len(subcats)})" if subcats else ""
            keyboard.append([InlineKeyboardButton(f"📁 {cat['name']}{count_text}", callback_data=f"cat_{cat['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Шаг 5/8: Выберите категорию товара:",
            reply_markup=reply_markup
        )
        return ManagerStates.PRODUCT_CATEGORY
    
    if query.data.startswith("cat_final_"):
        category_id = int(query.data.split('_')[2])
    else:
        category_id = int(query.data.split('_')[1])
    
    db = context.bot_data['db']
    
    if query.data.startswith("cat_final_"):
        context.user_data['product_category'] = category_id
        
        countries = db.get_countries()
        
        if not countries:
            await query.edit_message_text("❌ Нет доступных стран. Обратитесь к администратору.")
            return ConversationHandler.END
        
        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(country['name'], callback_data=f"country_{country['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        path = db.get_category_path(category_id)
        path_text = " / ".join([c['name'] for c in path])
        
        await query.edit_message_text(
            f"✅ Категория: {path_text}\n\nШаг 6/8: Выберите страну:",
            reply_markup=reply_markup
        )
        return ManagerStates.PRODUCT_COUNTRY
    
    subcategories = db.get_categories(category_id)
    
    if subcategories:
        keyboard = []
        category = db.get_category_by_id(category_id)
        path = db.get_category_path(category_id)
        path_text = " / ".join([c['name'] for c in path])
        
        for subcat in subcategories:
            subsubcats = db.get_categories(subcat['id'])
            count_text = f" ({len(subsubcats)})" if subsubcats else ""
            keyboard.append([InlineKeyboardButton(f"📁 {subcat['name']}{count_text}", callback_data=f"cat_{subcat['id']}")])
        
        keyboard.append([InlineKeyboardButton("✅ Выбрать эту категорию", callback_data=f"cat_final_{category_id}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="cat_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📁 Текущий путь: {path_text}\n\nВыберите подкатегорию или завершите выбор:",
            reply_markup=reply_markup
        )
        return ManagerStates.PRODUCT_CATEGORY
    else:
        context.user_data['product_category'] = category_id
        
        countries = db.get_countries()
        
        if not countries:
            await query.edit_message_text("❌ Нет доступных стран. Обратитесь к администратору.")
            return ConversationHandler.END
        
        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(country['name'], callback_data=f"country_{country['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        path = db.get_category_path(category_id)
        path_text = " / ".join([c['name'] for c in path])
        
        await query.edit_message_text(
            f"✅ Категория: {path_text}\n\nШаг 6/8: Выберите страну:",
            reply_markup=reply_markup
        )
        return ManagerStates.PRODUCT_COUNTRY

async def handle_select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    country_id = int(query.data.split('_')[1])
    context.user_data['product_country'] = country_id
    
    db = context.bot_data['db']
    cities = db.get_cities(country_id)
    
    if not cities:
        await query.edit_message_text("❌ В этой стране нет городов. Обратитесь к администратору.")
        return ConversationHandler.END
    
    keyboard = []
    for city in cities:
        keyboard.append([InlineKeyboardButton(city['name'], callback_data=f"city_{city['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Шаг 7/8: Выберите город:",
        reply_markup=reply_markup
    )
    return ManagerStates.PRODUCT_CITY

async def handle_select_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    city_id = int(query.data.split('_')[1])
    context.user_data['product_city'] = city_id
    
    db = context.bot_data['db']
    districts = db.get_districts(city_id)
    
    if not districts:
        await query.edit_message_text("❌ В этом городе нет районов. Обратитесь к администратору.")
        return ConversationHandler.END
    
    keyboard = []
    for district in districts:
        keyboard.append([InlineKeyboardButton(district['name'], callback_data=f"district_{district['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Шаг 8/8: Выберите район:",
        reply_markup=reply_markup
    )
    return ManagerStates.PRODUCT_DISTRICT

async def handle_select_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    district_id = int(query.data.split('_')[1])
    context.user_data['product_district'] = district_id
    
    await query.edit_message_text(
        "Шаг 9/9 (опционально): Отправьте фото товара или напишите 'Пропустить'"
    )
    return ManagerStates.PRODUCT_IMAGE

async def handle_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    user = update.message.from_user
    
    image_path = None
    
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        os.makedirs('images/products', exist_ok=True)
        image_path = f"images/products/{user.id}_{photo.file_id}.jpg"
        await file.download_to_drive(image_path)
    
    try:
        product_id = db.add_product(
            seller_id=user.id,
            name=context.user_data['product_name'],
            description=context.user_data['product_desc'],
            price=context.user_data['product_price'],
            stock=context.user_data['product_stock'],
            category_id=context.user_data['product_category'],
            country_id=context.user_data['product_country'],
            city_id=context.user_data['product_city'],
            district_id=context.user_data['product_district'],
            image_path=image_path
        )
        
        await update.message.reply_text(
            f"✅ *ТОВАР СОЗДАН!*\n\n"
            f"📦 ID: {product_id}\n"
            f"📝 Название: {context.user_data['product_name']}\n"
            f"💰 Цена: {context.user_data['product_price']} руб\n"
            f"📊 Остаток: {context.user_data['product_stock']} шт",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при создании товара: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db = context.bot_data['db']
    
    products = db.get_seller_products(user.id)
    
    if not products:
        await update.message.reply_text("📦 У вас пока нет товаров")
        return
    
    text = f"📦 *ВАШИ ТОВАРЫ* ({len(products)})\n\n"
    text += "Нажмите на товар для просмотра и редактирования:\n\n"
    
    keyboard = []
    for product in products[:20]:
        status_emoji = "✅" if product['status'] == 'active' else "❌"
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {product['name']} - {product['price']} руб ({product['stock']} шт)", 
            callback_data=f"my_product_{product['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(products) > 20:
        text += f"\n_Показано 20 из {len(products)} товаров_"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db = context.bot_data['db']
    
    orders = db.get_user_orders(user.id, role='seller')
    
    if not orders:
        await update.message.reply_text("🧾 У вас пока нет продаж")
        return
    
    text = f"🧾 *ВАШИ ПРОДАЖИ* ({len(orders)})\n\n"
    
    for order in orders[:10]:
        text += f"📦 Заказ #{order['order_number']}\n"
        text += f"🛍️ {order['product_name']}\n"
        text += f"💰 {order['total_price']} руб\n"
        text += f"📊 Статус: {order['status']}\n"
        text += "─────────────\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_manager_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db = context.bot_data['db']
    
    products = db.get_seller_products(user.id)
    orders = db.get_user_orders(user.id, role='seller')
    rating_data = db.get_seller_rating(user.id)
    
    user_data = db.get_user(user.id)
    
    completed_orders = [o for o in orders if o['status'] == 'completed']
    total_revenue = sum(o['total_price'] for o in completed_orders)
    
    avg_rating = rating_data['avg_rating'] if rating_data['avg_rating'] else 0
    rating_count = rating_data['rating_count']
    
    text = f"""📊 *ВАША СТАТИСТИКА*

📦 Товаров: {len(products)}
🧾 Заказов: {len(orders)}
✅ Выполнено: {len(completed_orders)}
💰 Выручка: {total_revenue:.2f} руб
💳 Баланс: {user_data['balance']:.2f} руб

⭐ Рейтинг: {avg_rating:.1f} ({rating_count} отзывов)
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено")
    context.user_data.clear()
    return ConversationHandler.END

async def handle_manager_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """ℹ️ *ИНФОРМАЦИЯ ДЛЯ ПРОДАВЦОВ*

*SHOP-Q* - маркетплейс виртуальных товаров с географической привязкой.

*Ваши возможности как продавца:*

📦 **Управление товарами:**
• Создание и редактирование товаров
• Привязка к локации (страна-город-район)
• Загрузка изображений
• Управление остатками и ценами

💰 **Финансы:**
• Отслеживание продаж в реальном времени
• Просмотр баланса и истории транзакций
• Статистика по категориям товаров

⭐ **Репутация:**
• Система рейтингов от покупателей
• Отзывы и комментарии
• Рост доверия = рост продаж

📊 **Аналитика:**
• Статистика по товарам
• История заказов
• Популярные позиции

*Советы для успешных продаж:*
✅ Добавляйте качественные фото
✅ Подробно описывайте товар
✅ Актуализируйте остатки
✅ Быстро отвечайте покупателям
✅ Поддерживайте высокий рейтинг

По вопросам обращайтесь в поддержку! 💬"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_manager_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """💬 *ТЕХНИЧЕСКАЯ ПОДДЕРЖКА*

*Как мы можем помочь:*

🔧 **Технические вопросы:**
• Проблемы с загрузкой товаров
• Ошибки в работе бота
• Вопросы по функционалу

💳 **Финансовые вопросы:**
• Вывод средств
• Балансы и комиссии

📦 **Работа с заказами:**
• Управление статусами
• Споры с покупателями
• Возвраты

⭐ **Рейтинги и отзывы:**
• Несправедливые отзывы
• Оспаривание рейтинга
• Жалобы

*Способы связи:*
• Напишите сообщение здесь, в боте
• Администратор ответит в течение 24 часов
• Срочные вопросы помечайте как "СРОЧНО"

Опишите вашу проблему подробно, и мы обязательно поможем!"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_view_my_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[-1])
    db = context.bot_data['db']
    
    product = db.get_product(product_id)
    
    if not product or product['seller_id'] != query.from_user.id:
        await query.edit_message_text("❌ Товар не найден")
        return
    
    status_text = {
        'active': '✅ Активен',
        'inactive': '❌ Неактивен',
        'pending': '⏳ На модерации',
        'rejected': '🚫 Отклонен'
    }.get(product['status'], product['status'])
    
    text = f"""📦 *{product['name']}*

📝 Описание: {product['description']}

💰 Цена: {product['price']} руб
📊 Остаток: {product['stock']} шт
📁 Категория: {product['category_name'] or 'Нет'}
📍 Локация: {product['country_name']}, {product['city_name']}, {product['district_name']}

📌 Статус: {status_text}
⭐ Рейтинг: {product['avg_rating'] or 0:.1f} ({product['rating_count']} отзывов)

🕐 Создан: {product['created_at'][:10]}
🕑 Обновлен: {product['updated_at'][:10]}"""
    
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_product_{product_id}")],
        [InlineKeyboardButton("🗑️ Удалить товар", callback_data=f"delete_my_product_{product_id}")],
        [InlineKeyboardButton("◀️ Назад к списку", callback_data="back_to_my_products")]
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
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_edit_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[-1])
    db = context.bot_data['db']
    
    product = db.get_product(product_id)
    
    if not product or product['seller_id'] != query.from_user.id:
        await query.edit_message_text("❌ Товар не найден")
        return ConversationHandler.END
    
    context.user_data['editing_product_id'] = product_id
    context.user_data['product_data'] = dict(product)
    
    keyboard = [
        [InlineKeyboardButton("📝 Название", callback_data="edit_field_name")],
        [InlineKeyboardButton("📄 Описание", callback_data="edit_field_description")],
        [InlineKeyboardButton("💰 Цена", callback_data="edit_field_price")],
        [InlineKeyboardButton("📊 Остаток", callback_data="edit_field_stock")],
        [InlineKeyboardButton("📁 Категория", callback_data="edit_field_category")],
        [InlineKeyboardButton("📍 Локация", callback_data="edit_field_location")],
        [InlineKeyboardButton("🖼️ Изображение", callback_data="edit_field_image")],
        [InlineKeyboardButton("◀️ Отмена", callback_data="back_to_my_product")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✏️ *РЕДАКТИРОВАНИЕ ТОВАРА*\n\n"
        f"📦 {product['name']}\n\n"
        f"Выберите, что хотите изменить:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ManagerStates.EDIT_SELECT_FIELD

async def handle_edit_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_my_product":
        product_id = context.user_data.get('editing_product_id')
        context.user_data.clear()
        await handle_view_my_product(update, context)
        return ConversationHandler.END
    
    field = query.data.split('_')[-1]
    context.user_data['editing_field'] = field
    
    db = context.bot_data['db']
    product = context.user_data.get('product_data')
    
    if field == 'name':
        await query.edit_message_text(
            f"📝 *Изменение названия*\n\n"
            f"Текущее: {product['name']}\n\n"
            f"Введите новое название:",
            parse_mode='Markdown'
        )
    elif field == 'description':
        await query.edit_message_text(
            f"📄 *Изменение описания*\n\n"
            f"Текущее: {product['description']}\n\n"
            f"Введите новое описание:",
            parse_mode='Markdown'
        )
    elif field == 'price':
        await query.edit_message_text(
            f"💰 *Изменение цены*\n\n"
            f"Текущая: {product['price']} руб\n\n"
            f"Введите новую цену:",
            parse_mode='Markdown'
        )
    elif field == 'stock':
        await query.edit_message_text(
            f"📊 *Изменение остатка*\n\n"
            f"Текущий: {product['stock']} шт\n\n"
            f"Введите новый остаток:",
            parse_mode='Markdown'
        )
    elif field == 'category':
        categories = db.get_categories()
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat['id']}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📁 *Изменение категории*\n\n"
            f"Текущая: {product['category_name']}\n\n"
            f"Выберите новую категорию:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif field == 'location':
        countries = db.get_countries()
        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(country['name'], callback_data=f"country_{country['id']}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📍 *Изменение локации*\n\n"
            f"Текущая: {product['country_name']}, {product['city_name']}, {product['district_name']}\n\n"
            f"Шаг 1/3: Выберите страну:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif field == 'image':
        await query.edit_message_text(
            f"🖼️ *Изменение изображения*\n\n"
            f"Отправьте новое фото товара:",
            parse_mode='Markdown'
        )
    
    return ManagerStates.EDIT_VALUE

async def handle_edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    product_id = context.user_data.get('editing_product_id')
    field = context.user_data.get('editing_field')
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if field == 'category':
            category_id = int(query.data.split('_')[1])
            success = db.update_product(product_id, category_id=category_id)
            
            if success:
                await query.edit_message_text("✅ Категория успешно изменена!")
            else:
                await query.edit_message_text("❌ Ошибка при изменении категории")
            
            context.user_data.clear()
            return ConversationHandler.END
        
        elif field == 'location':
            if query.data.startswith('country_'):
                country_id = int(query.data.split('_')[1])
                context.user_data['new_country_id'] = country_id
                
                cities = db.get_cities(country_id)
                keyboard = []
                for city in cities:
                    keyboard.append([InlineKeyboardButton(city['name'], callback_data=f"city_{city['id']}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "Шаг 2/3: Выберите город:",
                    reply_markup=reply_markup
                )
                return ManagerStates.EDIT_VALUE
            
            elif query.data.startswith('city_'):
                city_id = int(query.data.split('_')[1])
                context.user_data['new_city_id'] = city_id
                
                districts = db.get_districts(city_id)
                keyboard = []
                for district in districts:
                    keyboard.append([InlineKeyboardButton(district['name'], callback_data=f"district_{district['id']}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "Шаг 3/3: Выберите район:",
                    reply_markup=reply_markup
                )
                return ManagerStates.EDIT_VALUE
            
            elif query.data.startswith('district_'):
                district_id = int(query.data.split('_')[1])
                country_id = context.user_data.get('new_country_id')
                city_id = context.user_data.get('new_city_id')
                
                success = db.update_product(product_id, 
                                           country_id=country_id,
                                           city_id=city_id,
                                           district_id=district_id)
                
                if success:
                    await query.edit_message_text("✅ Локация успешно изменена!")
                else:
                    await query.edit_message_text("❌ Ошибка при изменении локации")
                
                context.user_data.clear()
                return ConversationHandler.END
    
    else:
        if update.message.photo:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            os.makedirs('images/products', exist_ok=True)
            image_path = f"images/products/{update.message.from_user.id}_{photo.file_id}.jpg"
            await file.download_to_drive(image_path)
            
            success = db.update_product(product_id, image_path=image_path)
            
            if success:
                await update.message.reply_text("✅ Изображение успешно изменено!")
            else:
                await update.message.reply_text("❌ Ошибка при изменении изображения")
            
            context.user_data.clear()
            return ConversationHandler.END
        
        value = update.message.text.strip()
        
        try:
            if field == 'name':
                if len(value) < 3:
                    await update.message.reply_text("❌ Название слишком короткое. Минимум 3 символа.")
                    return ManagerStates.EDIT_VALUE
                success = db.update_product(product_id, name=value)
            
            elif field == 'description':
                if len(value) < 10:
                    await update.message.reply_text("❌ Описание слишком короткое. Минимум 10 символов.")
                    return ManagerStates.EDIT_VALUE
                success = db.update_product(product_id, description=value)
            
            elif field == 'price':
                price = float(value)
                if price <= 0:
                    raise ValueError()
                success = db.update_product(product_id, price=price)
            
            elif field == 'stock':
                stock = int(value)
                if stock < 0:
                    raise ValueError()
                success = db.update_product(product_id, stock=stock)
            
            else:
                await update.message.reply_text("❌ Неизвестное поле")
                context.user_data.clear()
                return ConversationHandler.END
            
            if success:
                await update.message.reply_text("✅ Изменения сохранены!")
            else:
                await update.message.reply_text("❌ Ошибка при сохранении")
        
        except ValueError:
            await update.message.reply_text("❌ Неверное значение. Попробуйте еще раз.")
            return ManagerStates.EDIT_VALUE
        
        context.user_data.clear()
        return ConversationHandler.END

async def handle_delete_my_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[-1])
    context.user_data['deleting_product_id'] = product_id
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_yes_{product_id}"),
         InlineKeyboardButton("❌ Отмена", callback_data=f"confirm_delete_no_{product_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚠️ *ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ*\n\n"
        "Вы уверены, что хотите удалить этот товар?\n"
        "Это действие нельзя отменить!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_confirm_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[2]
    product_id = int(query.data.split('_')[-1])
    
    db = context.bot_data['db']
    
    if action == 'yes':
        product = db.get_product(product_id)
        
        if not product or product['seller_id'] != query.from_user.id:
            await query.edit_message_text("❌ Товар не найден или у вас нет прав на его удаление")
            return
        
        if db.delete_product(product_id):
            await query.edit_message_text("✅ Товар успешно удален!")
        else:
            await query.edit_message_text("❌ Ошибка при удалении товара")
    else:
        await handle_view_my_product(update, context)

async def handle_manager_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📋 *ПРАВИЛА ДЛЯ ПРОДАВЦОВ*

*1. РАЗМЕЩЕНИЕ ТОВАРОВ:*
• Размещайте только реальные товары
• Указывайте честные цены и описания
• Загружайте качественные фотографии
• Все товары проходят модерацию

*2. ОБРАБОТКА ЗАКАЗОВ:*
• Отправляйте товары в течение 24-48 часов
• Отвечайте на сообщения покупателей
• Обновляйте статусы заказов своевременно

*3. ЗАПРЕТЫ:*
• Запрещена продажа нелегальных товаров
• Запрещен обман покупателей
• Запрещено накручивание рейтинга
• Запрещены фейковые товары

*4. САНКЦИИ:*
• Предупреждение за первое нарушение
• Блокировка при повторных нарушениях
• Удаление всех товаров при серьезных нарушениях

Соблюдение правил - залог успешной работы!"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_manager_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📞 *КОНТАКТЫ ДЛЯ ПРОДАВЦОВ*

*Поддержка продавцов:*
• Telegram: @shop_q_sellers (пример)
• Email: sellers@shop-q.com (пример)
• Время работы: 24/7

*Технические вопросы:*
• Проблемы с загрузкой товаров
• Ошибки в работе бота
• Вопросы по функционалу

*Финансы:*
• Email: finance@shop-q.com (пример)
• Вопросы о выплатах и балансе

*Партнерская программа:*
• Email: partner@shop-q.com (пример)

⚡ Среднее время ответа: 1-12 часов"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_manager_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """❓ *FAQ ДЛЯ ПРОДАВЦОВ*

*1. Как добавить товар?*
Нажмите "➕ Добавить товар" и следуйте инструкциям.

*2. Почему товар на модерации?*
Все новые товары проверяются администратором. Обычно это занимает до 24 часов.

*3. Как редактировать товар?*
"📦 Мои товары" → выберите товар → "✏️ Редактировать".

*4. Как получить деньги?*
Нажмите "💰 Баланс" и выберите способ вывода.

*5. Как повысить продажи?*
- Качественные фото товаров
- Детальные описания
- Конкурентные цены
- Быстрая обработка заказов
- Положительные отзывы

*6. Что делать при споре?*
Свяжитесь с поддержкой через "💬 Поддержка".

*7. Как удалить товар?*
"📦 Мои товары" → товар → "🗑️ Удалить товар".

*8. Комиссия платформы?*
Уточните в поддержке актуальные тарифы."""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_manager_locations_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    user_id = update.message.from_user.id
    
    user = db.get_user(user_id)
    if not user or user['role'] != 'manager':
        await update.message.reply_text("❌ У вас нет прав продавца")
        return
    
    countries = db.get_countries()
    categories = db.get_categories()
    
    text = """🌍 *ЛОКАЦИИ И КАТЕГОРИИ*

📊 *Доступные локации:*
"""
    
    if countries:
        for country in countries[:10]:
            cities = db.get_cities(country['id'])
            text += f"• {country['name']} ({len(cities)} городов)\n"
    else:
        text += "• Локаций пока нет\n"
    
    text += "\n📁 *Доступные категории:*\n"
    
    if categories:
        for cat in categories[:20]:
            text += f"• {cat['name']}\n"
    else:
        text += "• Категорий пока нет\n"
    
    text += "\nℹ️ Для добавления новых локаций и категорий обратитесь к администратору."
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_manager_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db = context.bot_data['db']
    
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("❌ Профиль не найден")
        return
    
    products = db.get_seller_products(user.id)
    product_count = len(products)
    active_count = len([p for p in products if p['status'] == 'active'])
    rating_data = db.get_seller_rating(user.id)
    avg_rating = rating_data['avg_rating'] if rating_data and rating_data['avg_rating'] else 0
    rating_count = rating_data['rating_count'] if rating_data else 0
    
    text = f"""👤 *ПРОФИЛЬ ПРОДАВЦА*

*Личная информация:*
• Имя: {user_data['first_name']}
• Username: @{user_data['username'] or 'не указан'}
• ID: `{user.id}`
• Статус: Продавец ✅

*Статистика:*
• Товаров всего: {product_count}
• Активных товаров: {active_count}
• Баланс: {user_data['balance']:.2f} руб

*Рейтинг:*
• Средний рейтинг: {avg_rating:.1f} ⭐
• Отзывов: {rating_count}

*Аккаунт создан:* {user_data['created_at'][:10] if user_data.get('created_at') else 'неизвестно'}
*Последняя активность:* {user_data['last_active'][:16] if user_data.get('last_active') else 'неизвестно'}

💼 Продолжайте добавлять качественные товары для повышения продаж!"""
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("💳 Пополнить баланс", callback_data="add_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

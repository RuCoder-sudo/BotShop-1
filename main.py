import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)

import config
from database import Database
from handlers.start import handle_start, handle_role_selection, handle_back_to_role_selection
from handlers.admin import setup_admin_handlers
from handlers.manager import setup_manager_handlers
from handlers.buyer import setup_buyer_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shop_q.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context):
    db = context.bot_data['db']
    await handle_start(update, context, db)

async def role_selection_callback(update: Update, context):
    db = context.bot_data['db']
    bot = context.bot
    await handle_role_selection(update, context, db, bot)

async def back_to_role_callback(update: Update, context):
    db = context.bot_data['db']
    await handle_back_to_role_selection(update, context, db)

def main():
    logger.info("🚀 Запуск SHOP-Q бота...")
    
    db = Database()
    logger.info("✅ База данных инициализирована")
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    application.bot_data['db'] = db
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(role_selection_callback, pattern="^role_"))
    application.add_handler(CallbackQueryHandler(back_to_role_callback, pattern="^back_to_role_selection$"))
    
    setup_admin_handlers(application)
    setup_manager_handlers(application)
    setup_buyer_handlers(application)
    
    logger.info("✅ Все обработчики зарегистрированы")
    logger.info(f"🤖 Бот запущен! Админы: {config.SUPER_ADMIN_IDS}")
    logger.info(f"📢 Канал уведомлений: {config.NOTIFICATION_CHANNEL_ID}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    db.close()
    logger.info("👋 Бот остановлен")

if __name__ == '__main__':
    main()

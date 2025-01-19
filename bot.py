from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from handlers import start, search_medicine, cancel, button_handler, handle_price_limit, handle_dosage_limit, handle_tablets_limit, SEARCH, WAITING_FOR_PRICE, WAITING_FOR_DOSAGE, WAITING_FOR_TABLETS
import logging

# Настройка логирования для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    from config import BOT_TOKEN
    
    # Создаем приложение бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настройка ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_medicine),
                CallbackQueryHandler(button_handler)
            ],
            WAITING_FOR_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_limit)
            ],
            WAITING_FOR_DOSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dosage_limit)
            ],
            WAITING_FOR_TABLETS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tablets_limit)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False  # Устанавливаем False для поддержки разных типов обработчиков
    )
    
    # Добавляем обработчики в приложение
    application.add_handler(conv_handler)
    
    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == '__main__':
    main()
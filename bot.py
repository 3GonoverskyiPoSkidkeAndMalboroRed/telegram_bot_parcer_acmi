from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from handlers import start, search_medicine, cancel, button_handler, SEARCH

def main():
    print("Бот запущен...")
    from config import BOT_TOKEN
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Основной обработчик для сообщений
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_medicine)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False  # Отключаем per_message для обычных сообщений
    )
    
    # Отдельный обработчик для кнопок навигации
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Добавляем основной обработчик
    application.add_handler(conv_handler)
    
    application.run_polling()

if __name__ == '__main__':
    main()
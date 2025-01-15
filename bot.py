from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from handlers import start, search_medicine, cancel
from config import BOT_TOKEN
import requests

SEARCH = 1  # Состояние для ожидания ввода названия препарата

def main():
    print("Бот запущен...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создаем ConversationHandler для управления диалогом
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_medicine)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling(stop_signals=None)

if __name__ == '__main__':
    main()
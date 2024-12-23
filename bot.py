from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import start, send_command, handle_image
from config import BOT_TOKEN

def main():
    print("Бот запущен...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send_command))  # Команда для начала отправки фото
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))  # Обработчик изображений
    application.run_polling(stop_signals=None)

if __name__ == '__main__':
    main()
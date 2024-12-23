import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from PIL import Image, ImageDraw, ImageFont
import io

# Ваш токен бота
BOT_TOKEN = '7376088476:AAEWoyTXmpp_PfHBohLg_4vN7OQRKpIhWSA'
CHANNEL_ID = '@testNeveropv'  # Приватный канал
user_last_photo_time = {}
DEFAULT_CAPTION = "Добавьте свой текст"

# Функция для обработки команды /send
async def send_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Пожалуйста, отправьте изображение.")
    context.user_data['awaiting_photo'] = True  # Устанавливаем флаг ожидания фото

# Функция для обработки изображений
async def handle_image(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_photo', False):  # Проверяем флаг ожидания
        photo = update.message.photo[-1]
        caption = DEFAULT_CAPTION
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo.file_id,
            caption=caption
        )
        await update.message.reply_text("Изображение отправлено в канал!")
        context.user_data['awaiting_photo'] = False  # Сбрасываем флаг
    else:
        await update.message.reply_text("Сначала введите команду /send, чтобы отправить изображение.")

# Функция для старта
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Введите команду /send, чтобы отправить изображение в канал.")

def main():
    print("Бот запущен...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send_command))  # Команда для начала отправки фото
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))  # Обработчик изображений
    application.run_polling(stop_signals=None)

if __name__ == '__main__':
    main()
# handlers.py

from telegram import Update
from telegram.ext import CallbackContext
from config import CHANNEL_ID

# Функция для обработки команды /send
async def send_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Пожалуйста, отправьте изображение.")
    context.user_data['awaiting_photo'] = True  # Устанавливаем флаг ожидания фото

# Функция для обработки изображений
async def handle_image(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_photo', False):  # Проверяем флаг ожидания
        photo = update.message.photo[-1]
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo.file_id
        )
        await update.message.reply_text("Изображение отправлено в канал!")
        context.user_data['awaiting_photo'] = False  # Сбрасываем флаг
    else:
        await update.message.reply_text("Сначала введите команду /send, чтобы отправить изображение.")

# Функция для старта
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Введите команду /send, чтобы отправить изображение в канал.")
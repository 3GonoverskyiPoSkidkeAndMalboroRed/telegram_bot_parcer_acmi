import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from PIL import Image, ImageDraw, ImageFont
import io

# Ваш токен бота
BOT_TOKEN = '7376088476:AAEWoyTXmpp_PfHBohLg_4vN7OQRKpIhWSA'
CHANNEL_ID = '@testNeveropv'  # Приватный канал
# Словарь для хранения времени последней отправки фото пользователем
user_last_photo_time = {}
# Ограничение по времени (12 часов в секундах)
TIME_LIMIT = 0  # 12 часов = 43200 секунд
# Текст, который будет добавляться к посту
DEFAULT_CAPTION = "Добавьте свой текст"

# Функция для проверки ограничения
def can_send_photo(user_id):
    current_time = time.time()
    last_time = user_last_photo_time.get(user_id, 0)
    if current_time - last_time >= TIME_LIMIT:
        return True
    return False

# Функция для обработки изображений
async def handle_image(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    # Проверка на временное ограничение (12 часов)
    if can_send_photo(user_id):
        # Разрешаем отправку фото
        photo = update.message.photo[-1]
        # Используем заранее заданный текст как подпись
        caption = DEFAULT_CAPTION
        # Отправляем фото в канал с подписью
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo.file_id,
            caption=caption
        )
        # Обновляем время последней отправки фото
        user_last_photo_time[user_id] = time.time()
        # Подтверждение пользователю
        await update.message.reply_text("Изображение отправлено в канал!")
    else:
        # Если не прошло 12 часов, отклоняем запрос
        remaining_time = TIME_LIMIT - (time.time() - user_last_photo_time[user_id])
        hours, remainder = divmod(remaining_time, 3600)
        minutes, _ = divmod(remainder, 60)
        await update.message.reply_text(f"Вы сможете отправить фото через {int(hours)} часов и {int(minutes)} минут.")

# Функция для старта
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Отправьте мне изображение, и я размещу его в канале, но не чаще, чем раз в 12 часов.")
def main():
    # Создаем экземпляр Application и передаем ему токен бота
    application = Application.builder().token(BOT_TOKEN).build()
    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))
    # Обработчик изображений
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    # Запускаем бота
    application.run_polling()
if __name__ == '__main__':
    main()
    
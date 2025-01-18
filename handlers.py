# handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from parser import search_drug

SEARCH = 1
ITEMS_PER_PAGE = 3  # Количество препаратов на одной странице

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать в бот поиска лекарств!\n"
        "Введите название препарата, который хотите найти.\n"
        "Для отмены поиска используйте команду /cancel"
    )
    return SEARCH

async def search_medicine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drug_name = update.message.text
    await update.message.reply_text(f"🔍 Ищу информацию о препарате: {drug_name}")
    
    # Получаем результаты поиска
    results = await search_drug(drug_name)
    if results == "Препарат не найден":
        await update.message.reply_text(results)
        return SEARCH
        
    # Сохраняем результаты в контексте бота
    if isinstance(results, str):
        results = results.split('\n\n')  # Разбиваем на отдельные блоки
    context.user_data['results'] = results
    context.user_data['current_page'] = 0
    
    # Показываем первую страницу
    await show_page(update, context)
    
    return SEARCH

async def show_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = context.user_data['results']
    current_page = context.user_data['current_page']
    total_pages = (len(results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    # Формируем текст для текущей страницы
    start_idx = current_page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(results))
    current_items = results[start_idx:end_idx]
    
    message_text = f"Страница {current_page + 1} из {total_pages}\n\n"
    message_text += "\n\n".join(current_items)
    
    # Создаем кнопки навигации
    keyboard = []
    nav_buttons = []
    
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data="prev"))
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    # Отправляем или редактируем сообщение с поддержкой HTML
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'  # Добавлено для поддержки HTML-ссылок
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'  # Добавлено для поддержки HTML-ссылок
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "next":
        context.user_data['current_page'] += 1
    elif query.data == "prev":
        context.user_data['current_page'] -= 1
    
    await show_page(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Поиск отменен. Чтобы начать новый поиск, используйте /start"
    )
    return ConversationHandler.END
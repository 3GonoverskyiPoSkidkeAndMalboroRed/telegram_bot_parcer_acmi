# handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import re
from parser import search_drug

SEARCH = 1
WAITING_FOR_PRICE = 2  # Новое состояние для ожидания ввода цены
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
    
    results = await search_drug(drug_name)
    if results == "Препарат не найден":
        await update.message.reply_text(results)
        return SEARCH
    
    if isinstance(results, str):
        results = results.split('\n\n')
    
    # Сохраняем оригинальные результаты для фильтрации
    context.user_data['original_results'] = results.copy()
    context.user_data['results'] = results
    context.user_data['current_page'] = 0
    
    await show_page(update, context)
    return SEARCH

async def show_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = context.user_data.get('results', [])
    current_page = context.user_data.get('current_page', 0)
    total_pages = (len(results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    start_idx = current_page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(results))
    current_items = results[start_idx:end_idx]
    
    if not current_items:
        message_text = "❌ Нет препаратов для отображения."
    else:
        message_text = f"Страница {current_page + 1} из {total_pages}\n\n"
        message_text += "\n\n".join(current_items)
    
    # Создаем кнопки сортировки и навигации
    keyboard = []
    
    # Кнопки сортировки
    sort_buttons = [
        InlineKeyboardButton("🔽 По убыванию цены", callback_data="sort_desc"),
        InlineKeyboardButton("🔼 По возрастанию цены", callback_data="sort_asc")
    ]
    keyboard.append(sort_buttons)
    
    # Кнопки навигации
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data="prev"))
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка установки ограничения по цене
    price_button = [InlineKeyboardButton("💰 Установить ограничение по цене", callback_data="set_price_limit")]
    keyboard.append(price_button)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "next":
        context.user_data['current_page'] += 1
        await show_page(update, context)
        return SEARCH
    elif data == "prev":
        context.user_data['current_page'] -= 1
        await show_page(update, context)
        return SEARCH
    elif data == "set_price_limit":
        await query.message.reply_text(
            "💰 Введите максимальную цену (только число):\n"
            "Например: 500"
        )
        return WAITING_FOR_PRICE
    elif data in ["sort_asc", "sort_desc"]:
        results = context.user_data.get('results', [])
        
        def get_price(result):
            try:
                price_match = re.search(r'💰\s*([\d.]+)\s*руб\.', result)
                if price_match:
                    return float(price_match.group(1))
                return float('inf') if data == "sort_asc" else float('-inf')
            except (ValueError, AttributeError):
                return float('inf') if data == "sort_asc" else float('-inf')
        
        sorted_results = sorted(
            results,
            key=get_price,
            reverse=(data == "sort_desc")
        )
        context.user_data['results'] = sorted_results
        context.user_data['current_page'] = 0
        await show_page(update, context)
        return SEARCH
    else:
        await query.message.reply_text("❌ Неизвестная команда.")
        return SEARCH

async def handle_price_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price_limit = float(update.message.text)
        original_results = context.user_data.get('original_results', [])
        
        def get_price(result):
            try:
                price_match = re.search(r'💰\s*([\d.]+)\s*руб\.', result)
                if price_match:
                    return float(price_match.group(1))
                return float('inf')
            except (ValueError, AttributeError):
                return float('inf')
        
        # Применяем фильтр по цене
        filtered_results = [r for r in original_results if get_price(r) <= price_limit]
        
        if not filtered_results:
            await update.message.reply_text(
                f"❌ Нет препаратов дешевле {price_limit} руб.\n"
                "Показываю все доступные препараты:"
            )
            context.user_data['results'] = original_results.copy()
        else:
            context.user_data['results'] = filtered_results
            await update.message.reply_text(
                f"✅ Найдено {len(filtered_results)} препаратов до {price_limit} руб."
            )
        
        context.user_data['current_page'] = 0
        await show_page(update, context)
        return SEARCH
    
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите только число.\n"
            "Например: 500"
        )
        return WAITING_FOR_PRICE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Поиск отменен. Чтобы начать новый поиск, используйте /start"
    )
    return ConversationHandler.END
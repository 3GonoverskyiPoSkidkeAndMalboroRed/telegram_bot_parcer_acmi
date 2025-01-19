# handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import re
from parser import search_drug
import json
from fuzzywuzzy import process
import logging

logger = logging.getLogger(__name__)

SEARCH = 1
WAITING_FOR_PRICE = 2  # Новое состояние для ожидания ввода цены
WAITING_FOR_DOSAGE = 3  # Новое состояние для ожидания ввода дозировки
WAITING_FOR_TABLETS = 4  # Новое состояние для ожидания ввода количества таблеток
ITEMS_PER_PAGE = 3  # Количество препаратов на одной странице

# Загрузка списка известных препаратов
try:
    with open('drug_names.json', 'r', encoding='utf-8') as f:
        VALID_DRUG_NAMES = json.load(f)
except FileNotFoundError:
    VALID_DRUG_NAMES = []
    logger.error("Файл drug_names.json не найден. Проверка правильности написания не будет работать.")

def find_close_matches(drug_name, limit=3, threshold=70):
    matches = process.extract(drug_name, VALID_DRUG_NAMES, limit=limit)
    return [match for match, score in matches if score >= threshold]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.effective_user.id} начал разговор.")
    await update.message.reply_text(
        "👋 Добро пожаловать в бот поиска лекарств!\n"
        "Введите название препарата, который хотите найти.\n"
        "Для отмены поиска используйте команду /cancel"
    )
    return SEARCH

async def search_medicine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drug_name = update.message.text.strip().capitalize()
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} ищет препарат: {drug_name}")
    
    # Выполняем поиск препарата
    results = await search_drug(drug_name)
    
    if results == "Препарат не найден":
        # Если поиск не дал результатов, проверяем правильность написания
        if drug_name not in VALID_DRUG_NAMES:
            close_matches = find_close_matches(drug_name)
            if close_matches:
                buttons = [
                    InlineKeyboardButton(name, callback_data=f"confirm_{name}") for name in close_matches
                ]
                reply_markup = InlineKeyboardMarkup([buttons])
                await update.message.reply_text(
                    f"❌ Препарат **{drug_name}** не найден. Возможно, вы имели в виду один из следующих вариантов?",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return SEARCH  # Остаёмся в состоянии SEARCH для выбора пользователем
            else:
                await update.message.reply_text(
                    f"❌ Препарат **{drug_name}** не найден, и похожие названия не найдены. Пожалуйста, попробуйте ввести другое название.",
                    parse_mode='Markdown'
                )
                return SEARCH
        else:
            # Название правильное, но ничего не найдено
            await update.message.reply_text(
                f"❌ Препарат **{drug_name}** не найден в нашей базе. Пожалуйста, попробуйте другое название.",
                parse_mode='Markdown'
            )
            return SEARCH
    
    # Если результаты найдены
    if isinstance(results, str):
        results = results.split('\n\n')
    
    # Сохраняем оригинальные результаты для фильтрации
    context.user_data['original_results'] = results.copy()
    context.user_data['results'] = results
    context.user_data['current_page'] = 0
    
    await show_page(update, context)
    return SEARCH

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} нажал кнопку: {data}")
    
    if data.startswith("confirm_"):
        # Пользователь выбрал одно из предложенных названий
        confirmed_name = data.split("confirm_")[1]
        logger.info(f"Пользователь {user_id} подтвердил название препарата: {confirmed_name}")
        await query.edit_message_text(f"🔍 Ищу информацию о препарате: {confirmed_name}")
        # Здесь можно продолжить поиск с подтверждённым именем
        results = await search_drug(confirmed_name)
        if isinstance(results, str):
            results = results.split('\n\n')
        context.user_data['original_results'] = results.copy()
        context.user_data['results'] = results
        context.user_data['current_page'] = 0
        await show_page(update, context)
    elif data in ["sort_desc", "sort_asc"]:
        # Обработка сортировки
        sort_order = "descending" if data == "sort_desc" else "ascending"
        results = context.user_data.get('results', [])
        if sort_order == "descending":
            sorted_results = sorted(results, key=lambda x: extract_price(x), reverse=True)
        else:
            sorted_results = sorted(results, key=lambda x: extract_price(x))
        context.user_data['results'] = sorted_results
        context.user_data['current_page'] = 0
        await show_page(update, context)
    elif data in ["prev", "next"]:
        # Обработка навигации между страницами
        current_page = context.user_data.get('current_page', 0)
        total_pages = (len(context.user_data.get('results', [])) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        if data == "prev" and current_page > 0:
            context.user_data['current_page'] = current_page - 1
        elif data == "next" and current_page < total_pages - 1:
            context.user_data['current_page'] = current_page + 1
        await show_page(update, context)
    elif data == "set_price_limit":
        await query.edit_message_text(
            "💰 Введите максимальную цену для фильтрации:\n"
            "Например: 1000"
        )
        return WAITING_FOR_PRICE
    elif data == "set_dosage_limit":
        await query.edit_message_text(
            "💊 Введите точную дозировку (например, 50):"
        )
        return WAITING_FOR_DOSAGE
    elif data == "set_tablets_limit":
        await query.edit_message_text(
            "💊 Введите точное количество таблеток в пачке (например, 28):"
        )
        return WAITING_FOR_TABLETS
    
    return SEARCH

def extract_price(result):
    try:
        price_match = re.search(r'💰 (\d+) руб\.', result)
        if price_match:
            return int(price_match.group(1))
        return 0
    except:
        return 0

async def handle_price_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price_input = update.message.text.strip()
        max_price = int(price_input)
        original_results = context.user_data.get('original_results', [])
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} установил максимальную цену: {max_price} руб.")
        
        # Применяем фильтр по цене
        filtered_results = [r for r in original_results if extract_price(r) <= max_price]
        
        if not filtered_results:
            await update.message.reply_text(
                f"❌ Нет препаратов с ценой **до {max_price} руб.**.\n"
                "Пожалуйста, попробуйте ввести другую цену или выберите из доступных."
            )
            return SEARCH
        else:
            context.user_data['results'] = filtered_results
            await update.message.reply_text(
                f"✅ Найдено {len(filtered_results)} препаратов с ценой **до {max_price} руб.**."
            )
        
        context.user_data['current_page'] = 0
        await show_page(update, context)
        return SEARCH
    
    except ValueError:
        logger.warning(f"Пользователь {update.effective_user.id} ввел некорректное значение цены: {update.message.text}")
        await update.message.reply_text(
            "❌ Пожалуйста, введите только число.\n"
            "Например: 1000"
        )
        return WAITING_FOR_PRICE

async def handle_dosage_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dosage_input = update.message.text.strip()
        dosage = float(dosage_input)
        original_results = context.user_data.get('original_results', [])
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} установил точную дозировку: {dosage} мг")
        
        def get_dosage(result):
            try:
                dosage_match = re.search(r'(\d+)\s*мг', result.lower())
                if dosage_match:
                    return float(dosage_match.group(1))
                return None
            except (ValueError, AttributeError):
                return None
        
        # Применяем фильтр по точной дозировке
        filtered_results = [r for r in original_results if get_dosage(r) == dosage]
        
        if not filtered_results:
            await update.message.reply_text(
                f"❌ Нет препаратов с дозировкой **{dosage}** мг.\n"
                "Пожалуйста, попробуйте ввести другую дозировку или выберите из доступных."
            )
            return SEARCH
        else:
            context.user_data['results'] = filtered_results
            await update.message.reply_text(
                f"✅ Найдено {len(filtered_results)} препаратов с дозировкой **{dosage}** мг."
            )
        
        context.user_data['current_page'] = 0
        await show_page(update, context)
        return SEARCH
    
    except ValueError:
        logger.warning(f"Пользователь {update.effective_user.id} ввел некорректное значение дозировки: {update.message.text}")
        await update.message.reply_text(
            "❌ Пожалуйста, введите только число.\n"
            "Например: 50"
        )
        return WAITING_FOR_DOSAGE

async def handle_tablets_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tablets_input = update.message.text.strip()
        tablets = int(tablets_input)
        original_results = context.user_data.get('original_results', [])
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} установил точное количество таблеток: {tablets}")
        
        def get_tablets(result):
            try:
                tablets_match = re.search(r'№(\d+)', result)
                if tablets_match:
                    return int(tablets_match.group(1))
                return None
            except (ValueError, AttributeError):
                return None
        
        # Применяем фильтр по точному количеству таблеток
        filtered_results = [r for r in original_results if get_tablets(r) == tablets]
        
        if not filtered_results:
            await update.message.reply_text(
                f"❌ Нет препаратов с количеством таблеток **№{tablets}**.\n"
                "Пожалуйста, попробуйте ввести другое количество или выберите из доступных."
            )
            return SEARCH
        else:
            context.user_data['results'] = filtered_results
            await update.message.reply_text(
                f"✅ Найдено {len(filtered_results)} препаратов с количеством таблеток **№{tablets}**."
            )
        
        context.user_data['current_page'] = 0
        await show_page(update, context)
        return SEARCH
    
    except ValueError:
        logger.warning(f"Пользователь {update.effective_user.id} ввел некорректное значение количества таблеток: {update.message.text}")
        await update.message.reply_text(
            "❌ Пожалуйста, введите только число.\n"
            "Например: 28"
        )
        return WAITING_FOR_TABLETS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} отменил поиск.")
    await update.message.reply_text(
        "❌ Поиск отменен. Чтобы начать новый поиск, используйте /start"
    )
    return ConversationHandler.END

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
        message_text = f"📄 Страница {current_page + 1} из {total_pages}\n\n"
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
    
    # Кнопки фильтрации
    filter_buttons = [
        InlineKeyboardButton("💰 Установить ограничение по цене", callback_data="set_price_limit"),
        InlineKeyboardButton("💊 Установить точную дозировку", callback_data="set_dosage_limit"),
        InlineKeyboardButton("💊 Установить точное количество таблеток", callback_data="set_tablets_limit")
    ]
    keyboard.append(filter_buttons)
    
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
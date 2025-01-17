# handlers.py

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from parser import search_drug

SEARCH = 1

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
    
    # Если результаты слишком длинные, разбиваем их на части
    if len(results) > 4096:
        # Разбиваем текст на части по 4096 символов
        parts = [results[i:i+4096] for i in range(0, len(results), 4096)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(results)
    
    return SEARCH

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Поиск отменен. Чтобы начать новый поиск, используйте /start"
    )
    return ConversationHandler.END
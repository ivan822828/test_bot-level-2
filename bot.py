import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# ========== НАСТРОЙКА ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    exit(1)

# Состояния диалога (пока не используем, но оставим для будущего)
MAIN_MENU = 0

# ========== ТОВАРЫ ==========
PRODUCTS = {
    "coffee": {"name": "☕ Кофе арабика", "price": 3000},
    "tea": {"name": "🍵 Чай черный", "price": 1000},
    "nuts": {"name": "🥜 Миндаль", "price": 1200},
    "honey": {"name": "🍯 Мед цветочный", "price": 2500},
}

# ========== FLASK ==========
app = Flask(__name__)

# ========== БОТ ==========
updater = Updater(token=TOKEN, use_context=True)
dp = updater.dispatcher

# ========== ОБРАБОТЧИКИ ==========

def start(update, context):
    """Главное меню со списком товаров"""
    keyboard = []
    for prod_id, prod_info in PRODUCTS.items():
        button_text = f"{prod_info['name']} - {prod_info['price']} руб/кг"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"prod_{prod_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "🛍️ **Добро пожаловать в магазин!**\n\n"
        "👇 Выберите товар:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def product_info(update, context):
    """Показывает информацию о выбранном товаре"""
    query = update.callback_query
    query.answer()
    
    prod_id = query.data.replace("prod_", "")
    product = PRODUCTS.get(prod_id)
    
    if product:
        text = f"✅ **{product['name']}**\n"
        text += f"💰 Цена: {product['price']} руб/кг\n\n"
        text += "Этот раздел в разработке. Скоро здесь можно будет оформить заказ."
    else:
        text = "❌ Товар не найден"
    
    # Кнопка "Назад" в главное меню
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def back_to_menu(update, context):
    """Возврат в главное меню"""
    query = update.callback_query
    query.answer()
    
    keyboard = []
    for prod_id, prod_info in PRODUCTS.items():
        button_text = f"{prod_info['name']} - {prod_info['price']} руб/кг"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"prod_{prod_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "🛍️ **Добро пожаловать в магазин!**\n\n"
        "👇 Выберите товар:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def help_command(update, context):
    """Команда /help"""
    update.message.reply_text(
        "📖 **Помощь**\n\n"
        "/start - Показать меню товаров\n"
        "/help - Эта справка",
        parse_mode="Markdown"
    )

def unknown(update, context):
    """Обработка неизвестных команд"""
    update.message.reply_text("❌ Неизвестная команда. Используйте /start")

# ========== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ==========
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help_command))
dp.add_handler(CallbackQueryHandler(product_info, pattern="^prod_"))
dp.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
dp.add_handler(MessageHandler(Filters.command, unknown))

# ========== FLASK МАРШРУТЫ ==========
@app.route('/')
def index():
    return "✅ Shop Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(), updater.bot)
        dp.process_update(update)
        return 'ok', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'error', 500

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    # Запускаем бота в режиме вебхука
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_URL').replace('https://', '')}/{TOKEN}" if os.environ.get('RENDER_EXTERNAL_URL') else None
    )
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ != "__main__":
    # Для Gunicorn
    pass
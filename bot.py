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

# Состояния для ConversationHandler
SELECTING_SERVICE = 0

# ========== УСЛУГИ ==========
SERVICES = {
    "gmail": {
        "name": "📧 Gmail аккаунт",
        "description": "✅ Полный доступ к аккаунту Gmail\n✅ Восстановление пароля\n✅ Смена номера телефона\n✅ Гарантия 30 дней",
        "price": "1500 руб"
    },
    "facebook": {
        "name": "📘 Facebook аккаунт",
        "description": "✅ Полный доступ к профилю\n✅ Восстановление доступа\n✅ Смена почты и номера\n✅ Гарантия 30 дней",
        "price": "2000 руб"
    },
    "traffic": {
        "name": "📊 Чтение трафика",
        "description": "✅ Анализ токенов игры\n✅ Просмотр сетевых запросов\n✅ Детальный отчет\n✅ Консультация специалиста",
        "price": "2500 руб"
    },
    "delete": {
        "name": "🗑️ Удаление аккаунта",
        "description": "✅ Полное удаление аккаунта\n✅ Очистка личных данных\n✅ Подтверждение удаления\n✅ Без возможности восстановления",
        "price": "1000 руб"
    }
}

# Реквизиты для оплаты
PAYMENT_DETAILS = """
💳 **Реквизиты для оплаты:**

🏦 **Сбербанк**
Номер карты: `2202 1234 5678 9010`
Получатель: Иван Иванов

₿ **Криптовалюта (USDT)**
Адрес: `TAbcDEfGhIJkLmNOPqRsTuVwXyZ1234567`
Сеть: TRC-20

💸 **ЮMoney**
Кошелек: `4100 1234 5678 9012`

📌 **После оплаты отправьте скриншот в этот чат.**
"""

# ========== FLASK ==========
app = Flask(__name__)

# ========== БОТ ==========
updater = Updater(token=TOKEN, use_context=True)
dp = updater.dispatcher

# Временное хранилище данных пользователя
user_data = {}

# ========== ОБРАБОТЧИКИ ==========

def start(update, context):
    """Главное меню со списком услуг"""
    user_id = update.effective_user.id
    user_data[user_id] = {}
    
    keyboard = []
    for service_id, service_info in SERVICES.items():
        button_text = f"{service_info['name']} - {service_info['price']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service_{service_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "🔰 **Добро пожаловать в сервисный бот!**\n\n"
        "👇 Выберите нужную услугу:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_SERVICE

def service_selected(update, context):
    """Показывает информацию о выбранной услуге и предлагает подтверждение"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    service_id = query.data.replace("service_", "")
    service = SERVICES.get(service_id)
    
    if not service:
        query.edit_message_text("❌ Услуга не найдена")
        return ConversationHandler.END
    
    # Сохраняем выбранную услугу
    user_data[user_id] = {"service_id": service_id, "service": service}
    
    # Кнопки для подтверждения
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton("🔙 Назад к услугам", callback_data="back_to_services")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    service_text = (
        f"**{service['name']}**\n\n"
        f"{service['description']}\n\n"
        f"💰 **Цена: {service['price']}**\n\n"
        f"Подтвердите заказ:"
    )
    
    query.edit_message_text(
        service_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_SERVICE

def confirm_order(update, context):
    """Подтверждение заказа и показ реквизитов"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_data or "service" not in user_data[user_id]:
        query.edit_message_text("❌ Ошибка. Начните заново: /start")
        return ConversationHandler.END
    
    service = user_data[user_id]["service"]
    
    # Формируем итоговое сообщение
    order_text = (
        f"✅ **ЗАКАЗ ПОДТВЕРЖДЕН!**\n\n"
        f"**{service['name']}**\n\n"
        f"{service['description']}\n\n"
        f"💰 **ИТОГО К ОПЛАТЕ: {service['price']}**\n\n"
    )
    
    final_text = order_text + PAYMENT_DETAILS
    
    # Кнопка для нового заказа
    keyboard = [[InlineKeyboardButton("🛍️ Новый заказ", callback_data="new_order")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        final_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END

def back_to_services(update, context):
    """Возврат к списку услуг"""
    query = update.callback_query
    query.answer()
    
    keyboard = []
    for service_id, service_info in SERVICES.items():
        button_text = f"{service_info['name']} - {service_info['price']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service_{service_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "🔰 **Выберите нужную услугу:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_SERVICE

def new_order(update, context):
    """Начать новый заказ"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    user_data[user_id] = {}
    
    keyboard = []
    for service_id, service_info in SERVICES.items():
        button_text = f"{service_info['name']} - {service_info['price']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service_{service_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "🛍️ **Новый заказ**\n\n👇 Выберите услугу:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_SERVICE

def cancel_order(update, context):
    """Отмена заказа"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    user_data.pop(user_id, None)
    
    keyboard = [[InlineKeyboardButton("🛍️ Начать заново", callback_data="new_order")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "❌ Заказ отменен.\n\nМожете начать новый заказ:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

def help_command(update, context):
    """Команда /help"""
    update.message.reply_text(
        "📖 **Помощь**\n\n"
        "/start - Начать заказ\n"
        "/help - Эта справка\n"
        "/cancel - Отменить текущий заказ",
        parse_mode="Markdown"
    )

def cancel(update, context):
    """Отмена через команду"""
    user_id = update.message.from_user.id
    user_data.pop(user_id, None)
    update.message.reply_text("❌ Заказ отменен. /start - новый заказ")
    return ConversationHandler.END

def unknown(update, context):
    """Обработка неизвестных команд"""
    update.message.reply_text("❌ Неизвестная команда. Используйте /start")

# ========== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ==========

# ConversationHandler для основного процесса заказа
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        SELECTING_SERVICE: [
            CallbackQueryHandler(service_selected, pattern="^service_"),
            CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
            CallbackQueryHandler(back_to_services, pattern="^back_to_services$"),
            CallbackQueryHandler(cancel_order, pattern="^cancel_order$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

dp.add_handler(conv_handler)
dp.add_handler(CommandHandler("help", help_command))
dp.add_handler(CallbackQueryHandler(new_order, pattern="^new_order$"))
dp.add_handler(MessageHandler(Filters.command, unknown))

# ========== FLASK МАРШРУТЫ ==========
@app.route('/')
def index():
    return "✅ Service Bot Level 2 is running!"

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ != "__main__":
    # Для Gunicorn
    pass

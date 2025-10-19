import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные
SCHEDULE_DATA = None
TOKEN = None
bot = None
app = Flask(__name__)
application = None

def load_schedule():
    """Загружает расписание из переменной окружения"""
    global SCHEDULE_DATA
    schedule_json = os.getenv('SCHEDULE_JSON')
    if schedule_json:
        try:
            SCHEDULE_DATA = json.loads(schedule_json)
            logger.info("Расписание успешно загружено")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON расписания: {e}")
            SCHEDULE_DATA = None
    else:
        logger.error("Переменная окружения SCHEDULE_JSON не найдена")
        SCHEDULE_DATA = None

def get_current_week_type():
    """Определяет тип текущей недели (четная/нечетная)"""
    # Базовая дата - 19 октября 2025, воскресенье, конец первой недели (нечетной)
    base_date = datetime(2025, 10, 19)  # воскресенье

    # Вычисляем количество недель с базовой даты
    today = datetime.now()
    days_since_base = (today - base_date).days

    # Определяем тип недели
    # Базовая дата - конец нечетной недели, поэтому:
    # Если прошло четное количество недель - нечетная неделя (возвращаемся к началу нечетной)
    # Если прошло нечетное количество недель - четная неделя
    weeks_since_base = days_since_base // 7
    if weeks_since_base % 2 == 0:
        return 1  # нечетная неделя (базовая дата - конец нечетной)
    else:
        return 2  # четная неделя

def get_weekday_name(date):
    """Получает название дня недели на русском"""
    weekdays = {
        0: "Понедельник",
        1: "Вторник",
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
        6: "Воскресенье"
    }
    return weekdays[date.weekday()]

def format_class_info(class_item):
    """Форматирует информацию о занятии"""
    if 'window' in class_item:
        return f"🪟 Окно: {class_item['window']} ({class_item['duration']})"
    else:
        return (
            f"⏰ {class_item['time']}\n"
            f"📚 {class_item['subject']}\n"
            f"🏢 Аудитория: {class_item['room']}\n"
            f"📍 {class_item['address']}\n"
        )

def get_schedule_for_date(date_str=None):
    """Получает расписание для указанной даты"""
    if not SCHEDULE_DATA:
        return "❌ Расписание не загружено"

    try:
        if date_str:
            # Парсим дату в формате ДД.ММ
            day, month = map(int, date_str.split('.'))
            year = datetime.now().year
            target_date = datetime(year, month, day)
        else:
            target_date = datetime.now()

        current_week_type = get_current_week_type()
        weekday_name = get_weekday_name(target_date)

        # Находим нужную неделю в расписании
        for week in SCHEDULE_DATA['schedule']:
            if week['week'] == current_week_type:
                # Находим нужный день
                for day in week['days']:
                    if day['day'] == weekday_name:
                        classes = day['classes']

                        if not classes:
                            note = day.get('note', 'Нет занятий')
                            return f"📅 {weekday_name} ({target_date.strftime('%d.%m.%Y')})\n\n{note}"

                        response = f"📅 {weekday_name} ({target_date.strftime('%d.%m.%Y')})\n\n"

                        for class_item in classes:
                            response += format_class_info(class_item) + "\n"

                        return response

        return f"❌ Расписание для {weekday_name} не найдено"
    except ValueError:
        return "❌ Неверный формат даты. Используйте формат ДД.ММ"
    except Exception as e:
        logger.error(f"Ошибка получения расписания: {e}")
        return "❌ Ошибка при получении расписания"

def get_week_schedule():
    """Получает расписание на текущую неделю"""
    if not SCHEDULE_DATA:
        return "❌ Расписание не загружено"

    current_week_type = get_current_week_type()

    # Находим нужную неделю в расписании
    for week in SCHEDULE_DATA['schedule']:
        if week['week'] == current_week_type:
            response = "📅 Расписание на неделю\n\n"

            for day in week['days']:
                day_name = day['day']
                classes = day['classes']

                response += f"📅 {day_name}:\n"

                if not classes:
                    note = day.get('note', 'Нет занятий')
                    response += f"   {note}\n\n"
                else:
                    for class_item in classes:
                        response += f"   {format_class_info(class_item)}\n"
                response += "\n"

            return response

    return "❌ Расписание не найдено"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data='today')],
        [InlineKeyboardButton("📆 Конкретная дата", callback_data='date')],
        [InlineKeyboardButton("📅 На неделю", callback_data='week')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        '🎓 Добро пожаловать в бот расписания ИТМО!\n\n'
        'Выберите действие:',
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()

    if query.data == 'today':
        schedule = get_schedule_for_date()
        await query.edit_message_text(text=schedule)

    elif query.data == 'date':
        await query.edit_message_text(
            text='📝 Введите дату в формате ДД.ММ (например: 25.12)'
        )
        context.user_data['waiting_for_date'] = True

    elif query.data == 'week':
        schedule = get_week_schedule()
        await query.edit_message_text(text=schedule)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    if context.user_data.get('waiting_for_date'):
        date_str = update.message.text.strip()
        schedule = get_schedule_for_date(date_str)

        await update.message.reply_text(schedule)
        context.user_data['waiting_for_date'] = False
    else:
        await update.message.reply_text(
            '❓ Неизвестная команда. Используйте /start для начала работы с ботом.'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f'Update {update} caused error {context.error}')
    if update and update.message:
        await update.message.reply_text('❌ Произошла ошибка. Попробуйте еще раз.')

def init_bot():
    """Инициализирует бота и загружает данные"""
    global TOKEN, bot, application

    # Загружаем расписание
    load_schedule()

    if not SCHEDULE_DATA:
        logger.error("Не удалось загрузить расписание из переменной окружения SCHEDULE_JSON")
        logger.error("Убедитесь, что переменная окружения SCHEDULE_JSON установлена в Render Dashboard")
        return False

    # Проверяем токен
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Не найден токен бота в переменной окружения TELEGRAM_BOT_TOKEN")
        logger.error("Убедитесь, что переменная окружения TELEGRAM_BOT_TOKEN установлена в Render Dashboard")
        return False

    TOKEN = token
    bot = Bot(token=token)

    # Создаем глобальный application
    application = Application.builder().token(token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)

    return True

@app.route('/', methods=['GET'])
def home():
    """Домашняя страница для проверки сервера"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Telegram ИТМО Бот</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
        <h1>🤖 Telegram ИТМО Бот</h1>
        <p><strong>Статус:</strong> {"✅ Сервер работает" if bot else "❌ Бот не инициализирован"}</p>
        <p><strong>Вебхук:</strong> <code>/webhook</code></p>
        <p><strong>Правильный URL для вебхука:</strong> <code>https://telegram-itmo-bot.onrender.com/webhook</code></p>
        <p><strong>Ваш текущий URL (неправильный):</strong> <code>https://telegram-itmo-bot-.onrender.com/webhook</code></p>
        <hr>
        <h3>🚨 Вебхук не настроен!</h3>
        <p>Выполните команду в терминале:</p>
        <code style="background: #f0f0f0; padding: 10px; display: block; margin: 10px;">
        curl "https://api.telegram.org/bot8181605760:AAFm06efAuVxbFLU0OGUhoYMXG3MUznvoh0/setWebhook?url=https://telegram-itmo-bot.onrender.com/webhook"
        </code>
        <p>После настройки вебхука отправьте <code>/start</code> боту в Telegram</p>
    </body>
    </html>
    '''

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """Обработчик вебхуков от Telegram"""
    if request.method == 'GET':
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Вебхук Telegram Бота</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>🔗 Вебхук Telegram Бота</h1>
            <p><strong>Статус:</strong> {"✅ Готов к приему сообщений" if bot else "❌ Бот не инициализирован"}</p>
            <p><strong>Правильный URL:</strong> <code>https://telegram-itmo-bot.onrender.com/webhook</code></p>
            <hr>
            <h3>🚨 Проверьте статус вебхука!</h3>
            <p><strong>Выполните команду для проверки:</strong></p>
            <code style="background: #e7f3ff; padding: 10px; display: block; margin: 10px;">
            curl "https://api.telegram.org/bot8181605760:AAFm06efAuVxbFLU0OGUhoYMXG3MUznvoh0/getWebhookInfo"
            </code>
            <p><strong>Должен показать ваш вебхук URL.</strong></p>
            <p><a href="/">← Вернуться на главную</a></p>
        </body>
        </html>
        '''

    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 500

    try:
        update_data = request.get_json()
        if update_data:
            update = Update.de_json(update_data, bot)
            # Обрабатываем обновление асинхронно
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update(update))
            loop.close()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return jsonify({'error': str(e)}), 500

async def process_update(update):
    """Обрабатывает обновление от Telegram"""
    global application

    if not application:
        logger.error("Application не инициализирован")
        return

    # Обрабатываем обновление через глобальный application
    await application.process_update(update)

def main():
    """Основная функция"""
    logger.info("Запуск Telegram бота ИТМО...")

    # Инициализируем бота
    if not init_bot():
        logger.error("Не удалось инициализировать бота")
        return

    logger.info("Бот успешно инициализирован")

    # Проверяем, запущен ли бот в Render (есть переменная PORT)
    port = os.getenv('PORT')
    if port:
        # Запуск в режиме веб-сервера для вебхуков
        logger.info(f"Запуск веб-сервера на порту {port}")
        app.run(host='0.0.0.0', port=int(port), debug=False)
    else:
        # Запуск в режиме polling для локальной разработки
        logger.info("Запуск в режиме polling")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Создаем локальный application для polling режима
        local_app = Application.builder().token(TOKEN).build()
        local_app.add_handler(CommandHandler("start", start))
        local_app.add_handler(CallbackQueryHandler(button_handler))
        local_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        local_app.add_error_handler(error_handler)

        loop.run_until_complete(local_app.run_polling())
        loop.close()

if __name__ == '__main__':
    main()

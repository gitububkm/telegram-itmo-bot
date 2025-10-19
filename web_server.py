#!/usr/bin/env python3
"""
Веб-сервер для Telegram бота с поддержкой webhook
Совместим с Render Free Web Service

Использует асинхронную обработку обновлений через очередь
для избежания блокировки Flask сервера при обработке сообщений.
"""

import os
import json
import logging
import time
import asyncio
import threading
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальная переменная для хранения экземпляра Application
telegram_application = None

# Глобальная переменная для отслеживания статуса бота
bot_status = {
    'is_running': False,
    'start_time': None,
    'webhook_set': False,
    'last_update': None
}

# Очередь для обновлений и поток для их обработки
update_queue = asyncio.Queue()
processing_thread = None
loop = None

def start_update_processor():
    """Запускает асинхронный процессор обновлений"""
    global processing_thread, loop

    def run_processor():
        global loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def process_updates():
            while True:
                try:
                    # Получаем обновление из очереди
                    update_data = await update_queue.get()

                    if update_data is None:  # Сигнал остановки
                        break

                    if telegram_application:
                        # Создаем Update объект из JSON данных
                        from telegram import Update
                        update = Update.de_json(update_data, telegram_application.bot)

                        # Обрабатываем обновление асинхронно
                        await telegram_application.process_update(update)
                        logger.info(f"Обработан webhook update: {update.update_id}")
                    else:
                        logger.error("Telegram Application не инициализирован")

                    update_queue.task_done()

                except Exception as e:
                    logger.error(f"Ошибка обработки обновления: {e}")

        try:
            loop.run_until_complete(process_updates())
        except Exception as e:
            logger.error(f"Ошибка в процессоре обновлений: {e}")
        finally:
            loop.close()

    processing_thread = threading.Thread(target=run_processor, daemon=True)
    processing_thread.start()
    logger.info("✅ Асинхронный процессор обновлений запущен")

def stop_update_processor():
    """Останавливает асинхронный процессор обновлений"""
    global processing_thread, loop

    if processing_thread and processing_thread.is_alive():
        # Отправляем сигнал остановки
        if loop:
            loop.call_soon_threadsafe(lambda: asyncio.create_task(stop_processing()))

        processing_thread.join(timeout=5)

        if processing_thread.is_alive():
            logger.warning("Процессор обновлений не остановился корректно")

async def stop_processing():
    """Асинхронная функция для остановки процессинга"""
    await update_queue.put(None)

@app.route('/')
def home():
    """Главная страница для проверки работы сервера"""
    return "Bot is running", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook-запросов от Telegram"""
    try:
        # Получаем JSON данные от Telegram
        update_data = request.get_json()

        if not update_data:
            logger.warning("Получен пустой webhook запрос")
            return "OK", 200

        logger.info(f"Получен webhook update: {update_data.get('update_id', 'unknown')}")

        # Обновляем статус последнего обновления
        bot_status['last_update'] = time.time()

        # Добавляем обновление в асинхронную очередь для обработки
        if processing_thread and processing_thread.is_alive():
            # Используем синхронную версию для добавления в очередь
            # В реальном asyncio коде это было бы await
            def add_to_queue():
                try:
                    # Получаем текущий loop из процессора
                    if loop:
                        loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(update_queue.put(update_data))
                        )
                except Exception as e:
                    logger.error(f"Ошибка добавления в очередь: {e}")

            add_to_queue()
            logger.info("Обновление добавлено в очередь для асинхронной обработки")
        else:
            logger.error("Процессор обновлений не запущен")
            return "Update processor not running", 500

        return "OK", 200

    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return "Error processing webhook", 500

@app.route('/health')
def health_check():
    """Health check endpoint для Render"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': time.time(),
        'bot_running': bot_status['is_running'],
        'webhook_set': bot_status['webhook_set']
    }), 200

@app.route('/status')
def status():
    """JSON статус для мониторинга"""
    current_time = time.time()
    uptime = current_time - bot_status['start_time'] if bot_status['start_time'] else 0
    
    return jsonify({
        'bot_running': bot_status['is_running'],
        'webhook_set': bot_status['webhook_set'],
        'uptime': uptime,
        'last_update': bot_status['last_update'],
        'environment': {
            'telegram_token': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            'schedule_json': bool(os.getenv('SCHEDULE_JSON')),
            'port': os.getenv('PORT', '10000')
        }
    }), 200

def set_webhook():
    """Устанавливает webhook для Telegram бота"""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ Не найден токен бота в переменной окружения TELEGRAM_BOT_TOKEN")
            return False
        
        # Получаем URL приложения из переменной окружения или используем Render URL
        app_name = os.getenv('RENDER_APP_NAME')
        if app_name:
            webhook_url = f"https://{app_name}.onrender.com/webhook"
        else:
            # Если RENDER_APP_NAME не установлен, используем переменную WEBHOOK_URL
            webhook_url = os.getenv('WEBHOOK_URL')
            if not webhook_url:
                logger.error("❌ Не установлены переменные окружения RENDER_APP_NAME или WEBHOOK_URL")
                return False
        
        logger.info(f"🔗 Установка webhook: {webhook_url}")
        
        # Создаем бота и устанавливаем webhook
        bot = Bot(token=token)
        result = bot.set_webhook(url=webhook_url)
        
        if result:
            logger.info("✅ Webhook успешно установлен")
            bot_status['webhook_set'] = True
            return True
        else:
            logger.error("❌ Не удалось установить webhook")
            return False
            
    except TelegramError as e:
        logger.error(f"❌ Ошибка Telegram API при установке webhook: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при установке webhook: {e}")
        return False

def update_bot_status(running=False, last_update=None):
    """Обновляет статус бота"""
    bot_status['is_running'] = running
    if running and not bot_status['start_time']:
        bot_status['start_time'] = time.time()
    if last_update:
        bot_status['last_update'] = last_update

def initialize_telegram_app(application):
    """Инициализирует Telegram Application для обработки webhook"""
    global telegram_application
    telegram_application = application

    # Запускаем асинхронный процессор обновлений
    start_update_processor()

    logger.info("✅ Telegram Application инициализирован для webhook")

def run_server():
    """Запускает Flask сервер"""
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🚀 Запуск веб-сервера на порту {port}")

    # Устанавливаем webhook при запуске
    if set_webhook():
        logger.info("✅ Сервер готов к работе с webhook")
    else:
        logger.warning("⚠️ Webhook не установлен, но сервер запущен")

    # Обновляем статус
    update_bot_status(running=True)

    try:
        # Запускаем сервер
        app.run(host='0.0.0.0', port=port, debug=False)
    finally:
        # Останавливаем процессор обновлений при завершении
        logger.info("⏹️ Остановка процессора обновлений...")
        stop_update_processor()
        logger.info("✅ Процессор обновлений остановлен")

if __name__ == '__main__':
    run_server()
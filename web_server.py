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

# Глобальные переменные для межпоточного взаимодействия
update_queue = []
queue_lock = threading.Lock()
processing_thread = None
shutdown_event = threading.Event()

def start_update_processor():
    """Запускает асинхронный процессор обновлений"""
    global processing_thread

    def run_processor():
        # Создаем новое событие для asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def process_updates():
            logger.info("Запуск цикла обработки обновлений")
            while not shutdown_event.is_set():
                try:
                    # Получаем обновление из очереди (неблокирующе)
                    update_data = None
                    with queue_lock:
                        if update_queue:
                            update_data = update_queue.pop(0)
                            logger.info(f"Извлечено обновление из очереди, размер очереди: {len(update_queue)}")

                    if update_data is None:
                        await asyncio.sleep(0.1)  # Небольшая пауза
                        continue

                    logger.info(f"Обработка обновления: {update_data.get('update_id', 'unknown')}")

                    if telegram_application:
                        # Проверяем, что приложение инициализировано
                        if not hasattr(telegram_application, '_initialized') or not telegram_application._initialized:
                            logger.error("❌ Попытка обработать обновление в неинициализированном приложении")
                            continue

                        # Создаем Update объект из JSON данных
                        from telegram import Update
                        update = Update.de_json(update_data, telegram_application.bot)

                        # Обрабатываем обновление асинхронно
                        await telegram_application.process_update(update)
                        logger.info(f"✅ Успешно обработан webhook update: {update.update_id}")
                    else:
                        logger.error("❌ Telegram Application не инициализирован")

                except Exception as e:
                    logger.error(f"Ошибка обработки обновления: {e}")

            logger.info("Цикл обработки обновлений завершен")

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
    global processing_thread

    if processing_thread and processing_thread.is_alive():
        # Устанавливаем флаг завершения
        shutdown_event.set()

        processing_thread.join(timeout=5)

        if processing_thread.is_alive():
            logger.warning("Процессор обновлений не остановился корректно")

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

        update_id = update_data.get('update_id', 'unknown')
        logger.info(f"📨 Получен webhook update: {update_id}")

        # Проверяем тип обновления
        if 'message' in update_data:
            message = update_data['message']
            user_id = message.get('from', {}).get('id', 'unknown')
            text = message.get('text', 'no text')
            logger.info(f"📨 Сообщение от пользователя {user_id}: '{text}'")

        # Обновляем статус последнего обновления
        bot_status['last_update'] = time.time()

        # Добавляем обновление в очередь для обработки
        if processing_thread and processing_thread.is_alive():
            # Добавляем обновление в очередь синхронно
            with queue_lock:
                update_queue.append(update_data)

            logger.info(f"✅ Обновление {update_id} добавлено в очередь для асинхронной обработки")
        else:
            logger.error("❌ Процессор обновлений не запущен")
            return "Update processor not running", 500

        return "OK", 200

    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return "Error processing webhook", 500

@app.route('/check-webhook')
def check_webhook():
    """Проверяет настройки webhook в Telegram"""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            return jsonify({
                "error": "TELEGRAM_BOT_TOKEN не установлен",
                "status": "error"
            }), 500

        import requests

        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                return jsonify({
                    "webhook_url": webhook_info.get('url', 'не установлен'),
                    "pending_update_count": webhook_info.get('pending_update_count', 0),
                    "last_error_date": webhook_info.get('last_error_date'),
                    "last_error_message": webhook_info.get('last_error_message'),
                    "max_connections": webhook_info.get('max_connections', 40),
                    "ip_address": webhook_info.get('ip_address'),
                    "status": "success"
                })
            else:
                return jsonify({
                    "error": f"Ошибка API Telegram: {data}",
                    "status": "error"
                }), 500
        else:
            return jsonify({
                "error": f"Ошибка HTTP: {response.status_code}",
                "status": "error"
            }), 500

    except Exception as e:
        return jsonify({
            "error": f"Исключение: {e}",
            "status": "error"
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint для Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'bot_running': bot_status['is_running'],
        'webhook_set': bot_status['webhook_set'],
        'queue_size': len(update_queue),
        'processor_alive': processing_thread.is_alive() if processing_thread else False
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
        'queue_size': len(update_queue),
        'processor_alive': processing_thread.is_alive() if processing_thread else False,
        'environment': {
            'telegram_token': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            'schedule_json': bool(os.getenv('SCHEDULE_JSON')),
            'port': os.getenv('PORT', '10000')
        }
    }), 200

def set_webhook():
    """Устанавливает webhook для Telegram бота асинхронно"""
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

        # Создаем event loop для асинхронного вызова
        import asyncio

        async def _set_webhook():
            bot = Bot(token=token)
            return await bot.set_webhook(url=webhook_url)

        # Создаем новый event loop для асинхронного вызова
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_set_webhook())
            loop.close()

            if result:
                logger.info("✅ Webhook успешно установлен")
                bot_status['webhook_set'] = True
                return True
            else:
                logger.error("❌ Не удалось установить webhook")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка при создании event loop: {e}")
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

    # Проверяем, что приложение инициализировано
    if not hasattr(application, '_initialized') or not application._initialized:
        logger.error("❌ Telegram Application не инициализирован! Вызовите application.initialize()")
        return

    logger.info("🔗 Передача Application в веб-сервер для обработки webhook")

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
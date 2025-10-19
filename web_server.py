#!/usr/bin/env python3
"""
Простой веб-сервер для Render с health check endpoint
Работает параллельно с Telegram ботом
"""

from flask import Flask
import threading
import time
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальная переменная для отслеживания статуса бота
bot_status = {
    'is_running': False,
    'last_update': None,
    'start_time': None
}

@app.route('/')
def home():
    """Главная страница с информацией о статусе бота"""
    current_time = time.time()
    uptime = current_time - bot_status['start_time'] if bot_status['start_time'] else 0

    status_info = f"""
    🤖 Telegram Bot Status
    ======================

    Bot Running: {'✅ Да' if bot_status['is_running'] else '❌ Нет'}
    Start Time: {time.ctime(bot_status['start_time']) if bot_status['start_time'] else 'Не запущен'}
    Uptime: {uptime:.0f} секунд
    Last Update: {time.ctime(bot_status['last_update']) if bot_status['last_update'] else 'Нет обновлений'}

    Environment:
    - TELEGRAM_BOT_TOKEN: {'✅ Установлен' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Не установлен'}
    - SCHEDULE_JSON: {'✅ Установлен' if os.getenv('SCHEDULE_JSON') else '❌ Не установлен'}

    Сервер работает на порту {os.getenv('PORT', 10000)}
    """

    return f"<pre>{status_info}</pre>", 200

@app.route('/health')
def health_check():
    """Health check endpoint для Render"""
    return {'status': 'healthy', 'timestamp': time.time()}, 200

@app.route('/status')
def status():
    """JSON статус для мониторинга"""
    return {
        'bot_running': bot_status['is_running'],
        'uptime': time.time() - bot_status['start_time'] if bot_status['start_time'] else 0,
        'last_update': bot_status['last_update'],
        'environment': {
            'telegram_token': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            'schedule_json': bool(os.getenv('SCHEDULE_JSON'))
        }
    }

def update_bot_status(running=False, last_update=None):
    """Обновляет статус бота"""
    bot_status['is_running'] = running
    if running and not bot_status['start_time']:
        bot_status['start_time'] = time.time()
    if last_update:
        bot_status['last_update'] = last_update

def run_web_server():
    """Запускает веб-сервер в отдельном потоке"""
    # Используем порт из переменной окружения или значение по умолчанию
    port = int(os.getenv('PORT', 10000))
    logger.info(f"Запуск веб-сервера на порту {port}")

    # Запускаем сервер в отдельном потоке без блокировки
    from werkzeug.serving import make_server
    import threading

    server = make_server('0.0.0.0', port, app, threaded=True)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    logger.info(f"Веб-сервер запущен на порту {port}")

def start_web_server():
    """Запускает веб-сервер в фоне"""
    # run_web_server уже создает свой поток
    run_web_server()

if __name__ == '__main__':
    start_web_server()

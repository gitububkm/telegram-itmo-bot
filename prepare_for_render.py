#!/usr/bin/env python3
"""
Скрипт для подготовки репозитория к деплою на Render
Удаляет файлы с личной информацией и проверяет статус git
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✅ {description}")
            return result.stdout
        else:
            print(f"❌ Ошибка {description}: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        return None

def main():
    print("🚀 Подготовка репозитория к деплою на Render")
    print("=" * 60)

    # Проверяем статус git
    print("\n📋 Проверка статуса git...")
    git_status = run_command("git status --porcelain", "Проверка статуса git")

    # Обновляем файлы для совместимости
    print("\n🔧 Обновление файлов для совместимости...")
    run_command("git add runtime.txt requirements.txt main.py web_server.py", "Добавление обновленных файлов для веб-сервера и бота")

    if git_status:
        files = git_status.strip().split('\n')
        if files and files[0]:  # Если есть файлы для коммита
            print(f"📄 Найдено {len(files)} измененных файлов:")
            for file in files:
                print(f"   {file}")
        else:
            print("✅ Рабочая директория чистая")

    # Удаляем файлы с личной информацией, если они существуют
    private_files = [
        'schedule_for_render.json',
        '.env',
        '.env.local'
    ]

    print("\n🗑️  Удаление файлов с личной информацией...")
    for file in private_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Удален: {file}")
            except Exception as e:
                print(f"❌ Не удалось удалить {file}: {e}")
        else:
            print(f"✅ Файл не найден (уже удален): {file}")

    # Проверяем, что важные файлы есть
    required_files = [
        'main.py',
        'web_server.py',
        'requirements.txt',
        'runtime.txt',
        '.gitignore',
        'README.md'
    ]

    print("\n📋 Проверка наличия необходимых файлов...")
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ Найден: {file}")
        else:
            print(f"❌ Отсутствует: {file}")
            missing_files.append(file)

    if missing_files:
        print(f"\n❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        print("Добавьте эти файлы перед деплоем!")
        return False

    # Финальная проверка git status
    print("\n📋 Финальная проверка git status...")
    run_command("git status", "Финальный статус git")

    print("\n" + "=" * 60)
    print("🎉 Репозиторий готов к повторному деплою на Render!")
    print("\n📝 Следующие шаги:")
    print("1. Закоммитьте изменения: git add . && git commit -m 'Add web server with health check for infinite uptime'")
    print("2. Отправьте на GitHub: git push")
    print("3. Render автоматически запустит повторный деплой")
    print("\n🔧 НОВАЯ АРХИТЕКТУРА:")
    print("   ✅ Веб-сервер + Health Check для предотвращения 'засыпания'")
    print("   ✅ Бот работает параллельно с веб-сервером")
    print("   ✅ Автоматическое отслеживание статуса бота")
    print("   ✅ Бесконечная работа без падений")
    print("\n📋 Переменные окружения в Render Dashboard:")
    print("   - TELEGRAM_BOT_TOKEN: ваш токен бота")
    print("   - SCHEDULE_JSON: ваше расписание (из env_example.txt)")
    print("   - PORT: порт для веб-сервера (автоматически устанавливается Render, обычно 10000)")
   print("            Можно указать вручную в Render Dashboard → Settings → Environment")
    print("\n🚀 После деплоя:")
    print("   - Render увидит открытые порты и не завершит деплой")
    print("   - Веб-сервер ответит на health check")
    print("   - Бот запустится параллельно и будет работать бесконечно")
    print("   - Доступ к статусу: https://your-app.onrender.com/health")
    print("   - Мониторинг: https://your-app.onrender.com/status")
    print("\n📱 Использование бота:")
    print("   - Отправьте /start боту в Telegram")
    print("   - Бот ответит кнопками меню")
    print("   - Работает 24/7 без падений!")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

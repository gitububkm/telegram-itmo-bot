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
    run_command("git add runtime.txt requirements.txt main.py", "Добавление обновленных файлов для Flask веб-сервера")

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
    print("1. Закоммитьте изменения: git add . && git commit -m 'Improve schedule formatting with minimalist readable design'")
    print("2. Отправьте на GitHub: git push")
    print("3. Render автоматически запустит повторный деплой")
    print("4. Убедитесь, что переменные окружения установлены в Render Dashboard:")
    print("   - TELEGRAM_BOT_TOKEN: ваш токен бота")
    print("   - SCHEDULE_JSON: ваше расписание (из env_example.txt)")
    print("5. После деплоя бот автоматически удалит вебхук и запустится в режиме polling")
    print("6. В логах увидите 'Вебхук успешно удален' и успешный запуск")
    print("7. Отправьте /start боту в Telegram - он ответит кнопками меню")
    print("8. Расписание теперь в минималистичном формате - читаемо и красиво!")
    print("9. После каждого действия бот показывает меню снова - не нужно заново писать /start!")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

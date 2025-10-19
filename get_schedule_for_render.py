#!/usr/bin/env python3
"""
Скрипт для получения SCHEDULE_JSON для Render
Запустите этот скрипт, чтобы получить значение переменной SCHEDULE_JSON для вставки в Render
"""

import json

# Читаем содержимое env_example.txt
with open('env_example.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# Находим значение SCHEDULE_JSON
lines = content.split('\n')
schedule_json = None

for line in lines:
    if line.startswith('SCHEDULE_JSON='):
        # Убираем SCHEDULE_JSON= и берем значение
        schedule_json = line[14:]  # len('SCHEDULE_JSON=') = 14
        break

if schedule_json:
    print("✅ Найдено значение SCHEDULE_JSON:")
    print("=" * 80)
    print(schedule_json)
    print("=" * 80)
    print("\n📋 Инструкции:")
    print("1. Скопируйте текст выше (между знаками =)")
    print("2. Вставьте его в переменную окружения SCHEDULE_JSON на Render")
    print("3. Убедитесь, что весь текст вставлен в одну строку")

    # Проверяем, что JSON валидный
    try:
        parsed = json.loads(schedule_json)
        print(f"\n✅ JSON валидный! Найдено {len(parsed['schedule'])} типа недель")
    except json.JSONDecodeError as e:
        print(f"\n❌ Ошибка в JSON: {e}")
else:
    print("❌ Не найдено значение SCHEDULE_JSON в файле env_example.txt")

#!/usr/bin/env python3
"""
Локальный тест бота для проверки функциональности
Запустите этот файл для проверки работы бота без Telegram API
"""

import json
import sys
import os
from datetime import datetime
from main import get_current_week_type, get_schedule_for_date, get_week_schedule, load_schedule

# Загружаем расписание для тестирования
SCHEDULE_JSON = json.dumps({
    "schedule": [
        {
            "week": 1,
            "days": [
                {
                    "day": "Понедельник",
                    "classes": [
                        {
                            "time": "11:30 - 13:30",
                            "subject": "Название предмета",
                            "room": "306",
                            "address": "Адрес корпуса"
                        }
                    ]
                },
                {
                    "day": "Воскресенье",
                    "classes": [],
                    "note": "Выходной наконец то!"
                }
            ]
        },
        {
            "week": 2,
            "days": [
                {
                    "day": "Понедельник",
                    "classes": [
                        {
                            "time": "11:30 - 13:00",
                            "subject": "Название предмета",
                            "room": "306",
                            "address": "Адрес корпуса"
                        }
                    ]
                }
            ]
        }
    ]
})

def test_schedule_loading():
    """Тестируем загрузку расписания"""
    # Устанавливаем переменную окружения
    os.environ['SCHEDULE_JSON'] = SCHEDULE_JSON
    load_schedule()

    print("✅ Расписание загружено успешно")

def test_week_detection():
    """Тестируем определение типа недели"""
    current_week = get_current_week_type()
    print(f"📅 Текущий тип недели: {current_week}")

def test_today_schedule():
    """Тестируем получение расписания на сегодня"""
    schedule = get_schedule_for_date()
    print(f"📅 Расписание на сегодня:\n{schedule}")

def test_date_schedule():
    """Тестируем получение расписания на конкретную дату"""
    schedule = get_schedule_for_date("20.10")  # Понедельник
    print(f"📅 Расписание на 20.10:\n{schedule}")

def test_week_schedule():
    """Тестируем получение расписания на неделю"""
    schedule = get_week_schedule()
    print(f"📅 Расписание на неделю:\n{schedule}")

def main():
    """Основная функция тестирования"""
    print("🧪 Запуск локального тестирования бота...")
    print("=" * 50)

    try:
        test_schedule_loading()
        print()

        test_week_detection()
        print()

        test_today_schedule()
        print()

        test_date_schedule()
        print()

        test_week_schedule()
        print()

        print("=" * 50)
        print("✅ Все тесты завершены успешно!")

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

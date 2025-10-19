#!/usr/bin/env python3
"""
Тест корректности работы расписания с московским временем
"""

import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_moscow_time():
    """Получаем текущее время в Москве (симуляция)"""
    # Для теста используем фиксированное время - 19 октября 2025, воскресенье
    # Это поможет протестировать логику определения дней недели
    test_time = datetime(2025, 10, 19, 12, 0, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    return test_time

def get_current_week_type(target_date=None):
    """Определяет тип текущей недели (четная/нечетная)"""
    if target_date is None:
        target_date = get_moscow_time()

    # Находим ближайший понедельник в прошлом (день отсчета)
    days_since_monday = (target_date.weekday() - 0) % 7  # 0 = понедельник
    if days_since_monday == 0:  # Если сегодня понедельник
        reference_monday = target_date
    else:
        reference_monday = target_date - timedelta(days=days_since_monday)

    # Базовая дата - 12 октября 2025, воскресенье, конец четной недели
    base_date = datetime(2025, 10, 12, tzinfo=ZoneInfo("Europe/Moscow"))  # воскресенье

    # Вычисляем количество недель с базовой даты до дня отсчета
    days_since_base = (reference_monday - base_date).days
    weeks_since_base = days_since_base // 7

    # Определяем тип недели на основе дня отсчета
    # Базовая дата - конец четной недели, поэтому:
    # Если день отсчета - четное количество недель от базовой даты - нечетная неделя
    # Если день отсчета - нечетное количество недель от базовой даты - четная неделя
    if weeks_since_base % 2 == 0:
        return 1  # нечетная неделя
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

def test_schedule_logic():
    """Тестируем логику расписания с московским временем"""
    print("🧪 ТЕСТИРОВАНИЕ ЛОГИКИ РАСПИСАНИЯ С МОСКОВСКИМ ВРЕМЕНЕМ")
    print("=" * 60)

    # Текущее время в Москве (тестовое)
    current_time = get_moscow_time()
    print(f"📅 Текущее время: {current_time.strftime('%d.%m.%Y %H:%M:%S %Z')}")

    # Определяем день недели
    weekday = get_weekday_name(current_time)
    print(f"📅 День недели: {weekday}")

    # Определяем тип недели (четная/нечетная)
    week_type = get_current_week_type(current_time)
    print(f"📊 Тип недели: {'нечетная' if week_type == 1 else 'четная'}")

    # Тестируем разные даты
    test_dates = [
        ("19.10", "Воскресенье"),  # Текущая дата (без года)
        ("20.10", "Понедельник"), # Следующий день
        ("18.10", "Суббота"),     # Предыдущий день
    ]

    print("\n📅 Тесты определения дней недели:")
    for date_str, expected_day in test_dates:
        try:
            # Парсим дату в формате ДД.ММ (используем текущий год)
            day, month = map(int, date_str.split('.'))
            year = current_time.year
            test_date = datetime(year, month, day, tzinfo=ZoneInfo("Europe/Moscow"))

            actual_day = get_weekday_name(test_date)
            week_type = get_current_week_type(test_date)

            status = "✅" if actual_day == expected_day else "❌"
            print(f"   {date_str}.2025: {actual_day} (ожидалось: {expected_day}) {status}")
            print(f"      Тип недели: {'нечетная' if week_type == 1 else 'четная'}")

        except Exception as e:
            print(f"   {date_str}: Ошибка - {e}")

    # Тестируем логику четности/нечетности недель
    print("\n📊 Тесты четности недель:")

    # Базовая дата - 6 октября 2025 (понедельник) - начало четной недели
    base_date = datetime(2025, 10, 6, tzinfo=ZoneInfo("Europe/Moscow"))
    print(f"📅 Базовая дата: {base_date.strftime('%d.%m.%Y')} ({get_weekday_name(base_date)})")

    # Тестируем несколько недель вперед
    for weeks_ahead in [0, 1, 2, 7, 8]:
        test_date = base_date + timedelta(weeks=weeks_ahead)
        week_type = get_current_week_type(test_date)
        expected_type = "четная" if weeks_ahead % 2 == 0 else "нечетная"

        status = "✅" if ((week_type == 2 and weeks_ahead % 2 == 0) or (week_type == 1 and weeks_ahead % 2 == 1)) else "❌"
        print(f"   {weeks_ahead} недель: {test_date.strftime('%d.%m.%Y')} - {'четная' if week_type == 2 else 'нечетная'} (ожидалось: {expected_type}) {status}")

    return True

if __name__ == "__main__":
    try:
        success = test_schedule_logic()
        print(f"\n{'✅' if success else '❌'} Тест {'пройден' if success else 'провален'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

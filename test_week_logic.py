#!/usr/bin/env python3
"""
Тест логики определения типа недели
"""

from datetime import datetime, timedelta
from main import get_current_week_type

def test_week_logic():
    """Тестируем логику определения типа недели"""
    print("🧪 Тестирование логики определения типа недели")
    print("=" * 50)

    # Базовая дата - 19 октября 2025 (воскресенье, конец нечетной недели)
    base_date = datetime(2025, 10, 19)

    print(f"Базовая дата: {base_date.strftime('%d.%m.%Y')} (воскресенье) - конец нечетной недели")
    print("Логика: четное количество недель с базовой даты = нечетная неделя")
    print("        нечетное количество недель с базовой даты = четная неделя")
    print()

    # Тестируем несколько дат
    test_dates = [
        datetime(2025, 10, 19),  # воскресенье - конец нечетной недели (0 недель)
        datetime(2025, 10, 20),  # понедельник - начало четной недели (1 день = 0 недель)
        datetime(2025, 10, 26),  # воскресенье через неделю - конец четной недели (7 дней = 1 неделя)
        datetime(2025, 10, 27),  # понедельник - начало нечетной недели (8 дней = 1 неделя)
        datetime(2025, 11, 2),   # воскресенье через 2 недели - конец нечетной недели (14 дней = 2 недели)
        datetime(2025, 11, 3),   # понедельник - начало четной недели (15 дней = 2 недели)
    ]

    for test_date in test_dates:
        days_since_base = (test_date - base_date).days
        weeks_since_base = days_since_base // 7
        week_type = get_current_week_type_for_date(test_date)

        print(f"Дата: {test_date.strftime('%d.%m.%Y')} ({test_date.strftime('%A', locale='ru')})")
        print(f"  Дней с базовой даты: {days_since_base}")
        print(f"  Полных недель: {weeks_since_base}")
        print(f"  Тип недели: {week_type}")
        print()

def get_current_week_type_for_date(date):
    """Определяет тип недели для заданной даты (упрощенная версия)"""
    base_date = datetime(2025, 10, 19)  # воскресенье - конец нечетной недели
    days_since_base = (date - base_date).days
    weeks_since_base = days_since_base // 7

    # Базовая дата - конец нечетной недели, поэтому:
    # Если прошло четное количество недель - нечетная неделя
    # Если прошло нечетное количество недель - четная неделя
    if weeks_since_base % 2 == 0:
        return 1  # нечетная неделя
    else:
        return 2  # четная неделя

if __name__ == "__main__":
    test_week_logic()

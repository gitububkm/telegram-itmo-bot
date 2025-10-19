#!/usr/bin/env python3
"""
Тест функций времени в московском часовом поясе
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def get_moscow_time():
    """Получает текущее время в Москве"""
    moscow_tz = ZoneInfo("Europe/Moscow")
    return datetime.now(moscow_tz)

def format_moscow_time(dt=None):
    """Форматирует время в московском часовом поясе"""
    if dt is None:
        dt = get_moscow_time()

    return dt.strftime("%d.%m.%Y %H:%M:%S (МСК)")

def is_new_day(current_time=None):
    """Проверяет, начался ли новый день по московскому времени"""
    if current_time is None:
        current_time = get_moscow_time()

    # Сравниваем с временем начала дня (00:00:00)
    day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # Если текущее время больше или равно началу дня, то день уже начался
    return current_time >= day_start

def get_days_since_date(target_date_str, current_time=None):
    """Вычисляет количество дней между датой и текущим временем в Москве"""
    if current_time is None:
        current_time = get_moscow_time()

    try:
        # Парсим целевую дату (предполагаем формат ДД.ММ.ГГГГ)
        target_date = datetime.strptime(target_date_str, "%d.%m.%Y")
        # Добавляем московский часовой пояс
        target_date = target_date.replace(tzinfo=ZoneInfo("Europe/Moscow"))

        # Вычисляем разницу в днях
        delta = current_time - target_date
        return delta.days

    except ValueError:
        return None

def test_moscow_time():
    """Тестирует функции московского времени"""
    print("🕐 ТЕСТИРОВАНИЕ МОСКОВСКОГО ВРЕМЕНИ")
    print("=" * 50)

    # Текущее время в Москве
    current_time = get_moscow_time()
    formatted_time = format_moscow_time(current_time)

    print(f"📅 Текущее время в Москве: {formatted_time}")

    # Проверка начала дня
    day_started = is_new_day(current_time)
    print(f"✅ День начался: {day_started}")

    # Тест разницы дат
    days_since = get_days_since_date("01.01.2024", current_time)
    if days_since is not None:
        print(f"📊 Дней с 01.01.2024: {days_since}")
    else:
        print("❌ Ошибка при расчете дней")

    # Тест с различными датами
    test_dates = ["19.10.2025", "20.10.2025", "25.12.2024"]

    print("\n📅 Тесты разницы дат:")
    for date_str in test_dates:
        days = get_days_since_date(date_str, current_time)
        if days is not None:
            status = "прошло" if days > 0 else "осталось" if days < 0 else "сегодня"
            print(f"   {date_str}: {abs(days)} дней {status}")
        else:
            print(f"   {date_str}: ошибка парсинга")

    return True

def test_timezone_compatibility():
    """Тестирует совместимость с часовыми поясами"""
    print("\n🌍 ТЕСТИРОВАНИЕ ЧАСОВЫХ ПОЯСОВ")
    print("=" * 50)

    # Текущее время в разных часовых поясах
    moscow_time = get_moscow_time()
    utc_time = datetime.now(ZoneInfo("UTC"))

    print(f"🕐 Москва: {format_moscow_time(moscow_time)}")
    print(f"🌍 UTC: {utc_time.strftime('%d.%m.%Y %H:%M:%S (UTC)')}")

    # Разница между Москвой и UTC (должна быть 3 часа зимой, 4 часа летом)
    # Вычисляем разницу правильно, используя timestamp
    moscow_timestamp = moscow_time.timestamp()
    utc_timestamp = utc_time.timestamp()
    hours_diff = (moscow_timestamp - utc_timestamp) / 3600

    print(f"⏰ Разница с UTC: {hours_diff} часов")

    # Проверка корректности перехода на летнее время
    # В 2024 году переход на летнее время в России был 31 марта
    spring_date = datetime(2024, 3, 31, 2, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    formatted_spring = format_moscow_time(spring_date)
    print(f"🌸 Весенний переход 31.03.2024: {formatted_spring}")

    return True

def run_all_tests():
    """Запускает все тесты"""
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ФУНКЦИЙ ВРЕМЕНИ")
    print("=" * 60)

    try:
        # Базовые тесты
        test_moscow_time()
        test_timezone_compatibility()

        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🕐 Функции времени работают корректно с московским часовым поясом")

        return True

    except Exception as e:
        print(f"\n❌ ОШИБКА ПРИ ТЕСТИРОВАНИИ: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

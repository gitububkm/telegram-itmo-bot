#!/usr/bin/env python3
"""
Тест исправленной логики определения типа недели
"""

import sys
sys.path.append('.')

from datetime import datetime
from main import get_current_week_type

def test_week_logic():
    """Тестируем исправленную логику"""
    print("🧪 Тестирование исправленной логики")
    print("=" * 50)

    test_cases = [
        (datetime(2025, 10, 20), "четная неделя"),
        (datetime(2025, 10, 27), "нечетная неделя"),
        (datetime(2025, 11, 3), "четная неделя"),
        (datetime(2025, 11, 10), "нечетная неделя"),
    ]

    for test_date, expected in test_cases:
        week_type = get_current_week_type(test_date)
        week_name = "нечетная" if week_type == 1 else "четная"

        status = "✅" if (week_name == expected) else "❌"
        print(f"{status} {test_date.strftime('%d.%m.%Y')}: {week_name} неделя (ожидаемая: {expected})")

if __name__ == "__main__":
    test_week_logic()

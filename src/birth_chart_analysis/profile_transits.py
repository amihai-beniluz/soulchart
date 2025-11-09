#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
פרופיילר פשוט לזיהוי בקבוקי צוואר בביצועים
"""

import cProfile
import pstats
import io
from pstats import SortKey


def profile_transit_analysis():
    """
    מריץ את הניתוח עם פרופיילר
    """
    # הוסף את הנתיב לפרויקט
    # sys.path.insert(0, '/path/to/your/project')

    # ייבא את הפונקציה הראשית
    from src.cli.transit_main import main

    # צור פרופיילר
    profiler = cProfile.Profile()

    print("🔍 מתחיל פרופיילינג...")
    print("=" * 80)

    # הרץ עם פרופיילר
    profiler.enable()

    try:
        main()  # הפונקציה הראשית שלך
    except SystemExit:
        pass  # התוכנה מסיימת באופן תקין

    profiler.disable()

    print("\n" + "=" * 80)
    print("📊 תוצאות הפרופיילינג:")
    print("=" * 80)

    # צור דוח
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)

    # מיין לפי זמן מצטבר (cumulative time)
    stats.sort_stats(SortKey.CUMULATIVE)

    # הצג את 20 הפונקציות הכי איטיות
    print("\n🐌 20 הפונקציות שלוקחות הכי הרבה זמן:")
    print("-" * 80)
    stats.print_stats(20)

    # שמור לקובץ
    with open('profile_results.txt', 'w', encoding='utf-8') as f:
        stats.stream = f
        stats.print_stats()

    print("\n✅ דוח מלא נשמר ב: profile_results.txt")

    # ניתוח ממוקד
    print("\n" + "=" * 80)
    print("🎯 ניתוח ממוקד - פונקציות שלך:")
    print("=" * 80)

    stats.stream = io.StringIO()
    stats.print_stats('ChartAnalysis|TransitCalculator|CalculationEngine')
    print(stats.stream.getvalue())


if __name__ == '__main__':
    profile_transit_analysis()
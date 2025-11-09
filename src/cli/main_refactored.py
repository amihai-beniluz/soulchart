"""
סקריפט CLI ראשי למערכת SoulChart - ניתוח שמות ומפות לידה.
"""
import os
import sys
from datetime import datetime

# הוספת src לנתיב
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ..birth_chart_analysis.ChartAnalysis import ChartAnalysis
from ..birth_chart_analysis.BirthChartDrawer import draw_and_save_chart
from ..birth_chart_analysis.CalculationEngine import calculate_chart_positions
from ..name_analysis.NameAnalysis import NameAnalysis
from ..user import User
from ..core import write_results_to_file, get_interpretation_choice

# הגדרת תיקיות
MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
NAMES_DIR = os.path.join(PROJECT_DIR, 'output', 'names')
CHARTS_DIR = os.path.join(PROJECT_DIR, 'output', 'charts')


def get_user_input_combined():
    """אוסף את כל נתוני המשתמש: שם, תאריך, שעה, מיקום וניקוד."""
    from ..core.user_input import get_validated_date, get_validated_time

    print("\n--- איסוף נתוני משתמש ---")

    name = input("הכנס את השם שלך: ").strip()

    # תאריך לידה
    birthdate = get_validated_date("הכנס תאריך לידה (פורמט YYYY-MM-DD): ")

    # שעת לידה (אופציונלי)
    birthtime = get_validated_time(
        "הכנס שעת לידה (פורמט HH:MM, השאר ריק אם לא ידוע): ",
        is_optional=True
    )

    # מיקום
    print("\n--- נתוני מיקום ---")
    location = None
    location_str = input(
        "הכנס מיקום לידה (פורמט Latitude, Longitude - לדוגמה 32.08, 34.78. אם אין: לחץ Enter): "
    ).strip()

    if location_str:
        try:
            lat_str, lon_str = location_str.split(',')
            location = (float(lat_str.strip()), float(lon_str.strip()))
        except ValueError:
            print("⚠️ פורמט קואורדינטות לא תקין. נמשיך ללא מיקום מדויק.")

    # ניקוד
    nikud_dict = {}
    print("\n--- איסוף ניקוד השם ---")
    for i, letter in enumerate(name):
        nikud = input(f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, השאר ריק): ").strip()
        if nikud:
            nikud_dict[i + 1] = nikud

    return User(name, birthdate, birthtime, location), nikud_dict


def main():
    """נקודת הכניסה הראשית."""
    import traceback

    user, nikud_dict = get_user_input_combined()

    # 1. ניתוח שם
    print("\n--- ביצוע ניתוח שם ---")
    try:
        analysis = NameAnalysis(user.name, nikud_dict)
        name_result = analysis.analyze_name()
        write_results_to_file(NAMES_DIR, user.name, name_result, "_name.txt")
    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח שם: {e}")
        traceback.print_exc()

    # 2. ניתוח מפת לידה
    print("\n--- ביצוע ניתוח מפת לידה ---")
    try:
        # בדיקה שיש נתונים מספיקים
        if not user.location or not user.birthtime:
            print(f"⚠️ חסרים נתונים לחישוב מפה מדויקת (שעה או מיקום)")
            return

        # בחירת פרשנות
        is_interpreted = get_interpretation_choice()

        chart_analysis = ChartAnalysis(user)

        # חישוב נתוני המפה
        birth_datetime = datetime.combine(user.birthdate, user.birthtime)
        chart_positions = calculate_chart_positions(
            birth_datetime,
            user.location[0],  # Latitude
            user.location[1]  # Longitude
        )

        # ביצוע ניתוח טקסטואלי
        report_text = chart_analysis.analyze_chart(is_interpreted)

        # שמירת דוח
        suffix = "_chart_interpreted.txt" if is_interpreted else "_chart_positions.txt"
        write_results_to_file(CHARTS_DIR, user.name, report_text, suffix)

        # ציור ושמירת מפת הלידה כתמונה
        image_filename = os.path.join(CHARTS_DIR, f"{user.name}_chart.png")
        draw_and_save_chart(chart_positions, user, image_filename)

        print(f"\n✅ ניתוח מפת לידה הושלם!")
        print(f"   📄 דוח: {CHARTS_DIR}/{user.name}{suffix}")
        print(f"   🖼️  תמונה: {image_filename}")

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח מפת לידה: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

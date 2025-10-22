import os
from datetime import datetime

from birth_chart_analysis.ChartAnalysis import ChartAnalysis
from birth_chart_analysis.ChartDrawer import draw_and_save_chart
from birth_chart_analysis.CalculationEngine import calculate_chart_positions
from name_analysis.NameAnalysis import NameAnalysis
from user import User
from utils import write_results_to_file, get_validated_date, get_validated_time

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir))
NAMES_DIR = os.path.join(PROJECT_DIR, os.path.join('output', 'names'))
CHARTS_DIR = os.path.join(PROJECT_DIR, os.path.join('output', 'charts'))


def get_user_input():
    """אוסף את כל נתוני המשתמש: שם, תאריך, שעה ומיקום."""
    print("\n--- איסוף נתוני משתמש ---")

    name = input("הכנס את השם שלך: ").strip()

    # 1. תאריך לידה (חובה) - שימוש בפונקציית עזר
    birthdate = get_validated_date("הכנס תאריך לידה (פורמט YYYY-MM-DD): ")

    # 2. שעת לידה (אופציונלי) - שימוש בפונקציית עזר
    birthtime = get_validated_time(
        "הכנס שעת לידה (פורמט HH:MM, השאר ריק אם לא ידוע): ",
        is_optional=True
    )

    # 3. מיקום (חובה למפה) - שימוש בפונקציית עזר
    print("\n--- נתוני מיקום ---")
    location = input(
        "הכנס מיקום לידה (אופציונלי, פורמט Latitude, Longitude - לדוגמה 32.08, 34.78. אם אין: לחץ Enter): ").strip()
    if location:
        try:
            lat_str, lon_str = location.split(',')
            location = (float(lat_str.strip()), float(lon_str.strip()))
        except ValueError:
            print("⚠️ פורמט קואורדינטות לא תקין. נמשיך ללא מיקום מדויק.")

    # 4. קלט ניקוד
    nikud_dict = {}
    print("\n--- איסוף ניקוד השם ---")
    for i, letter in enumerate(name):
        nikud = input(f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, כתוב ריק) ")
        if nikud:  # אם הוזן ניקוד
            nikud_dict[i + 1] = nikud  # המיקום הוא אינדקס + 1

    return User(name, birthdate, birthtime, location), nikud_dict


def main():
    import traceback
    user, nikud_dict = get_user_input()

    # 1. ניתוח שם (הפונקציה הקיימת)
    print("\n--- ביצוע ניתוח שם ---")
    try:
        analysis = NameAnalysis(user.name, nikud_dict)
        name_result = analysis.analyze_name()
        write_results_to_file(NAMES_DIR, user.name, name_result, "_name.txt")
    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח שם: {e}")

    # 2. ניתוח מפת לידה
    print("\n--- ביצוע ניתוח מפת לידה ---")
    try:
        # בדיקה שיש נתונים מספיקים
        if not user.location or not user.birthtime:
            print(f"⚠️ חסרים נתונים לחישוב מפה מדויקת (שעה או מיקום)")
            return

        chart_analysis = ChartAnalysis(user)

        # ✅ חישוב נתוני המפה הגולמיים (Planets, HouseCusps, Aspects)
        birth_datetime = datetime.combine(user.birthdate, user.birthtime)
        chart_positions = calculate_chart_positions(
            birth_datetime,
            user.location[0],  # Latitude
            user.location[1]  # Longitude
        )

        print(f"\n✅ חישוב מפה הושלם:")
        print(f"   📊 {len(chart_positions.get('Planets', {}))} פלנטות")
        print(f"   🏠 {len(chart_positions.get('HouseCusps', {}))} בתים")
        print(f"   🔗 {len(chart_positions.get('Aspects', []))} אספקטים")

        # ביצוע ניתוח טקסטואלי
        report_text = chart_analysis.analyze_chart(True)
        write_results_to_file(CHARTS_DIR, user.name, report_text, "_chart.txt")

        # ציור ושמירת מפת הלידה כתמונה
        image_filename = os.path.join(CHARTS_DIR, f"{user.name}_chart.png")
        draw_and_save_chart(chart_positions, user, image_filename)

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח מפת לידה: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

"""
סקריפט CLI ראשי למערכת SoulChart - ניתוח שמות ומפות לידה.
"""
import os
import sys
from datetime import datetime

# הוספת src לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from chart_analysis.ChartAnalysis import ChartAnalysis
from chart_analysis.ChartDrawer import draw_and_save_chart
from chart_analysis.CalculationEngine import calculate_chart_positions
from name_analysis.NameAnalysis import NameAnalysis
from names_manager import NamesManager, nikud_dict_from_nikud_name
from user import User
from core import write_results_to_file, get_interpretation_choice

# הגדרת תיקיות
MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
NAMES_DIR = os.path.join(PROJECT_DIR, 'output', 'names')
CHARTS_DIR = os.path.join(PROJECT_DIR, 'output', 'charts')
NAMES_FILE = os.path.join(PROJECT_DIR, 'data', 'names.txt')

# אתחול מנהל השמות
names_manager = NamesManager(NAMES_FILE)


def get_nikud_for_name(name: str):
    """
    מקבל ניקוד לשם - אוטומטית מהמאגר או ידנית מהמשתמש.

    Args:
        name: השם ללא ניקוד

    Returns:
        דיקשנרי ניקוד
    """
    nikud_name, nikud_options = names_manager.get_nikud_for_name(name)

    if nikud_name:
        # שם עם ניקוד יחיד
        print(f"\n✅ שמך מופיע במערכת עם הניקוד הבא: {nikud_name}")
        choice = input("האם הניקוד נכון? (כן/לא): ").strip().lower()

        if choice in ['כן', 'yes', 'y', 'כ'] or not choice:
            return nikud_dict_from_nikud_name(name, nikud_name)
        else:
            print("אנא הזן את ניקוד שמך באופן ידני:")
            nikud_dict = get_manual_nikud(name)
            # עדכון המאגר עם הניקוד החדש
            manual_nikud_name = apply_nikud_to_name(name, nikud_dict)
            names_manager.add_or_update_name(name, manual_nikud_name)
            print(f"✅ הניקוד עודכן במערכת!")
            return nikud_dict

    elif len(nikud_options) > 1:
        # מספר אפשרויות ניקוד
        print(f"\n⚠️ שמך מופיע במערכת עם {len(nikud_options)} אפשרויות ניקוד:")
        for i, option in enumerate(nikud_options, 1):
            print(f"{i}. {option}")

        print(f"{len(nikud_options) + 1}. הזן ניקוד ידנית")

        while True:
            try:
                choice = int(input("\nבחר מספר אפשרות: ").strip())
                if 1 <= choice <= len(nikud_options):
                    selected_nikud = nikud_options[choice - 1]
                    return nikud_dict_from_nikud_name(name, selected_nikud)
                elif choice == len(nikud_options) + 1:
                    nikud_dict = get_manual_nikud(name)
                    manual_nikud_name = apply_nikud_to_name(name, nikud_dict)
                    names_manager.add_or_update_name(name, manual_nikud_name)
                    print(f"✅ הניקוד נוסף למערכת!")
                    return nikud_dict
                else:
                    print("⚠️ בחירה לא תקינה, נסה שוב.")
            except ValueError:
                print("⚠️ נא להזין מספר.")

    else:
        # השם לא נמצא במאגר
        print(f"\n⚠️ שמך לא מופיע במאגר השמות הקיימים.")
        print("אנא הזן את ניקוד שמך באופן ידני:")
        nikud_dict = get_manual_nikud(name)
        manual_nikud_name = apply_nikud_to_name(name, nikud_dict)
        names_manager.add_or_update_name(name, manual_nikud_name)
        print(f"✅ שמך נוסף למאגר עם הניקוד שהוזן!")
        return nikud_dict


def get_manual_nikud(name: str) -> dict:
    """
    אוסף ניקוד באופן ידני מהמשתמש.

    Args:
        name: השם

    Returns:
        דיקשנרי ניקוד
    """
    nikud_dict = {}
    print("\n--- איסוף ניקוד השם ---")
    for i, letter in enumerate(name):
        nikud = input(f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, השאר ריק): ").strip()
        if nikud:
            nikud_dict[i + 1] = nikud
    return nikud_dict


def apply_nikud_to_name(name: str, nikud_dict: dict) -> str:
    """
    מחבר שם עם דיקשנרי ניקוד ליצירת שם מנוקד.

    Args:
        name: השם המקורי
        nikud_dict: דיקשנרי הניקוד (1-based indices)

    Returns:
        שם מנוקד
    """
    result = []
    for i, char in enumerate(name, 1):
        result.append(char)
        if i in nikud_dict:
            result.append(nikud_dict[i])
    return ''.join(result)


def get_user_input_combined():
    """אוסף את כל נתוני המשתמש: שם, תאריך, שעה, מיקום וניקוד."""
    from core.user_input import get_validated_date, get_validated_time

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

    # ניקוד - שימוש במנהל השמות
    nikud_dict = get_nikud_for_name(name)

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
            user.location[1]   # Longitude
        )

        # ביצוע ניתוח טקסטואלי
        report_text = chart_analysis.analyze_chart(is_interpreted)

        # שמירת דוח
        suffix = "_chart_interpreted.txt" if is_interpreted else "_chart_positions.txt"
        write_results_to_file(CHARTS_DIR, user.name, report_text, suffix)

        # ציור ושמירת מפת הלידה כתמונה
        image_filename = os.path.join(CHARTS_DIR, f"{user.name}_chart.png")
        draw_and_save_chart(chart_positions, user, image_filename)

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח מפת לידה: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

import os
import textwrap
from datetime import datetime
from user import User  # הנחה: user.py נמצא ב-src/
from name_analysis.NameAnalysis import NameAnalysis  # ייבוא מהחבילה המאורגנת
from birth_chart_analysis.ChartAnalysis import ChartAnalysis  # ייבוא מהחבילה החדשה

MODULE_DIR  = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir))
NAMES_DIR    = os.path.join(PROJECT_DIR, 'names')
CHARTS_DIR    = os.path.join(PROJECT_DIR, 'charts')

def get_user_input():
    """אוסף את כל נתוני המשתמש: שם, תאריך, שעה ומיקום."""
    print("\n--- איסוף נתוני משתמש ---")

    name = input("הכנס את השם שלך: ").strip()

    # 1. תאריך לידה (חובה)
    while True:
        try:
            birthdate_str = input("הכנס תאריך לידה (פורמט YYYY-MM-DD): ").strip()
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            break
        except ValueError:
            print("❌ פורמט תאריך לא תקין. אנא הזן מחדש (YYYY-MM-DD).")

    # 2. שעת לידה (אופציונלי אך נדרש למפה)
    birthtime = None
    birthtime_str = input("הכנס שעת לידה (אופציונלי, פורמט HH:MM - לדוגמה 14:30. אם אין: לחץ Enter): ").strip()
    if birthtime_str:
        try:
            birthtime = datetime.strptime(birthtime_str, '%H:%M').time()
        except ValueError:
            print("⚠️ פורמט שעת לידה לא תקין. נמשיך ללא שעה מדויקת.")

    # 3. מיקום לידה (אופציונלי אך נדרש למפה) - קואורדינטות
    location = None
    location_str = input(
        "הכנס מיקום לידה (אופציונלי, פורמט Latitude, Longitude - לדוגמה 32.08, 34.78. אם אין: לחץ Enter): ").strip()
    if location_str:
        try:
            lat_str, lon_str = location_str.split(',')
            location = (float(lat_str.strip()), float(lon_str.strip()))
        except ValueError:
            print("⚠️ פורמט קואורדינטות לא תקין. נמשיך ללא מיקום מדויק.")

    # 4. קלט ניקוד (כמו קודם)
    nikud_dict = {}
    print("\n--- איסוף ניקוד השם ---")
    for i, letter in enumerate(name):
        nikud = input(f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, כתוב ריק) ")
        if nikud:  # אם הוזן ניקוד
            nikud_dict[i + 1] = nikud  # המיקום הוא אינדקס + 1

    return User(name, birthdate, birthtime, location), nikud_dict


def write_results_to_file(output_dir: str, name: str, results: list, file_suffix: str = ".txt", wrap_text: bool = True):
    """פונקציה לשמירת פלט לקובץ, כולל יצירת התיקייה."""

    # יצירת התיקייה אם אינה קיימת
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"❌ אירעה שגיאה קריטית ביצירת התיקייה '{output_dir}': {e}")
        return

    output_path = os.path.join(output_dir, name + file_suffix)

    # כתיבת הפלט לקובץ
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            if wrap_text:
                # עטיפת טקסט (למפות לידה)
                wrapper = textwrap.TextWrapper(width=150)
                file.write("\n")
                for line in results:
                    # בדיקת שורות ריקות לפני עטיפה
                    if not line or not line.strip():
                        file.write("\n")
                        continue

                    wrapped_lines = wrapper.wrap(text=line)
                    for wrapped_line in wrapped_lines:
                        file.write(wrapped_line + "\n")
            else:
                # כתיבה ישירה ללא עטיפה (לשמות)
                for i, line in enumerate(results):
                    # הסרת \n מיותרים מסוף השורה
                    clean_line = line.rstrip('\n')
                    file.write(clean_line + "\n")

                    # הוספת שורה ריקה אחרי מפריד (אבל לא אחרי המפריד האחרון)
                    if clean_line.strip() == "--------" and i < len(results) - 1:
                        file.write("\n")

        print(f"\n✅ התוצאה נשמרה בהצלחה בקובץ: {output_path}")

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בכתיבה לקובץ {output_path}: {e}")

def main():
    user, nikud_dict = get_user_input()

    # 1. ניתוח שם (הפונקציה הקיימת)
    print("\n--- ביצוע ניתוח שם ---")
    try:
        analysis = NameAnalysis(user.name, nikud_dict)
        name_result = analysis.analyze_name(False)
        write_results_to_file(NAMES_DIR, user.name, name_result, "_name.txt")
    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח שם: {e}")

    # 2. ניתוח מפת לידה (הפונקציה החדשה) - כעת מחוץ ל-except!
    print("\n--- ביצוע ניתוח מפת לידה ---")
    try:
        chart_analysis = ChartAnalysis(user)
        chart_result = chart_analysis.analyze_chart(True)
        write_results_to_file(CHARTS_DIR, user.name, chart_result, "_chart.txt")
    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח מפת לידה: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

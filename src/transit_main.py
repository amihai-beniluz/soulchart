import os
from datetime import datetime
import traceback

# ייבוא מהחבילות
from user import User
from birth_chart_analysis.ChartAnalysis import ChartAnalysis
from utils import write_results_to_file, get_validated_date, get_validated_time, get_location_input

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir))
TRANSITS_DIR = os.path.join(PROJECT_DIR, os.path.join('output', 'transits'))  # <-- נתיב חדש לטרנזיטים


def get_birth_data_input():
    """אוסף את נתוני הלידה הנדרשים (תאריך, שעה, מיקום)."""
    print("\n--- איסוף נתוני לידה (נטאל) ---\n")

    # שם משתמש (חובה לצורך שמירת הקובץ, אפשר להשאיר 'User' כברירת מחדל)
    name = input("הכנס שם המשתמש (לצורך שמירת הקובץ): ").strip() or "User"

    # 1. תאריך לידה (חובה)
    birthdate = get_validated_date("הכנס תאריך לידה (פורמט YYYY-MM-DD): ")

    # 2. שעת לידה (חובה לחישוב מדויק של מעברים)
    birthtime = get_validated_time("הכנס שעת לידה (פורמט HH:MM): ", is_optional=False)

    # 3. מיקום לידה (חובה)
    print("\n--- נתוני מיקום לידה ---")
    try:
        location_str = input("הכנס את מקום הלידה (Latitude, Longitude - לחישוב מדויק של קווי יתד המעבר): ").strip()
        lat_str, lon_str = location_str.split(',')
        latitude = float(lat_str.strip())
        longitude = float(lon_str.strip())
        location = (latitude, longitude)

    except ValueError:
        print("❌ פורמט מיקום לא תקין. אנא הזן מחדש (Latitude, Longitude).")
    except Exception:
        print("❌ פורמט מיקום לא תקין. אנא הזן מחדש (Latitude, Longitude).")

    user = User(name, birthdate, birthtime, location)
    return user


def get_current_location_input():
    """אוסף את נתוני המיקום הנוכחי לצורך חישוב הטרנזיט."""
    print("\n--- איסוף מיקום נוכחי לחישוב מעברים ---\n")

    while True:
        try:
            location_str = input("הכנס מיקום נוכחי (Latitude, Longitude - לחישוב מדויק של קווי יתד המעבר): ").strip()
            lat_str, lon_str = location_str.split(',')
            latitude = float(lat_str.strip())
            longitude = float(lon_str.strip())
            return (latitude, longitude)
        except ValueError:
            print("❌ פורמט מיקום לא תקין. אנא הזן מחדש (Latitude, Longitude).")
        except Exception:
            print("❌ פורמט מיקום לא תקין. אנא הזן מחדש (Latitude, Longitude).")


def main():
    # 1. איסוף נתוני לידה (נטאל)
    user = get_birth_data_input()

    # 2. איסוף נתוני מיקום נוכחי
    current_location = get_current_location_input()

    # 3. ניתוח מעברים (טרנזיטים) בלבד
    print("\n--- ביצוע ניתוח מעברים (טרנזיטים) ---\n")
    try:
        # יצירת מופע חדש של ChartAnalysis (עבור ה-user עם נתוני הלידה)
        chart_analysis = ChartAnalysis(user)

        # הקריאה למודול החדש - עם העברת המיקום הנוכחי כפרמטר
        transit_result = chart_analysis.analyze_transits_and_aspects(current_location, is_interpreted=True)

        # שמירת הדוח בתיקייה transits
        # השם יהיה: Transit User_transits.txt
        filename_prefix = f"Natal_{user.birthdate}_at_{user.birthtime.hour}-{user.birthtime.minute}_Transit_to_{datetime.now().strftime('%Y-%m-%d')}"
        write_results_to_file(TRANSITS_DIR, filename_prefix, transit_result, ".txt")

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח מעברים: {e}")
        traceback.print_exc()  # הדפסת עקבת המחסנית לאיתור שגיאות

    print("\n🎉 ניתוח המעברים הסתיים בהצלחה!")


if __name__ == '__main__':
    # ודא שכל התיקיות קיימות לפני ההפעלה
    os.makedirs(TRANSITS_DIR, exist_ok=True)
    main()

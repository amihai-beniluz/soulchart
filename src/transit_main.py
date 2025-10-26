import os
from datetime import datetime
import traceback

# ייבוא מהחבילות
from user import User
from birth_chart_analysis.ChartAnalysis import ChartAnalysis
from utils import write_results_to_file, get_validated_date, get_validated_time, get_location_input
from birth_chart_analysis.CalculationEngine import calculate_chart_positions, calculate_current_positions # ✅ ייבוא זה
from birth_chart_analysis.BirthChartDrawer import draw_and_save_biwheel_chart # ✅ ייבוא זה
# ...

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


# transit_main.py - changes in the main function

def main():
    # TODO: לחשב ולהציג זמן רלוונטיות היבט וכמה ממנו עבר

    # 1. איסוף נתוני לידה (נטאל)
    user = get_birth_data_input()

    # 2. איסוף נתוני מיקום נוכחי
    current_location = get_current_location_input()

    # 3. ניתוח מעברים (טרנזיטים) בלבד
    print("\n--- ביצוע ניתוח מעברים (טרנזיטים) ---\n")
    try:
        # יצירת מופע של ChartAnalysis (עבור הניתוח הטקסטואלי)
        chart_analysis = ChartAnalysis(user)

        # 1. קבלת נתוני נטאל גולמיים (Natal Raw Data) - חישוב ישיר
        birth_datetime = datetime.combine(user.birthdate, user.birthtime)
        natal_chart_data = calculate_chart_positions(
            birth_datetime,
            user.location[0],
            user.location[1]
        )

        # 2. קבלת נתוני מעבר גולמיים (Transit Raw Data) - קריאה ישירה למנוע החישוב
        current_datetime = datetime.now()
        transit_chart_data = calculate_current_positions(
            current_datetime,
            current_location[0],
            current_location[1]
        )

        # 3. ביצוע הניתוח הטקסטואלי (הקריאה המקורית, ללא שינוי)
        transit_result = chart_analysis.analyze_transits_and_aspects(current_location, is_interpreted=False)

        # ... (שמירת הדוח הטקסטואלי)
        birth_time_str = user.birthtime.strftime('%H-%M') if user.birthtime else 'Unknown'
        filename_prefix = f"Natal_{user.birthdate}_at_{birth_time_str}_Transit_to_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"

        write_results_to_file(TRANSITS_DIR, filename_prefix, transit_result, ".txt")

        # 4. ציור מפת המעברים (Bi-Wheel)
        image_filename = os.path.join(TRANSITS_DIR, f"{filename_prefix}_biwheel.png")

        draw_and_save_biwheel_chart(
            natal_chart_data,  # נתונים פנימיים (שחושבו כרגע)
            transit_chart_data,  # נתונים חיצוניים (שחושבו כרגע)
            user,
            current_datetime,
            image_filename
        )

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח מעברים: {e}")
        traceback.print_exc()

    print("\n🎉 ניתוח המעברים הסתיים בהצלחה!")


if __name__ == '__main__':
    # ודא שכל התיקיות קיימות לפני ההפעלה
    os.makedirs(TRANSITS_DIR, exist_ok=True)
    main()

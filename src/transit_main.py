import os
from datetime import datetime
import textwrap
import traceback

# ייבוא מהחבילות
from user import User
from birth_chart_analysis.ChartAnalysis import ChartAnalysis

# אין צורך לייבא את NameAnalysis
# אין צורך לייבא את NameAnalysis

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir))
TRANSITS_DIR = os.path.join(PROJECT_DIR, 'transits')  # <-- נתיב חדש לטרנזיטים


def get_birth_data_input():
    """אוסף את נתוני הלידה הנדרשים (תאריך, שעה, מיקום)."""
    print("\n--- איסוף נתוני לידה (נטאל) ---\n")

    # 1. תאריך לידה (חובה)
    while True:
        try:
            birthdate_str = input("הכנס תאריך לידה (פורמט YYYY-MM-DD): ").strip()
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            break
        except ValueError:
            print("❌ פורמט תאריך לא תקין. אנא הזן מחדש (YYYY-MM-DD).")

    # 2. שעת לידה (חובה לחישוב מדויק)
    while True:
        try:
            birthtime_str = input("הכנס שעת לידה (פורמט HH:MM, חובה למפה מדויקת): ").strip()
            birthtime = datetime.strptime(birthtime_str, '%H:%M').time()
            break
        except ValueError:
            print("❌ פורמט שעה לא תקין. אנא הזן מחדש (HH:MM).")

    # 3. מיקום לידה (Latitude, Longitude)
    while True:
        try:
            location_str = input("הכנס מיקום לידה (Latitude, Longitude - לדוגמה: 32.08, 34.78): ").strip()
            lat_str, lon_str = location_str.split(',')
            latitude = float(lat_str.strip())
            longitude = float(lon_str.strip())
            location = (latitude, longitude)
            break
        except ValueError:
            print("❌ פורמט מיקום לא תקין. אנא הזן מחדש (Latitude, Longitude).")
        except Exception:
            print("❌ פורמט מיקום לא תקין. אנא הזן מחדש (Latitude, Longitude).")

    # 4. יצירת מופע של User עם נתוני לידה
    # שם: 'Transit User' ישמש כערך ברירת מחדל
    user = User(name='Transit User', birthdate=birthdate, birthtime=birthtime, location=location)

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


def write_results_to_file(directory: str, filename_prefix: str, results: list, suffix: str):
    """פונקציה גנרית לשמירת תוצאות לקובץ."""
    os.makedirs(directory, exist_ok=True)
    output_path = os.path.join(directory, f"{filename_prefix}{suffix}")

    try:
        with open(output_path, 'w', encoding='utf-8') as file:
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
        transit_result = chart_analysis.analyze_transits_and_aspects(current_location)

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
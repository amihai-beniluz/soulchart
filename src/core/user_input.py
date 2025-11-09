"""
מודול לניהול קלט ואימות נתוני משתמש.
מרכז את כל פונקציות הקלט והאימות במקום אחד.
"""
import re
from datetime import datetime


def get_validated_date(prompt: str) -> datetime.date:
    """
    אוסף ומאמת תאריך מהמשתמש בפורמט YYYY-MM-DD.

    Args:
        prompt: ההודעה להצגה למשתמש

    Returns:
        datetime.date: אובייקט תאריך מאומת
    """
    while True:
        try:
            date_str = input(prompt).strip()
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                raise ValueError("פורמט שגוי")

            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            return date_obj
        except ValueError:
            print("❌ פורמט תאריך לא תקין. אנא הזן מחדש (YYYY-MM-DD).")


def get_validated_time(prompt: str, is_optional: bool = False) -> datetime.time:
    """
    אוסף ומאמת שעה מהמשתמש בפורמט HH:MM.

    Args:
        prompt: ההודעה להצגה למשתמש
        is_optional: האם ניתן להשאיר ריק

    Returns:
        datetime.time או None: אובייקט זמן מאומת או None אם אופציונלי וריק
    """
    while True:
        time_str = input(prompt).strip()

        if is_optional and not time_str:
            return None

        try:
            if not re.match(r'^\d{2}:\d{2}$', time_str):
                raise ValueError

            time_obj = datetime.strptime(time_str, '%H:%M').time()
            return time_obj
        except ValueError:
            optional_hint = ", השאר ריק אם לא ידוע" if is_optional else ""
            print(f"❌ פורמט שעה לא תקין. אנא הזן מחדש (HH:MM){optional_hint}.")


def get_location_input(prompt_lat: str = None, prompt_lon: str = None,
                       single_prompt: str = None) -> tuple:
    """
    אוסף קואורדינטות (רוחב ואורך).

    Args:
        prompt_lat: הודעה לרוחב (אם מופרד)
        prompt_lon: הודעה לאורך (אם מופרד)
        single_prompt: הודעה אחת לשני הערכים (Lat, Lon)

    Returns:
        tuple: (latitude, longitude)
    """
    while True:
        try:
            if single_prompt:
                location_str = input(single_prompt).strip()
                lat_str, lon_str = location_str.split(',')
                latitude = float(lat_str.strip())
                longitude = float(lon_str.strip())
            else:
                latitude_str = input(prompt_lat).strip()
                longitude_str = input(prompt_lon).strip()
                latitude = float(latitude_str)
                longitude = float(longitude_str)

            # בדיקות טווח
            if not (-90 <= latitude <= 90):
                raise ValueError("ערך רוחב (Latitude) חייב להיות בין -90 ל-90.")
            if not (-180 <= longitude <= 180):
                raise ValueError("ערך אורך (Longitude) חייב להיות בין -180 ל-180.")

            return (latitude, longitude)

        except ValueError as e:
            print(f"❌ קלט לא תקין: {e}. אנא הזן מספרים עשרוניים תקינים.")


def get_interpretation_choice() -> bool:
    """
    שואל את המשתמש האם רוצה פרשנות אסטרולוגית מלאה.

    Returns:
        bool: True אם רוצה פרשנות, False אחרת
    """
    print("\n" + "=" * 80)
    print("האם ברצונך לקבל פרשנות אסטרולוגית מלאה?")
    print("=" * 80)
    print("כן (1) - דוח מפורט עם הסברים והנחיות אסטרולוגיות")
    print("לא (2) - רק מיקומי כוכבים והיבטים ללא פרשנות (ברירת מחדל)")
    print("=" * 80)

    while True:
        choice = input("\nהכנס בחירה (1/2, ברירת מחדל: 2): ").strip()
        if choice == '1':
            return True
        elif choice in ['', '2']:
            return False
        print("❌ בחירה לא תקינה. אנא הזן 1 או 2")


def get_birth_data() -> dict:
    """
    אוסף את כל נתוני הלידה הנדרשים: שם, תאריך, שעה ומיקום.

    Returns:
        dict: מילון עם המפתחות name, birthdate, birthtime, location
    """
    print("\n--- איסוף נתוני לידה ---")

    name = input("הכנס שם: ").strip() or "User"
    birthdate = get_validated_date("הכנס תאריך לידה (פורמט YYYY-MM-DD): ")
    birthtime = get_validated_time(
        "הכנס שעת לידה (פורמט HH:MM, השאר ריק אם לא ידוע): ",
        is_optional=True
    )

    print("\n--- נתוני מיקום לידה ---")
    location = get_location_input(
        single_prompt="הכנס מיקום לידה (Latitude, Longitude - לדוגמה: 32.08, 34.78): "
    )

    return {
        'name': name,
        'birthdate': birthdate,
        'birthtime': birthtime,
        'location': location
    }


def get_name_and_nikud() -> tuple:
    """
    אוסף שם וניקוד לניתוח קבלי.

    Returns:
        tuple: (name, nikud_dict) כאשר nikud_dict הוא {position: nikud}
    """
    print("\n--- איסוף נתוני שם ---")
    name = input("הכנס את השם: ").strip()

    nikud_dict = {}
    print("\n--- איסוף ניקוד השם ---")
    for i, letter in enumerate(name):
        nikud = input(f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, השאר ריק): ").strip()
        if nikud:
            nikud_dict[i + 1] = nikud

    return name, nikud_dict


def get_yes_no_choice(prompt: str, default: bool = True) -> bool:
    """
    פונקציה גנרית לשאלת כן/לא.

    Args:
        prompt: השאלה להציג
        default: התשובה המוגדרת כברירת מחדל

    Returns:
        bool: True לכן, False ללא
    """
    default_text = "(Y/n)" if default else "(y/N)"
    user_input = input(f"{prompt} {default_text}: ").strip().lower()

    if not user_input:
        return default

    return user_input in ['y', 'yes', 'כן', '1']
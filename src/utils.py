import os
import textwrap
from datetime import datetime
import re


def write_results_to_file(output_dir: str, name: str, results: list, file_suffix: str = ".txt",
                          wrap_text: bool = False):
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


def get_validated_date(prompt: str) -> datetime.date:
    """אוסף ומאמת תאריך מהמשתמש בפורמט YYYY-MM-DD."""
    while True:
        try:
            date_str = input(prompt).strip()
            # בדיקה חזקה יותר כדי לוודא שזה תואם את הפורמט לפני ה-strptime
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                raise ValueError("פורמט שגוי")

            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            return date_obj
        except ValueError:
            print("❌ פורמט תאריך לא תקין. אנא הזן מחדש (YYYY-MM-DD).")


def get_validated_time(prompt: str, is_optional: bool = False) -> [datetime.time, None]:
    """אוסף ומאמת שעה מהמשתמש בפורמט HH:MM. מאפשר לדלג אם is_optional=True."""
    while True:
        time_str = input(prompt).strip()

        if is_optional and not time_str:
            return None  # אם אופציונלי והמשתמש השאיר ריק

        try:
            # בדיקה חזקה יותר
            if not re.match(r'^\d{2}:\d{2}$', time_str):
                raise ValueError

            time_obj = datetime.strptime(time_str, '%H:%M').time()
            return time_obj
        except ValueError:
            # אם is_optional=False, ההודעה תהיה ברורה שנדרש קלט
            optional_hint = ", השאר ריק אם לא ידוע" if is_optional else ""
            print(f"❌ פורמט שעה לא תקין. אנא הזן מחדש (HH:MM){optional_hint}.")


def get_location_input(prompt_lat: str, prompt_lon: str) -> dict:
    """אוסף קואורדינטות (רוחב ואורך) ומחזיר מילון: {'lat': float, 'lon': float}."""
    while True:
        try:
            latitude_str = input(prompt_lat).strip()
            longitude_str = input(prompt_lon).strip()

            latitude = float(latitude_str)
            longitude = float(longitude_str)

            # בדיקות טווח
            if not (-90 <= latitude <= 90):
                raise ValueError("ערך רוחב (Latitude) חייב להיות בין -90 ל-90.")
            if not (-180 <= longitude <= 180):
                raise ValueError("ערך אורך (Longitude) חייב להיות בין -180 ל-180.")

            return {'lat': latitude, 'lon': longitude}

        except ValueError as e:
            # מטפל גם בפורמט (לא מספר) וגם בטווח לא תקין
            print(f"❌ קלט לא תקין: {e}. אנא הזן מספרים עשרוניים תקינים.")


def get_position_key(position):
    if position == 1:
        return "ראשונה"
    elif position == 2:
        return "שנייה"
    elif position == 3:
        return "שלישית"
    else:
        return "רביעית ואילך"


def get_element_key(letter):
    element_mapping = {
        "האש": {'ג', 'ד', 'ה', 'ט', 'כ', 'ס', 'ש'},
        "האוויר": {'א', 'ז', 'ל', 'פ', 'צ', 'ר'},
        "המים": {'ח', 'מ', 'נ', 'ק', 'ת'},
        "האדמה": {'ב', 'ו', 'י', 'ע'}
    }

    for element, letters in element_mapping.items():
        if letter in letters:
            return element

    return None  # במקרה שהאות אינה מופיעה בטבלה


def normalize_final_letters(text):
    final_letters_map = {
        'ך': 'כ',
        'ם': 'מ',
        'ן': 'נ',
        'ף': 'פ',
        'ץ': 'צ'
    }
    return ''.join(final_letters_map.get(char, char) for char in text)


def position_to_word(index):
    words_map = ["ראשונה", "שניה", "שלישית", "רביעית", "חמישית", "שישית", "שביעית", "שמינית", "תשיעית", "עשירית",
                 "אחת-עשרה", "שתים-עשרה", "שלוש-עשרה", "ארבע-עשרה", "חמש-עשרה", "שש-עשרה", "מי יודע כמה"]
    if index >= 17:
        index = 17
    return words_map[index]

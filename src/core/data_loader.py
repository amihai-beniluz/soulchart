"""
מודול גנרי לטעינת נתונים מקבצי טקסט.
מרכז את הלוגיקה המשותפת של NameDataLoaders ו-ChartDataLoaders.
"""
import os
import re
from typing import Callable, Optional


def load_hierarchical_data(filepath: str, header_detector: Callable[[str], bool],
                           subheader_detector: Optional[Callable[[str], bool]] = None) -> dict:
    """
    טעינת נתונים היררכיים (כותרת -> תת-כותרת -> תוכן).

    Args:
        filepath: נתיב מלא לקובץ
        header_detector: פונקציה לזיהוי כותרת ראשית
        subheader_detector: פונקציה לזיהוי תת-כותרת (אופציונלי)

    Returns:
        dict: מילון מקונן או שטוח לפי המבנה
    """
    data = {}

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            current_key = None
            current_subkey = None

            for line in f:
                line = line.strip()

                if not line:
                    continue

                # זיהוי כותרת ראשית
                if header_detector(line):
                    current_key = extract_key_from_line(line)
                    if subheader_detector:
                        data[current_key] = {}
                    else:
                        data[current_key] = ""
                    current_subkey = None

                # זיהוי תת-כותרת
                elif subheader_detector and current_key and subheader_detector(line):
                    current_subkey = extract_key_from_line(line)
                    data[current_key][current_subkey] = ""

                # תוכן
                else:
                    if current_key:
                        if current_subkey:
                            data[current_key][current_subkey] += line + " "
                        else:
                            if isinstance(data[current_key], dict):
                                # אם יש מבנה מקונן אבל אין subkey, שמור בתוכן הכותרת עצמה
                                if '__content__' not in data[current_key]:
                                    data[current_key]['__content__'] = ""
                                data[current_key]['__content__'] += line + " "
                            else:
                                data[current_key] += line + " "

    except FileNotFoundError:
        print(f"⚠️ אזהרה: קובץ '{filepath}' לא נמצא")
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת '{filepath}': {e}")

    return data


def load_simple_data(filepath: str, max_header_length: int = 100) -> dict:
    """
    טעינת נתונים פשוטים (כותרת קצרה + תוכן).

    Args:
        filepath: נתיב מלא לקובץ
        max_header_length: אורך מקסימלי לכותרת

    Returns:
        dict: {header: content}
    """
    data = {}

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            current_key = None
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                if not line or line.startswith("#"):
                    i += 1
                    continue

                # זיהוי כותרת: שורה קצרה שאחריה תוכן
                if len(line) < max_header_length and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith("#"):
                        current_key = line
                        data[current_key] = ""
                        i += 1
                        continue

                # הוסף תוכן
                if current_key:
                    data[current_key] += line + " "

                i += 1

    except FileNotFoundError:
        print(f"⚠️ אזהרה: קובץ '{filepath}' לא נמצא")
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת '{filepath}': {e}")

    return data


def load_structured_data(filepath: str, header_max_length: int = 80) -> dict:
    """
    טעינת נתונים מובנים (כותרות באנגלית + תוכן).

    Args:
        filepath: נתיב מלא לקובץ
        header_max_length: אורך מקסימלי לכותרת

    Returns:
        dict: {normalized_header: content}
    """
    data = {}

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            current_key = None
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                if not line or line.startswith("#"):
                    i += 1
                    continue

                # זיהוי כותרת אנגלית
                is_header = False
                clean_line = line.replace(' ', '').replace('-', '')

                if clean_line.isalpha() and len(line) < header_max_length:
                    if all(c.isupper() or c.islower() or c.isspace() or c == '-' for c in line):
                        is_header = True

                if is_header:
                    # נירמול המפתח
                    normalized_key = " ".join(line.split()).strip().replace('-', '')
                    current_key = normalized_key
                    data[current_key] = ""
                elif current_key:
                    data[current_key] += line + " "

                i += 1

    except FileNotFoundError:
        print(f"⚠️ אזהרה: קובץ '{filepath}' לא נמצא")
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת '{filepath}': {e}")

    return data


def load_custom_data(filepath: str, parser_func: Callable) -> dict:
    """
    טעינת נתונים עם parser מותאם אישית.

    Args:
        filepath: נתיב מלא לקובץ
        parser_func: פונקציה המקבלת רשימת שורות ומחזירה dict

    Returns:
        dict: התוצאה של parser_func
    """
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            return parser_func(lines)
    except FileNotFoundError:
        print(f"⚠️ אזהרה: קובץ '{filepath}' לא נמצא")
        return {}
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת '{filepath}': {e}")
        return {}


def extract_key_from_line(line: str) -> str:
    """
    מחלץ מפתח מכותרת (מסיר תווים מיוחדים).
    """
    parts = line.split()
    if len(parts) > 1:
        # אם יש מילות מפתח כמו "האות", "יסוד", קח את המילה הבאה
        if parts[0] in ["האות", "יסוד", "הניקוד"]:
            return parts[1].rstrip(':')
    return line


def get_data_dir(module_dir: str, levels_up: int = 2) -> str:
    """
    מחשב את נתיב תיקיית data יחסית למודול.

    Args:
        module_dir: __file__ של המודול הקורא
        levels_up: כמה רמות למעלה עד שורש הפרויקט

    Returns:
        str: נתיב לתיקיית data
    """
    current = os.path.dirname(module_dir)
    for _ in range(levels_up):
        current = os.path.abspath(os.path.join(current, os.pardir))
    return os.path.join(current, 'data')
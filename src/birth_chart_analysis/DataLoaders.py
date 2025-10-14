# src/birth_chart_analysis/DataLoaders.py
import os

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')


def _load_simple_data(filename: str) -> dict:
    """
    טעינת נתונים מקבצים עם כותרות פשוטות (planets, signs, houses, chart_rulers).
    הכותרת היא שורה קצרה שאחריה באה פסקת תוכן.
    """
    data = {}
    try:
        with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            current_key = None
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                # דלג על שורות ריקות והערות
                if not line or line.startswith("#"):
                    i += 1
                    continue

                # זיהוי כותרת: שורה קצרה (פחות מ-100 תווים) שאחריה תוכן
                if len(line) < 100 and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # אם השורה הבאה היא תוכן (לא ריקה)
                    if next_line and not next_line.startswith("#"):
                        current_key = line
                        data[current_key] = ""
                        i += 1
                        continue

                # הוסף תוכן למפתח הנוכחי
                if current_key:
                    data[current_key] += line + " "

                i += 1

    except FileNotFoundError:
        print(f"⚠️ אזהרה: קובץ '{filename}' לא נמצא ב-{DATA_DIR}")
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת '{filename}': {e}")

    return data


def _load_structured_data(filename: str) -> dict:
    """
    טעינת נתונים מקבצים עם כותרות בפורמט אנגלי
    (planet_in_sign, planet_in_house, aspects וכו').
    הכותרת היא שורה באנגלית עם מילים מסוימות.
    """
    data = {}
    try:
        with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            current_key = None
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                # דלג על שורות ריקות והערות
                if not line or line.startswith("#"):
                    i += 1
                    continue

                # זיהוי כותרת: שורה באנגלית קצרה שמכילה מילות מפתח
                is_header = False

                # בדיקה אם זו כותרת באנגלית (מכילה רק אותיות אנגליות, רווחים ומקפים)
                clean_line = line.replace(' ', '').replace('-', '')
                if clean_line.isalpha() and all(c.isupper() or c.islower() or c.isspace() or c == '-' for c in line):
                    # ובנוסף, אם השורה קצרה מספיק (פחות מ-80 תווים)
                    if len(line) < 80:
                        is_header = True

                if is_header:
                    # נרמול המפתח - הסרת מקפים לאחידות
                    current_key = line.replace('-', '')
                    data[current_key] = ""
                elif current_key:
                    # הוסף תוכן עם רווח
                    data[current_key] += line + " "

                i += 1

    except FileNotFoundError:
        print(f"⚠️ אזהרה: קובץ '{filename}' לא נמצא ב-{DATA_DIR}")
    except Exception as e:
        print(f"⚠️ שגיאה בטעינת '{filename}': {e}")

    return data


def _load_house_to_house_data(filename: str) -> dict:
    """
    טעינה ייעודית של קובץ house_to_house המכיל מפתחות ניתוח מורכבים.
    """
    data = {}
    try:
        with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            current_key = None

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # זיהוי מפתח ניתוח מורכב
                if "house is in" in line and "when its ruler" in line:
                    current_key = line
                    data[current_key] = ""
                elif current_key:
                    data[current_key] += line + " "

    except FileNotFoundError:
        print(f"❌ שגיאה: קובץ '{filename}' לא נמצא")
    except Exception as e:
        print(f"❌ שגיאה בטעינת '{filename}': {e}")

    return data


def load_all_chart_data():
    """טוען את כל הנתונים האסטרולוגיים לזיכרון"""
    return {
        # קבצים פשוטים (עברית)
        'planets': _load_simple_data('planets.txt'),
        'signs': _load_simple_data('signs.txt'),
        'houses': _load_simple_data('houses.txt'),
        'chart_rulers': _load_simple_data('chart_rulers.txt'),

        # קבצים מובנים (אנגלית)
        'planet_in_sign': _load_structured_data('planet_in_sign.txt'),
        'planet_in_house': _load_structured_data('planet_in_house.txt'),
        'house_in_sign': _load_structured_data('house_in_sign.txt'),
        'aspects': _load_structured_data('aspects.txt'),
        'sun_moon_ascendant': _load_structured_data('sun_moon_ascendant.txt'),
        'house_to_house': _load_house_to_house_data('house_to_house.txt'),
    }

"""
טוען נתונים אסטרולוגיים מקבצי טקסט.
משתמש במודול data_loader הגנרי.
"""
import os
import sys

# הוספת src לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.data_loader import load_simple_data, load_structured_data, get_data_dir

MODULE_DIR = os.path.dirname(__file__)
DATA_DIR = get_data_dir(MODULE_DIR)


def _load_house_to_house_data(filename: str) -> dict:
    """
    טעינה ייעודית של קובץ house_to_house המכיל מפתחות ניתוח מורכבים.
    """
    data = {}
    filepath = os.path.join(DATA_DIR, filename)

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
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


def load_all_chart_data() -> dict:
    """
    טוען את כל הנתונים האסטרולוגיים לזיכרון.

    Returns:
        dict: מילון עם כל סוגי הנתונים
    """
    return {
        'planets': load_simple_data(os.path.join(DATA_DIR, 'planets.txt')),
        'signs': load_simple_data(os.path.join(DATA_DIR, 'signs.txt')),
        'houses': load_simple_data(os.path.join(DATA_DIR, 'houses.txt')),
        'chart_rulers': load_simple_data(os.path.join(DATA_DIR, 'chart_rulers.txt')),
        'planet_in_sign': load_structured_data(os.path.join(DATA_DIR, 'planet_in_sign.txt')),
        'planet_in_house': load_structured_data(os.path.join(DATA_DIR, 'planet_in_house.txt')),
        'house_in_sign': load_structured_data(os.path.join(DATA_DIR, 'house_in_sign.txt')),
        'planet_house_sign': load_structured_data(os.path.join(DATA_DIR, 'planet_house_sign.txt')),
        'aspects': load_structured_data(os.path.join(DATA_DIR, 'aspects.txt')),
        'sun_moon_ascendant': load_structured_data(os.path.join(DATA_DIR, 'sun_moon_ascendant.txt')),
        'house_to_house': _load_house_to_house_data('house_to_house.txt'),
        'aspects_transit': load_structured_data(os.path.join(DATA_DIR, 'aspects_transit.txt'))
    }
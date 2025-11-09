"""
פונקציות עזר לבוט הטלגרם.
"""
import os
import json
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# תיקיות פלט
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, '..', '..', 'output')
NAMES_DIR = os.path.join(OUTPUT_DIR, 'names')
CHARTS_DIR = os.path.join(OUTPUT_DIR, 'charts')
TRANSITS_DIR = os.path.join(OUTPUT_DIR, 'transits')
USER_DATA_DIR = os.path.join(OUTPUT_DIR, 'user_data')

# יצירת תיקיות
for directory in [NAMES_DIR, CHARTS_DIR, TRANSITS_DIR, USER_DATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# מילון פרופילי משתמשים (בזיכרון)
user_profiles = {}


def save_user_input(user_id: int, data_dict: dict):
    """
    שומר קלטים של משתמש לקובץ JSON.

    Args:
        user_id: מזהה משתמש טלגרם
        data_dict: המידע לשמירה
    """
    try:
        file_path = os.path.join(USER_DATA_DIR, f'user_{user_id}.json')
        save_data = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'inputs': data_dict
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving user input: {e}")


def get_main_menu_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """
    יוצר מקלדת לתפריט הראשי.

    Args:
        user_id: מזהה משתמש (אופציונלי)

    Returns:
        InlineKeyboardMarkup: מקלדת עם כפתורים
    """
    keyboard = [
        [InlineKeyboardButton("📝 ניתוח שם", callback_data="name_analysis")],
        [InlineKeyboardButton("⭐ מפת לידה אסטרולוגית", callback_data="birth_chart")],
        [InlineKeyboardButton("🌍 מפת מעברים (טרנזיטים)", callback_data="transits")],
    ]

    if user_id and user_id in user_profiles:
        profile = user_profiles[user_id]
        keyboard.append([InlineKeyboardButton(
            f"🔄 משתמש חדש (נוכחי: {profile['name']})",
            callback_data="new_user"
        )])

    keyboard.append([InlineKeyboardButton("ℹ️ עזרה", callback_data="help")])

    return InlineKeyboardMarkup(keyboard)


def get_user_profile(user_id: int) -> dict:
    """
    מחזיר פרופיל משתמש אם קיים.

    Args:
        user_id: מזהה משתמש

    Returns:
        dict או None: פרופיל המשתמש
    """
    return user_profiles.get(user_id)


def save_user_profile(user_id: int, name: str, birthdate, birthtime, birth_location: tuple):
    """
    שומר פרופיל משתמש בזיכרון.

    Args:
        user_id: מזהה משתמש
        name: שם
        birthdate: תאריך לידה
        birthtime: שעת לידה
        birth_location: מיקום לידה (lat, lon)
    """
    user_profiles[user_id] = {
        'name': name,
        'birthdate': birthdate,
        'birthtime': birthtime,
        'birth_location': birth_location
    }


def delete_user_profile(user_id: int) -> bool:
    """
    מוחק פרופיל משתמש.

    Args:
        user_id: מזהה משתמש

    Returns:
        bool: True אם נמחק, False אם לא היה
    """
    if user_id in user_profiles:
        del user_profiles[user_id]
        return True
    return False

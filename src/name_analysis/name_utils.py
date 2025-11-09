"""
פונקציות עזר לניתוח שמות עבריים - קבלה ונומרולוגיה.
"""


def get_position_key(position: int) -> str:
    """
    ממיר מספר מיקום למחרוזת תיאור המיקום.

    Args:
        position: מיקום האות בשם (1-based)

    Returns:
        str: תיאור המיקום (ראשונה, שנייה, וכו')
    """
    if position == 1:
        return "ראשונה"
    elif position == 2:
        return "שנייה"
    elif position == 3:
        return "שלישית"
    else:
        return "רביעית ואילך"


def get_element_key(letter: str) -> str:
    """
    מחזיר את היסוד של אות עברית לפי חלוקה קבלית.

    Args:
        letter: אות עברית

    Returns:
        str: שם היסוד (האש, האוויר, המים, האדמה) או None
    """
    element_mapping = {
        "האש": {'ג', 'ד', 'ה', 'ט', 'כ', 'ס', 'ש'},
        "האוויר": {'א', 'ז', 'ל', 'פ', 'צ', 'ר'},
        "המים": {'ח', 'מ', 'נ', 'ק', 'ת'},
        "האדמה": {'ב', 'ו', 'י', 'ע'}
    }

    for element, letters in element_mapping.items():
        if letter in letters:
            return element

    return None


def normalize_final_letters(text: str) -> str:
    """
    ממיר אותיות סופיות לאותיות רגילות.

    Args:
        text: טקסט עברי

    Returns:
        str: טקסט עם אותיות רגילות בלבד
    """
    final_letters_map = {
        'ך': 'כ',
        'ם': 'מ',
        'ן': 'נ',
        'ף': 'פ',
        'ץ': 'צ'
    }
    return ''.join(final_letters_map.get(char, char) for char in text)


def position_to_word(index: int) -> str:
    """
    ממיר אינדקס (0-based) למילה תיאורית של המיקום.

    Args:
        index: אינדקס האות (מתחיל מ-0)

    Returns:
        str: תיאור המיקום במילים
    """
    words_map = [
        "ראשונה", "שניה", "שלישית", "רביעית", "חמישית", "שישית",
        "שביעית", "שמינית", "תשיעית", "עשירית", "אחת-עשרה",
        "שתים-עשרה", "שלוש-עשרה", "ארבע-עשרה", "חמש-עשרה",
        "שש-עשרה", "מי יודע כמה"
    ]

    if index >= len(words_map) - 1:
        index = len(words_map) - 1

    return words_map[index]
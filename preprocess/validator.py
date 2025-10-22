import os
import re
import unicodedata

# --- הגדרות קבצים ---
FULL_INPUT_FILE = "aspects_transit.txt"
OUTPUT_FILE = "aspects_transit_output.txt"
MISSING_OUTPUT_FILE = "missing_aspects_list.txt"


# --- פונקציית נורמליזציה אולטימטיבית ---

def ultimate_normalize_text(text):
    """
    מבצעת נורמליזציה אגרסיבית לטקסט לצורך השוואה מדויקת.
    """
    if not text:
        return ""

    text = unicodedata.normalize('NFC', text)
    text = text.strip()
    # הופך את כל סוגי הרווחים לרווח בודד
    text = re.sub(r'\s+', ' ', text)

    return text


# --- פונקציות עזר לקריאה ---

def read_original_aspects(filename):
    """קורא את כל הכותרות המקוריות לסט, לאחר נורמליזציה."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # סט הכותרות המקוריות בפורמט נקי
            return {ultimate_normalize_text(line) for line in f if line.strip()}
    except FileNotFoundError:
        print(f"שגיאה: קובץ הקלט המקורי לא נמצא: {filename}")
        return set()


def read_completed_aspects_robust(output_filename, original_aspects_normalized):
    """
    **קריאה חסינה**: עוברת על כל שורה ושורה בקובץ הפלט
    ובודקת אם השורה (לאחר נורמליזציה) נמצאת בסט הכותרות המקוריות.
    """
    completed_aspects_found = set()

    try:
        with open(output_filename, 'r', encoding='utf-8') as f:

            # עוברים על כל שורה בקובץ הפלט!
            for line in f:
                raw_line = line.strip()
                if not raw_line:
                    continue

                # מנרמלים את השורה מהפלט
                normalized_line = ultimate_normalize_text(raw_line)

                # בדיקה: האם השורה הזו היא כותרת מקורית?
                if normalized_line in original_aspects_normalized:
                    completed_aspects_found.add(normalized_line)

    except FileNotFoundError:
        print(f"שגיאה: קובץ הפלט לא נמצא: {output_filename}")
        return set()

    return completed_aspects_found


# --- פונקציית האימות הראשית ---

def find_missing_aspects():
    print("--- מתחיל אימות סופי חסין לכשלים ---")

    # 1. קריאת הכותרות המקוריות (סט נקי)
    original_set_normalized = read_original_aspects(FULL_INPUT_FILE)

    # 2. קריאת הכותרות שהושלמו (שימוש במנגנון החסין)
    completed_set_normalized = read_completed_aspects_robust(OUTPUT_FILE, original_set_normalized)

    if not original_set_normalized:
        print("לא ניתן להמשיך: קובץ הקלט המקורי חסר או ריק.")
        return

    # 3. חישוב: (כל המקור) פחות (מה שהושלם) = החסרים
    missing_set_normalized = original_set_normalized - completed_set_normalized

    # 4. יצירת רשימה מסודרת של החסרים (כדי לשמור על הטקסט המקורי)
    missing_list_raw = []

    with open(FULL_INPUT_FILE, 'r', encoding='utf-8') as f:
        # עובר על כל שורה בקלט המקורי
        for line in f:
            raw_aspect = line.strip()
            if not raw_aspect:
                continue

            # בודק האם הגרסה המנורמלת חסרה
            if ultimate_normalize_text(raw_aspect) in missing_set_normalized:
                missing_list_raw.append(raw_aspect)

    total_original = len(original_set_normalized)
    total_completed = len(completed_set_normalized)
    total_missing = len(missing_list_raw)

    # 5. סיכום וכתיבה לקובץ
    print("-" * 30)
    print(f"סה\"כ כותרות מקוריות: {total_original:,}")
    print(f"סה\"כ כותרות נוטחו ונמצאו: {total_completed:,}")
    print(f"**סה\"כ כותרות חסרות (יש להשלים):** {total_missing:,}")

    if total_missing > 0:
        with open(MISSING_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(missing_list_raw) + '\n')

        print(f"\n✅ רשימת הכותרות החסרות נשמרה ב: {MISSING_OUTPUT_FILE}")
    else:
        print("\n✅ כל הכותרות נמצאו בהצלחה! הפרויקט הושלם.")

    print("--- סיום אימות ---")


# --- הפעלת הסקריפט ---
if __name__ == "__main__":
    find_missing_aspects()
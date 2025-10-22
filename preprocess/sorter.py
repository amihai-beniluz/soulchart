import os
import re
import unicodedata

# --- הגדרות קבצים ---
FULL_INPUT_FILE = "aspects_transit.txt"
OUTPUT_FILE = "aspects_transit_output.txt"

FINAL_SORTED_FILE = "aspects_transit_FINAL_SORTED.txt"
ERROR_FILE = "aspects_transits_analysi_errors.txt"


# --- פונקציית נורמליזציה (כדי לוודא שיוויון מלא) ---
def ultimate_normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


# --- שלב 1: בניית מפת ניתוח (Analysis Map) ---

def build_analysis_map_robust(output_filename, original_aspects_set):
    """
    קורא את קובץ הפלט בצורה חסינת כשלים, ומייצר מילון:
    {כותרת מנורמלת: הניתוח המלא}.
    """
    analysis_map = {}

    try:
        with open(output_filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]

        i = 0
        while i < len(lines):
            current_line = lines[i]
            # 💡 טיפ: מומלץ תמיד לנקות שורה מתווי רווח מיותרים לפני הפיצול
            current_line_split = current_line.strip().split()

            if current_line_split and current_line_split[-1] == 'retrograde':
                # 1. שמירת המילה הראשונה (לדוגמה: 'מרקורי')
                first_word = current_line_split[0]

                # 2. שמירת המילים האמצעיות (מהשנייה עד לפני האחרונה)
                middle_words = current_line_split[1:-1]

                # 3. בנייה מחדש של השורה באמצעות join, הוספת 'retrograde'
                #    במקום השני, וצירוף המילים האמצעיות

                # בניית הרשימה החדשה: [first_word, 'retrograde', *middle_words]
                new_list = [first_word, 'retrograde'] + middle_words

                # חיבור הרשימה למחרוזת שורה אחת
                current_line = " ".join(new_list)

            # 1. בדיקה: האם השורה הנוכחית היא כותרת?
            normalized_current_line = ultimate_normalize_text(current_line)

            if normalized_current_line in original_aspects_set:
                # 2. אם זו כותרת, נניח שהשורה הבאה היא הניתוח שלה
                if i + 1 < len(lines):
                    llm_analysis = lines[i + 1].strip()

                    # ודא שהניתוח אינו כותרת או הודעת שגיאה
                    if not llm_analysis.startswith('[שגיאה:') and normalized_current_line != ultimate_normalize_text(
                            llm_analysis):
                        analysis_map[normalized_current_line] = llm_analysis
                        # קופץ מעבר לכותרת ולניתוח, מחפש את הכותרת הבאה
                        i += 2
                        continue

            # אם לא נמצאה כותרת/ניתוח תקינים, מקדמים את המונה ב-1 וממשיכים
            i += 1

    except FileNotFoundError:
        print(f"שגיאה: קובץ הפלט לא נמצא: {output_filename}")
        return {}

    return analysis_map


# --- שלב 2: מיון וייצוא סופי ---

def sort_and_export():
    print("--- מתחיל שלב 1: קריאת סדר המקור ---")

    # קורא את כל הכותרות המקוריות לסט ולרשימה
    try:
        with open(FULL_INPUT_FILE, 'r', encoding='utf-8') as f:
            original_order_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"שגיאה: קובץ המקור {FULL_INPUT_FILE} לא נמצא.")
        return

    # בניית סט הכותרות המנורמלות
    original_aspects_set = {ultimate_normalize_text(a) for a in original_order_list}

    print("--- מתחיל שלב 2: בניית מפת הניתוחים החסינה ---")
    analysis_map = build_analysis_map_robust(OUTPUT_FILE, original_aspects_set)

    if len(analysis_map) == 0:
        print("שגיאה קריטית: לא נמצאו ניתוחים במפת הניתוח. סיום.")
        return

    print(f"נמצאו {len(analysis_map):,} ניתוחים ייחודיים במפת הניתוח.")
    print("-" * 30)
    print("--- מתחיל שלב 3: קריאת סדר המקור וייצוא ממוין ---")

    sorted_count = 0
    missing_in_map = 0
    error_log = []

    with open(FINAL_SORTED_FILE, 'w', encoding='utf-8') as f_final:

        # עובר על הכותרות המקוריות לפי הסדר
        for raw_aspect in original_order_list:

            normalized_aspect = ultimate_normalize_text(raw_aspect)

            # בדיקה: אם הניתוח קיים במפה
            if normalized_aspect in analysis_map:
                llm_analysis = analysis_map[normalized_aspect]

                # כתיבת הכותרת המקורית (raw) והניתוח שלה לקובץ הממוין
                f_final.write(f"{raw_aspect}\n")
                f_final.write(f"{llm_analysis}\n")
                f_final.write("\n")
                sorted_count += 1
            else:
                missing_in_map += 1
                error_log.append(raw_aspect)

    print("-" * 30)
    print(f"✅ סיום מיון! נכתבו {sorted_count:,} ניתוחים ממוינים לקובץ: {FINAL_SORTED_FILE}")

    # בדיקה סופית (אם זה לא 0, זה הבעיה!)
    if missing_in_map > 0:
        print(f"❌ אזהרה חמורה: {missing_in_map:,} כותרות לא נמצאו במפת הניתוח המלאה (נשמרו ל-{ERROR_FILE}).")
        with open(ERROR_FILE, 'w', encoding='utf-8') as f_err:
            f_err.write('\n'.join(error_log) + '\n')


# --- הפעלת הסקריפט ---
if __name__ == "__main__":
    sort_and_export()

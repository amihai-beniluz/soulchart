import os
from pathlib import Path

# --- הגדרת הנתיבים (בהתאם להנחה שהסקריפט רץ מחוץ ל-src) ---

# הנתיבים לקבצים הנקיים
script_path = Path(__file__).resolve()
project_root_dir = script_path.parent
output_dir = project_root_dir / "data"

CLEAN_FILE_TO_PUNCTUATE = output_dir / "names_empty.txt"
CLEAN_PUNCTUATED_FILE = output_dir / "names_wv.txt"

# הנתיב לקובץ הפלט המאוחד
COMBINED_FILE = output_dir / "names.txt"


def combine_files():
    """
    קורא את שני קבצי השמות הנקיים ומאחד אותם לקובץ אחד בפורמט:
    [שם_לא_מנוקד] [שם_מנוקד]
    """
    try:
        # 1. קורא את שני הקבצים
        with open(CLEAN_FILE_TO_PUNCTUATE, 'r', encoding='utf-8') as f_unpunc:
            unpunc_lines = f_unpunc.readlines()

        with open(CLEAN_PUNCTUATED_FILE, 'r', encoding='utf-8') as f_punc:
            punc_lines = f_punc.readlines()

    except FileNotFoundError:
        print(f"--- ❌ שגיאת קריאת קובץ ---")
        print(
            f"ודא שהקבצים '{CLEAN_FILE_TO_PUNCTUATE.name}' ו-'{CLEAN_PUNCTUATED_FILE.name}' קיימים בתיקייה '{output_dir.name}'.")
        return

    # 2. מוודא שיש מספר שווה של שורות
    if len(unpunc_lines) != len(punc_lines):
        print("אזהרה: מספר השורות בקבצים הנקיים אינו זהה. האיחוד ייעצר בשורה הקצרה יותר.")

    combined_lines = []

    # 3. מאחד את השמות, שורה אחר שורה
    # ה-zip עובר על שני האיטרטורים במקביל
    for unpunc_line, punc_line in zip(unpunc_lines, punc_lines):

        # מנקה רווחים ותווי שורה משני הצדדים
        unpunc_name = unpunc_line.strip()
        punc_name = punc_line.strip()

        # מוודא שהשורות אינן ריקות לפני האיחוד
        if unpunc_name and punc_name:
            # הפורמט: [שם לא מנוקד] רווח [שם מנוקד]
            combined_lines.append(f"{unpunc_name} {punc_name}")

    # 4. כותב את הקובץ המאוחד
    try:
        with open(COMBINED_FILE, 'w', encoding='utf-8') as f_out:
            f_out.write('\n'.join(combined_lines) + '\n')

        print("--- ✅ איחוד הושלם ---")
        print(f"סה\"כ זוגות שמות שנשמרו: {len(combined_lines)}")
        print(f"הקובץ המאוחד נשמר בנתיב: {COMBINED_FILE}")

    except IOError as e:
        print(f"שגיאה בכתיבת קובץ: {e}")


# הפעלת הפונקציה הראשית
if __name__ == "__main__":
    combine_files()
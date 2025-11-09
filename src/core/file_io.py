"""
מודול לניהול קבצים - קריאה וכתיבה.
"""
import os
import textwrap


def write_results_to_file(output_dir: str, name: str, results: list,
                          file_suffix: str = ".txt", wrap_text: bool = False):
    """
    שומר תוצאות ניתוח לקובץ טקסט.

    Args:
        output_dir: תיקיית הפלט
        name: שם הקובץ (ללא סיומת)
        results: רשימת שורות לכתיבה
        file_suffix: סיומת הקובץ
        wrap_text: האם לעטוף טקסט ארוך (למפות לידה)
    """
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


def ensure_dir_exists(directory: str) -> bool:
    """
    מוודא שתיקייה קיימת, יוצר אותה במידת הצורך.

    Args:
        directory: נתיב התיקייה

    Returns:
        bool: True אם הצליח, False אחרת
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ שגיאה ביצירת תיקייה {directory}: {e}")
        return False
    
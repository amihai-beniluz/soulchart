"""
מודול לניהול קובץ השמות המנוקדים.
מאפשר חיפוש, הוספה ועדכון של שמות בקובץ names.txt.
"""
import os
from typing import Dict, List, Optional, Tuple


class NamesManager:
    """מנהל את קובץ השמות המנוקדים."""

    def __init__(self, names_file_path: str):
        """
        מאתחל את מנהל השמות.

        Args:
            names_file_path: נתיב מלא לקובץ השמות
        """
        self.names_file_path = names_file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """מוודא שקובץ השמות קיים, אחרת יוצר אותו."""
        if not os.path.exists(self.names_file_path):
            os.makedirs(os.path.dirname(self.names_file_path), exist_ok=True)
            open(self.names_file_path, 'w', encoding='utf-8').close()

    def search_name(self, name: str) -> List[str]:
        """
        מחפש שם בקובץ ומחזיר רשימה של כל הניקודים האפשריים.

        Args:
            name: השם ללא ניקוד

        Returns:
            רשימה של שמות מנוקדים. רשימה ריקה אם השם לא נמצא.
        """
        name = name.strip()
        nikud_versions = []

        try:
            with open(self.names_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        file_name, nikud_name = parts
                        if file_name == name:
                            nikud_versions.append(nikud_name)
        except Exception as e:
            print(f"⚠️ שגיאה בקריאת קובץ השמות: {e}")

        return nikud_versions

    def add_or_update_name(self, name: str, nikud_name: str) -> bool:
        """
        מוסיף שם חדש או מעדכן שם קיים בקובץ.
        הקובץ נשמר ממוין לקסיקוגרפית.

        Args:
            name: השם ללא ניקוד
            nikud_name: השם המנוקד

        Returns:
            True אם הפעולה הצליחה, False אחרת
        """
        name = name.strip()
        nikud_name = nikud_name.strip()

        try:
            # קריאת כל השורות הקיימות
            lines = []
            name_found = False

            if os.path.exists(self.names_file_path):
                with open(self.names_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            file_name, file_nikud = parts
                            if file_name == name and file_nikud == nikud_name:
                                # השם כבר קיים עם אותו ניקוד
                                return True
                            lines.append((file_name, file_nikud))

            # בדיקה אם השם כבר קיים (עם ניקוד שונה)
            existing_names = [line[0] for line in lines]
            if name not in existing_names:
                # הוספת שם חדש
                lines.append((name, nikud_name))
            else:
                # עדכון שם קיים - לא נעדכן אם יש כבר כניסה זהה
                # במקרה שיש שם עם ניקוד אחר, נוסיף כניסה נוספת
                lines.append((name, nikud_name))

            # מיון לקסיקוגרפי
            lines.sort(key=lambda x: x[0])

            # כתיבה חזרה לקובץ
            with open(self.names_file_path, 'w', encoding='utf-8') as f:
                for file_name, file_nikud in lines:
                    f.write(f"{file_name} {file_nikud}\n")

            return True

        except Exception as e:
            print(f"⚠️ שגיאה בעדכון קובץ השמות: {e}")
            return False

    def get_nikud_for_name(self, name: str) -> Tuple[Optional[str], List[str]]:
        """
        מחזיר את הניקוד לשם, או רשימת אפשרויות אם יש יותר מאחת.

        Args:
            name: השם ללא ניקוד

        Returns:
            טאפל של (ניקוד_יחיד, רשימת_כל_האפשרויות)
            - אם יש ניקוד יחיד: (nikud_name, [nikud_name])
            - אם יש מספר ניקודים: (None, [nikud1, nikud2, ...])
            - אם אין ניקוד: (None, [])
        """
        nikud_versions = self.search_name(name)

        if len(nikud_versions) == 0:
            return None, []
        elif len(nikud_versions) == 1:
            return nikud_versions[0], nikud_versions
        else:
            return None, nikud_versions


def nikud_dict_from_nikud_name(name: str, nikud_name: str) -> Dict[int, str]:
    """
    ממיר שם מנוקד לדיקשנרי ניקוד בפורמט של המערכת.
    מחזיר רק את שמות הניקודים שהמערכת מכירה, לא את תווי Unicode.

    Args:
        name: השם המקורי ללא ניקוד
        nikud_name: השם המנוקד

    Returns:
        דיקשנרי שבו המפתחות הם מיקום האות (1-based) והערכים הם שמות הניקודים
        (פתח/חיריק/צירה/קמץ/סגול/שווא/חולם/קובוץ/שורוק/ריק)
    """
    # מיפוי תווי ניקוד Unicode לשמות שהמערכת מכירה
    NIKUD_MAP = {
        '\u05B7': 'פתח',    # ַ
        '\u05B8': 'קמץ',    # ָ
        '\u05B4': 'חיריק',  # ִ
        '\u05B5': 'צירה',   # ֵ
        '\u05B6': 'סגול',   # ֶ
        '\u05B0': 'שווא',   # ְ
        '\u05B9': 'חולם',   # ֹ
        '\u05BB': 'קובוץ',  # ֻ
        # חטפים - מומרים לניקוד הרגיל
        '\u05B1': 'חטף_סגול',  # ֱ -> סגול
        '\u05B2': 'חטף_פתח',   # ֲ -> פתח
        '\u05B3': 'חטף_קמץ',   # ֳ -> קמץ
    }

    # המרת חטפים לניקודים רגילים
    CHATAF_TO_NIKUD = {
        'חטף_סגול': 'סגול',
        'חטף_פתח': 'פתח',
        'חטף_קמץ': 'קמץ',
    }

    # תו דגש
    DAGESH = '\u05BC'

    # אותיות ניקוד
    VAV = 'ו'
    YOD = 'י'

    nikud_dict = {}
    nikud_idx = 0
    name_idx = 0

    while nikud_idx < len(nikud_name) and name_idx < len(name):
        char = nikud_name[nikud_idx]

        if char == name[name_idx]:
            # אות רגילה - בודק אם יש ניקוד אחריה
            nikud_idx += 1
            collected_nikud = []

            # בדיקה מיוחדת: האם האות הבאה היא אות ניקוד (ו או י)?
            next_letter_is_nikud = False
            next_nikud_type = None

            if name_idx + 1 < len(name):
                # בודק אם האות הבאה בשם המקורי היא ו או י
                next_char = name[name_idx + 1]

                # בודק מה יש אחרי האות הנוכחית בשם המנוקד
                temp_idx = nikud_idx

                # דלג על דגש אם יש
                while temp_idx < len(nikud_name) and nikud_name[temp_idx] == DAGESH:
                    temp_idx += 1

                # בדוק אם יש ניקוד רגיל
                while temp_idx < len(nikud_name) and nikud_name[temp_idx] in NIKUD_MAP:
                    temp_idx += 1

                # עכשיו בדוק אם האות הבאה היא אות ניקוד
                if temp_idx < len(nikud_name) and nikud_name[temp_idx] == next_char:
                    # האות הבאה קיימת - בדוק אם אחריה יש דגש (שורוק) או חולם/חיריק
                    peek_idx = temp_idx + 1

                    if next_char == VAV and peek_idx < len(nikud_name):
                        if nikud_name[peek_idx] == DAGESH:
                            # שורוק מלא - האות הנוכחית תקבל "שורוק" והו תהיה "ריק"
                            next_letter_is_nikud = True
                            next_nikud_type = 'שורוק'
                        elif nikud_name[peek_idx] == '\u05B9':  # חולם
                            # חולם מלא - האות הנוכחית תקבל "חולם" והו תהיה "ריק"
                            next_letter_is_nikud = True
                            next_nikud_type = 'חולם'

                    elif next_char == YOD and peek_idx < len(nikud_name):
                        if nikud_name[peek_idx] == '\u05B4':  # חיריק
                            # חיריק מלא - האות הנוכחית תקבל "חיריק" והיוד תהיה "ריק"
                            next_letter_is_nikud = True
                            next_nikud_type = 'חיריק'

            # אם האות הבאה משמשת כאות ניקוד - הניקוד שייך לאות הנוכחית
            if next_letter_is_nikud and next_nikud_type:
                nikud_dict[name_idx + 1] = next_nikud_type
                # האות הבאה תהיה ריקה
                nikud_dict[name_idx + 2] = 'ריק'
                # דלג על כל הניקודים עד האות הבאה ועל הניקוד שלה
                while nikud_idx < len(nikud_name) and nikud_name[nikud_idx] != name[name_idx + 1]:
                    nikud_idx += 1
                # דלג על האות הבאה והניקוד שלה
                if nikud_idx < len(nikud_name):
                    nikud_idx += 1  # דלג על האות
                    # דלג על הניקוד (דגש או ניקוד רגיל)
                    if nikud_idx < len(nikud_name) and (nikud_name[nikud_idx] == DAGESH or nikud_name[nikud_idx] in NIKUD_MAP):
                        nikud_idx += 1

                name_idx += 2  # קפוץ שתי אותיות
                continue

            # איסוף ניקודים רגילים
            while nikud_idx < len(nikud_name):
                nikud_char = nikud_name[nikud_idx]

                # התעלמות מדגש (למעט במקרה של שורוק שכבר טופל)
                if nikud_char == DAGESH:
                    nikud_idx += 1
                    continue

                # אם זה ניקוד מוכר - נוסיף אותו
                if nikud_char in NIKUD_MAP:
                    nikud_name_str = NIKUD_MAP[nikud_char]
                    # המרת חטף לניקוד רגיל
                    if nikud_name_str in CHATAF_TO_NIKUD:
                        nikud_name_str = CHATAF_TO_NIKUD[nikud_name_str]
                    collected_nikud.append(nikud_name_str)
                    nikud_idx += 1
                else:
                    # לא ניקוד - מפסיקים את האיסוף
                    break

            # שמירת הניקוד (רק אם יש)
            if collected_nikud:
                # אם יש יותר מניקוד אחד, נשתמש רק בראשון
                nikud_dict[name_idx + 1] = collected_nikud[0]
            else:
                # אין ניקוד = ריק
                nikud_dict[name_idx + 1] = 'ריק'

            name_idx += 1
        else:
            # תו שאינו אות מהשם המקורי - דלג
            nikud_idx += 1

    # השלמת אותיות שלא קיבלו ניקוד
    for i in range(1, len(name) + 1):
        if i not in nikud_dict:
            nikud_dict[i] = 'ריק'

    return nikud_dict

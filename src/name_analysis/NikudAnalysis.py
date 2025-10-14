nikud_position_data = None  # משתנה גלובלי שישמור את המילון
nikud_data = None  # משתנה גלובלי שישמור את מילון הניקוד

import os

# בסמוך לראש הקובץ
MODULE_DIR  = os.path.dirname(__file__)              # …/SoulChart/src
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))  # …/SoulChart
DATA_DIR    = os.path.join(PROJECT_DIR, 'data')

def load_nikud_position_data():
    global nikud_position_data
    if nikud_position_data is None:
        nikud_position_data = {}
        try:
            with open(os.path.join(DATA_DIR, 'nikud_by_position.txt'), 'r', encoding='utf-8-sig') as f:
                current_nikud = None
                current_position = None

                for line in f:
                    line = line.strip()

                    if line.startswith("הניקוד"):  # שורה המתארת ניקוד חדש
                        current_nikud = line.split(" ")[1]  # זיהוי הניקוד
                        nikud_position_data[current_nikud] = {}

                    elif "באות" in line:  # זיהוי מיקום של הניקוד
                        current_position = line.split(" ")[1].strip(" ,")
                        match current_position:
                            case "הראשונה":
                                current_position = "ראשונה"
                            case "השנייה":
                                current_position = "שנייה"
                            case "השלישית":
                                current_position = "שלישית"
                            case "הרביעית":
                                current_position = "רביעית ואילך"
                        nikud_position_data[current_nikud][current_position] = line

                    elif line == '':
                        continue

                    else:
                        nikud_position_data[current_nikud][current_position] = line  # הוספת התוכן למיקום הנוכחי

        except Exception as e:
            print(f"Error reading the file: {e}")
    return nikud_position_data


def load_nikud_data():
    global nikud_data
    if nikud_data is None:  # טוענים רק אם עוד לא נטען
        nikud_data = {}
        try:
            with open(os.path.join(DATA_DIR, 'nikud.txt'), 'r', encoding='utf-8-sig') as f:
                current_nikud = None

                for line in f:
                    line = line.strip()

                    if line.startswith("הניקוד"):
                        current_nikud = line.split(" ")[1]
                        nikud_data[current_nikud] = line

                    elif line == "ניקוד וספירות":
                        break

                    elif current_nikud is not None:
                        nikud_data[current_nikud] += "\n" + line  # רק אם ניקוד קודם הוגדר

        except FileNotFoundError:
            print("שגיאה: הקובץ 'data/nikud.txt' לא נמצא.")
        except Exception as e:
            print(f"שגיאה בקריאת הקובץ: {e}")

    return nikud_data  # מחזירים את הנתונים שכבר נטענו

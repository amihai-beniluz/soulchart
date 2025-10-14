letters_nikud_data = None  # משתנה גלובלי שישמור את המילון

import os

# בסמוך לראש הקובץ
MODULE_DIR  = os.path.dirname(__file__)              # …/SoulChart/src
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))  # …/SoulChart
DATA_DIR    = os.path.join(PROJECT_DIR, 'data')

def load_letters_nikud_data():
    global letters_nikud_data
    if letters_nikud_data is None:
        letters_nikud_data = {}
        try:
            with open(os.path.join(DATA_DIR, 'letters_by_nikud.txt'), 'r', encoding='utf-8-sig') as f:
                current_letter = None

                for line in f:
                    line = line.strip()

                    if line.startswith("האות"):  # שורה המתארת ניקוד חדש
                        current_letter = line.split(" ")[1][0]  # זיהוי האות
                        letters_nikud_data[current_letter] = {}

                    elif line == '':
                        continue

                    else:
                        current_nikud = line.split(" ")[1].strip(":")[1:]
                        if current_nikud == "לא":
                            current_nikud = "ריק"
                        letters_nikud_data[current_letter][current_nikud] = line  # הוספת התוכן למיקום הנוכחי

        except Exception as e:
            print(f"Error reading the file: {e}")
    return letters_nikud_data

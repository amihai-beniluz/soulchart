letters_nikud_position_data = None  # משתנה גלובלי שישמור את המילון

import os

# בסמוך לראש הקובץ
MODULE_DIR  = os.path.dirname(__file__)              # …/SoulChart/src
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))  # …/SoulChart
DATA_DIR    = os.path.join(PROJECT_DIR, 'data')

def load_letters_nikud_position_data():
    global letters_nikud_position_data
    if letters_nikud_position_data is None:
        letters_nikud_position_data = {}
        try:
            with open(os.path.join(DATA_DIR, 'letters_by_nikud_position.txt'), 'r', encoding='utf-8-sig') as f:

                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("האות"):
                        try:
                            parts = line.split()
                            current_letter = parts[1][0]  # האות עצמה
                            current_nikud = parts[2][1:]       # הניקוד
                            if current_nikud == "לא":
                                current_nikud = "ריק"
                            current_position = parts[4] if parts[4] != "באות" else parts[5]
                            if current_position == "רביעית":
                                current_position += " ואילך"
                            else:
                                current_position = current_position.rstrip(':')

                            # אתחול מילונים פנימיים לפי הצורך
                            if current_letter not in letters_nikud_position_data:
                                letters_nikud_position_data[current_letter] = {}
                            if current_nikud not in letters_nikud_position_data[current_letter]:
                                letters_nikud_position_data[current_letter][current_nikud] = {}
                            if current_position not in letters_nikud_position_data[current_letter][current_nikud]:
                                letters_nikud_position_data[current_letter][current_nikud][current_position] = ""
                            letters_nikud_position_data[current_letter][current_nikud][current_position] += line + "\n"
                        except Exception as e:
                            print(f"שורת כותרת לא תקינה: {line} — {e}")

        except Exception as e:
            print(f"Error reading the file: {e}")
    return letters_nikud_position_data

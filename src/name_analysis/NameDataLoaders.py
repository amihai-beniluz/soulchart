import os
import re

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')


def load_letter_position_data():
    letter_position_data = {}
    try:
        with open(os.path.join(DATA_DIR, 'letters_by_position.txt'), 'r', encoding='utf-8-sig') as f:
            current_letter = None
            current_position = None

            for line in f:
                line = line.strip()

                if line.startswith("האות"):
                    current_letter = line.split(" ")[1][0]
                    letter_position_data[current_letter] = {}

                elif "כאות" in line:
                    current_position = line.split(" ")[1].strip(":")
                    if current_position == "רביעית":
                        current_position += " ואילך"

                elif line == '':
                    continue

                else:
                    letter_position_data[current_letter][current_position] = line

    except Exception as e:
        print(f"Error reading the file: {e}")

    return letter_position_data  # מחזירים את הנתונים שכבר נטענו


def load_element_position_data():
    element_position_data = {}
    try:
        with open(os.path.join(DATA_DIR, 'element_by_position.txt'), 'r', encoding='utf-8-sig') as f:
            current_element = None

            for line in f:
                line = line.strip()

                if line.startswith("יסוד"):
                    current_element = line.split(" ")[1]
                    element_position_data[current_element] = {}

                elif "באות" in line:
                    current_position = line.split(" ")[1].strip(":")
                    if current_position == "רביעית":
                        current_position += " ואילך"
                    element_position_data[current_element][current_position] = line

                else:
                    continue

    except Exception as e:
        print(f"Error reading the file: {e}")
    return element_position_data  # מחזירים את הנתונים שכבר נטענו


def load_letter_data():
    letter_data = {}
    try:
        with open(os.path.join(DATA_DIR, 'letters.txt'), 'r', encoding='utf-8-sig') as f:
            current_letter = None

            for line in f:
                line = line.strip()

                match = re.match(r"^האות ([א-ת])' -\s*", line)
                if match:
                    current_letter = match.group(1)
                    letter_data[current_letter] = line

                elif current_letter is not None:
                    letter_data[current_letter] += "\n" + line  # רק אם אות קודמת הוגדרה

    except FileNotFoundError:
        print("שגיאה: הקובץ 'data/letters.txt' לא נמצא.")
    except Exception as e:
        print(f"שגיאה בקריאת הקובץ: {e}")

    return letter_data  # מחזירים את הנתונים שכבר נטענו


def load_element_data():
    element_data = {}
    try:
        with open(os.path.join(DATA_DIR, 'element.txt'), 'r', encoding='utf-8-sig') as f:
            current_element = None

            for line in f:
                line = line.strip()

                if line.startswith("יסוד ה"):
                    current_element = line.split(" ")[1]
                    element_data[current_element] = line

                elif current_element is not None:
                    element_data[current_element] += "\n" + line  # רק אם ניקוד קודם הוגדר

    except FileNotFoundError:
        print("שגיאה: הקובץ 'data/element.txt' לא נמצא.")
    except Exception as e:
        print(f"שגיאה בקריאת הקובץ: {e}")

    return element_data  # מחזירים את הנתונים שכבר נטענו


def load_letters_nikud_data():
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


def load_nikud_position_data():
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


def load_letters_nikud_position_data():
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
                        current_nikud = parts[2][1:]  # הניקוד
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


def load_all_name_data():
    """טוען את כל הנתונים לזיכרון"""
    return {
        'letter_data': load_letter_data(),
        'nikud_data': load_nikud_data(),
        'element_data': load_element_data(),
        'letter_position_data': load_letter_position_data(),
        'element_position_data': load_element_position_data(),
        'nikud_position_data': load_nikud_position_data(),
        'letters_nikud_data': load_letters_nikud_data(),
        'letters_nikud_position_data': load_nikud_position_data()
    }

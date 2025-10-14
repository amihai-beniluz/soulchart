import re
import os

# בסמוך לראש הקובץ
MODULE_DIR = os.path.dirname(__file__)              # …/SoulChart/src/name_analysis
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))  # …/SoulChart
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

letter_position_data = None  # משתנה גלובלי, נטען פעם אחת בלבד
element_position_data = None  # משתנה גלובלי, נטען פעם אחת בלבד
letter_data = None  # משתנה גלובלי, נטען פעם אחת בלבד
element_data = None # משתנה גלובלי, נטען פעם אחת בלבד


def load_letter_position_data():
    global letter_position_data
    if letter_position_data is None:  # טוענים רק אם עוד לא נטען
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
    global element_position_data
    if element_position_data is None:  # טוענים רק אם עוד לא נטען
        element_position_data = {}
        try:
            with open(os.path.join(DATA_DIR, 'element_by_position.txt'), 'r', encoding='utf-8-sig') as f:
                current_element = None
                current_position = None

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
    global letter_data
    if letter_data is None:  # טוענים רק אם עוד לא נטען
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
    global element_data
    if element_data is None:  # טוענים רק אם עוד לא נטען
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

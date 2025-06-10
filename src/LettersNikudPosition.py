import re

letters_nikud_position_data = None  # משתנה גלובלי שישמור את המילון

def load_letters_nikud_position_data():
    global letters_nikud_position_data
    if letters_nikud_position_data is None:
        letters_nikud_position_data = {}
        try:
            with open('data/letters_by_nikud_position.txt', 'r', encoding='utf-8-sig') as f:
                current_letter = None
                current_nikud = None
                current_position = None

                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # שורת כותרת של אות חדשה
                    if line.startswith("אות "):
                        try:
                            current_letter = line.split()[1][0]
                            current_nikud = None
                            current_position = None
                        except Exception as e:
                            print(f"שורת אות לא תקינה: {line} — {e}")
                        continue

                    # שורת כותרת המתארת אות, ניקוד ומיקום
                    if line.startswith("האות"):
                        match = re.match(r"^האות\s+([\u0590-\u05EA])'\s+(.*?)\s+באות\s+([^:]+):\s*(.*)", line)
                        if match:
                            letter, nikud, position, text = match.groups()
                            nikud = nikud.lstrip('ב').strip()
                            if nikud == "ללא ניקוד" or nikud == "ללא":
                                nikud = "ריק"
                            if position == "רביעית ומעלה":
                                position = "רביעית ואילך"

                            letters_nikud_position_data.setdefault(letter, {}).setdefault(nikud, {})[position] = text + "\n"

                            current_letter = letter
                            current_nikud = nikud
                            current_position = position
                        else:
                            print(f"שורת כותרת לא תקינה: {line}")
                        continue

                    # המשך פסקה — הוסף לתוכן של המיקום הנוכחי
                    if current_letter and current_nikud and current_position:
                        letters_nikud_position_data[current_letter][current_nikud][current_position] += line + "\n"

        except Exception as e:
            print(f"Error reading the file: {e}")
    return letters_nikud_position_data

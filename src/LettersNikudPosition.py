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

                    if line.startswith("האות"):
                        try:
                            parts = line.split()
                            current_letter = parts[1][0]  # האות עצמה
                            current_nikud = parts[2][1:]       # הניקוד
                            if current_nikud == "ללא":
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

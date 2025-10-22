# ייבוא הפונקציות לטעינת המידע
from .NameDataLoaders import load_all_name_data
from src.utils import get_position_key, get_element_key, normalize_final_letters, position_to_word


class NameAnalysis:
    name_data = None

    def __init__(self, name, nikud_dict):
        self.name = name
        self.nikud_dict = nikud_dict

        # טעינת נתוני הניתוח האסטרולוגיים פעם אחת
        if NameAnalysis.name_data is None:
            NameAnalysis.name_data = load_all_name_data()

    def analyze_name(self):
        result = []
        letter_data = self.name_data['letter_data']
        nikud_data = self.name_data['nikud_data']
        element_data = self.name_data['element_data']
        letter_position_data = self.name_data['letter_position_data']
        element_position_data = self.name_data['element_position_data']
        nikud_position_data = self.name_data['nikud_position_data']
        letters_nikud_data = self.name_data['letters_nikud_data']
        letter_nikud_position_data = self.name_data['letters_nikud_position_data']
        position_text = {
            1: "האות הראשונה בשם מייצגת:\n\n1. את המוח ואת הראש הפיזי.\n2. את האינטליגנציה.\n3. את היכולת והרצון "
               "בלימודים.\n4. את יכולת התקשורת.\n5. את היכולת להסתדר בחברה מבחינת דיבור ותקשורת.\n6. את המודעות "
               "העצמית ואת הרוחניות.\n7. את האישיות הבסיסית של האדם.\n8. את יכולת הביטוי בכתב ובעל פה.\n9. האות "
               "הראשונה מזכירה את הבית הראשון במפה האסטרולוגית.\n",
            2: "האות השנייה בשם מייצגת:\n\n1. את הלב הפיזי.\n2. את צורת ההבעה הרגשית כלפי בן או בת הזוג.\n3. את הדרך "
               "בה מבטאים רגשות חיוביים באופן כללי.\n4. את היחס לרגשות - הפנמה, החצנה או דיכוי.\n5. את היחס הכללי לבני "
               "הזוג.\n6. את צורת חינוך הילדים.\n7. את המערכת הזוגית.\n8. את בן או בת הזוג המתאים לכל אדם.\n9. את "
               "מידת החיבור לרגשות.\n10. את מידת הצורך שלנו בזוגיות.\n11. את היחס לאהבה ולמין.\n12. האות השנייה "
               "מזכירה את בית 7 באסטרולוגיה - בית הנישואים\n",
            3: "האות השלישית בשם מייצגת:\n\n1. את הכבד בגוף האדם.\n2. את הכעסים.\n3. את הדרך להבעת כעסים, תסכול ורגשות "
               "שליליים באופן כללי.\n4. מהו התיקון של האדם בחיים הללו.\n5. את תכונות האופי השליליות.\n6. בשילוב עם "
               "האות השלישית בשמו של בן/ת הזוג ניתן להבין מה קורה לבני הזוג כשהם רבים זה עם זו.\n8. את הסיבות לכך "
               "שאין לאדם הצלחה בתחום מסוים בחיים.\n9. האות השלישית מזכירה את בית 12 במפה האסטרולוגית.\n",
            4: "האותיות רביעית ואילך בשם מייצגות:\n 1. כיצד אנו מביאים לידי פעולה את שאיפותינו ורצונותינו.\n2. כיצד "
               "נראה כרטיס הביקור שלנו בעיני הסביבה.\n3. עם אילו כישורים וסגולות אנו מסוגלים לממש את יכולותינו.\n4. "
               "כמה כוח פיזי ואנרגיה נפשית יש לנו.\n5. מאגרי הגוף של האדם.\n6. כיצד אנו נתפסים בעיני הזולת.\n7. "
               "אותיות אלה יכולות להראות על מרכז (רום) שמים וגם על בית 11 - בית החברים במפה האסטרולוגית.\n",
            'default': ""
        }

        for i, letter in enumerate(normalize_final_letters(self.name)):
            position = i + 1  # מיקום האות בשם (מתחילים מ-1)
            position_key = get_position_key(position)
            nikud = self.nikud_dict[position]  # ניקוד האות הנוכחית

            # הדפסת כותרת - האות הנוכחית וניקודה
            txt = "האות ה" + position_to_word(i) + " בשם " + self.name + " היא " + letter + "' בניקוד " + nikud
            result.append(txt)
            result.append("")

            # המיקום
            txt = position_text.get(position, position_text['default'])
            result.append(txt)
            result.append("")

            # האות
            if letter in letter_data and letter_data[letter] not in ''.join(result):
                result.append(letter_data[letter])
                result.append("")

            # היסוד
            element = get_element_key(letter)
            if element in element_data and element_data[element] not in ''.join(result):
                result.append(element_data[element])
                result.append("")

            # ניתוח היסוד ביחס למיקום
            if element in element_position_data and position_key in element_position_data[element] and \
                    element_position_data[element][position_key] not in ''.join(result):
                result.append(f"יסוד {element} {element_position_data[element][position_key]}\n")
                result.append("")

            # ניתוח האות ביחס למיקום
            if letter in letter_position_data and position_key in letter_position_data[letter] and \
                    letter_position_data[letter][position_key] not in ''.join(result):
                result.append(f"{letter}' כאות {position_key}: {letter_position_data[letter][position_key]}")
                result.append("")

            # הניקוד
            if nikud in nikud_data and nikud_data[nikud] not in ''.join(result):
                result.append(nikud_data[nikud])
                result.append("")

            # ניתוח הניקוד ביחס למיקום
            if nikud in nikud_position_data and position_key in nikud_position_data[nikud] and \
                    nikud_position_data[nikud][position_key] not in ''.join(result):
                result.append(f"ניקוד {nikud} באות ה{position_key}: {nikud_position_data[nikud][position_key]}")
                result.append("")

            # ניתוח האות ביחס לניקוד
            if letter in letters_nikud_data and nikud in letters_nikud_data[letter] and \
                    letters_nikud_data[letter][nikud] not in ''.join(result):
                result.append(letters_nikud_data[letter][nikud])
                result.append("")

            # ניתוח האות ביחס למיקום ולניקוד
            if letter in letter_nikud_position_data and nikud in letter_nikud_position_data[letter] and \
                    position_key in letter_nikud_position_data[letter][nikud] and \
                    letter_nikud_position_data[letter][nikud][position_key] not in ''.join(result):
                result.append(f"{letter_nikud_position_data[letter][nikud][position_key]}")
                result.append("")

            result.append("--------\n")

        return result

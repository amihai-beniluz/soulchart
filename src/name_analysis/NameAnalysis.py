# ייבוא הפונקציות לטעינת המידע
from .LettersAnalysis import load_letter_position_data, load_letter_data, load_element_data, load_element_position_data
from .LettersNikud import load_letters_nikud_data
from .NikudAnalysis import load_nikud_position_data, load_nikud_data
from .LettersNikudPosition import load_letters_nikud_position_data


class NameAnalysis:
    letter_data = None
    nikud_data = None
    element_data = None
    letter_position_data = None
    element_position_data = None
    nikud_position_data = None
    letters_nikud_data = None
    letters_nikud_position_data = None

    def __init__(self, name, nikud_dict):
        self.name = name
        self.nikud_dict = nikud_dict
        if NameAnalysis.letter_data is None:
            NameAnalysis.letter_data = load_letter_data()  # טוען את נתוני האות
        if NameAnalysis.nikud_data is None:
            NameAnalysis.nikud_data = load_nikud_data()  # טוען את נתוני הניקוד
        if NameAnalysis.element_data is None:
            NameAnalysis.element_data = load_element_data()  # טוען את נתוני היסוד
        if NameAnalysis.letter_position_data is None:
            NameAnalysis.letter_position_data = load_letter_position_data()  # טוען את נתוני האות והמיקום
        if NameAnalysis.element_position_data is None:
            NameAnalysis.element_position_data = load_element_position_data()  # טוען את נתוני האלמנט והמיקום
        if NameAnalysis.nikud_position_data is None:
            NameAnalysis.nikud_position_data = load_nikud_position_data()  # טוען את נתוני הניקוד והמיקום
        if NameAnalysis.letters_nikud_data is None:
            NameAnalysis.letters_nikud_data = load_letters_nikud_data()  # טוען את נתוני הניקוד והאות
        if NameAnalysis.letters_nikud_position_data is None:
            NameAnalysis.letters_nikud_position_data = load_letters_nikud_position_data()  # טוען את נתוני האות הניקוד והמיקום

    def analyze_name(self, colors=True):
        result = []
        letter_data = NameAnalysis.letter_data
        nikud_data = NameAnalysis.nikud_data
        element_data = NameAnalysis.element_data
        letter_position_data = NameAnalysis.letter_position_data
        element_position_data = NameAnalysis.element_position_data
        nikud_position_data = NameAnalysis.nikud_position_data
        letters_nikud_data = NameAnalysis.letters_nikud_data
        letter_nikud_position_data = NameAnalysis.letters_nikud_position_data
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

        for i, letter in enumerate(self.normalize_final_letters(self.name)):
            position = i + 1  # מיקום האות בשם (מתחילים מ-1)
            position_key = self.get_position_key(position)
            nikud = self.nikud_dict[position]  # ניקוד האות במיקום הנוכחי

            # הדפסת כותרת - האות הנוכחית וניקודה
            txt = "האות ה" + self.position_to_word(i) + " בשם " + self.name + " היא " + letter + "' בניקוד " + nikud
            if colors:
                result.append("\033[97m" + txt + "\033[0m\n\n")
            else:
                result.append(txt+"\n\n")

            # המיקום
            txt = position_text.get(position, position_text['default'])
            if colors:
                result.append("\033[36m" + txt + "\033[0m\n\n")
            else:
                result.append(txt+"\n\n")

            # האות
            if letter in letter_data and letter_data[letter] not in ''.join(result):
                if colors:
                    result.append("\033[35m" + letter_data[letter] + "\033[0m\n\n")
                else:
                    result.append(letter_data[letter]+"\n\n")

            # היסוד
            element = self.get_element_key(letter)
            if element in element_data and element_data[element] not in ''.join(result):
                if colors:
                    result.append("\033[93m" + element_data[element] + "\033[0m\n\n")
                else:
                    result.append(element_data[element]+"\n\n")

            # ניתוח היסוד ביחס למיקום
            if element in element_position_data and position_key in element_position_data[element] and \
                    element_position_data[element][position_key] not in ''.join(result):
                if colors:
                    result.append("\033[31m" + f"יסוד {element} {element_position_data[element][position_key]}\n + \033[0m\n\n")
                else:
                    result.append(f"יסוד {element} {element_position_data[element][position_key]}\n\n\n")

            # ניתוח האות ביחס למיקום
            if letter in letter_position_data and position_key in letter_position_data[letter] and \
                    letter_position_data[letter][position_key] not in ''.join(result):
                if colors:
                    result.append(f"\033[94m{letter}' כאות {position_key}: {letter_position_data[letter][position_key]}"
                                  f"\n\033[0m")
                else:
                    result.append(f"{letter}' כאות {position_key}: {letter_position_data[letter][position_key]}\n")

            # הניקוד
            if nikud in nikud_data and nikud_data[nikud] not in ''.join(result):
                if colors:
                    result.append("\033[30m" + nikud_data[nikud] + "\033[0m\n\n")
                else:
                    result.append(nikud_data[nikud] + "\n\n")

            # ניתוח הניקוד ביחס למיקום
            if nikud in nikud_position_data and position_key in nikud_position_data[nikud] and \
                    nikud_position_data[nikud][position_key] not in ''.join(result):
                if colors:
                    result.append("\033[93m" + f"ניקוד {nikud} באות ה{position_key}: "
                                           f"{nikud_position_data[nikud][position_key]}\n\033[0m")
                else:
                    result.append(f"ניקוד {nikud} באות ה{position_key}: {nikud_position_data[nikud][position_key]}\n")

            # ניתוח האות ביחס לניקוד
            if letter in letters_nikud_data and nikud in letters_nikud_data[letter] and \
                    letters_nikud_data[letter][nikud] not in ''.join(result):
                if colors:
                    result.append("\033[91m" + letters_nikud_data[letter][nikud] + "\033[0m\n\n")
                else:
                    result.append(letters_nikud_data[letter][nikud] + "\n\n")

            # ניתוח האות ביחס למיקום ולניקוד
            if letter in letter_nikud_position_data and nikud in letter_nikud_position_data[letter] and \
                    position_key in letter_nikud_position_data[letter][nikud] and \
                    letter_nikud_position_data[letter][nikud][position_key] not in ''.join(result):
                if colors:
                    result.append("\033[94m" + f"{letter_nikud_position_data[letter][nikud][position_key]}\n\033[0m")
                else:
                    result.append(f"{letter_nikud_position_data[letter][nikud][position_key]}\n")

            result.append("--------\n")

        return result

    @staticmethod
    def get_position_key(position):
        if position == 1:
            return "ראשונה"
        elif position == 2:
            return "שנייה"
        elif position == 3:
            return "שלישית"
        else:
            return "רביעית ואילך"

    @staticmethod
    def get_element_key(letter):
        element_mapping = {
            "האש": {'ג', 'ד', 'ה', 'ט', 'כ', 'ס', 'ש'},
            "האוויר": {'א', 'ז', 'ל', 'פ', 'צ', 'ר'},
            "המים": {'ח', 'מ', 'נ', 'ק', 'ת'},
            "האדמה": {'ב', 'ו', 'י', 'ע'}
        }

        for element, letters in element_mapping.items():
            if letter in letters:
                return element

        return None  # במקרה שהאות אינה מופיעה בטבלה

    @staticmethod
    def normalize_final_letters(text):
        final_letters_map = {
            'ך': 'כ',
            'ם': 'מ',
            'ן': 'נ',
            'ף': 'פ',
            'ץ': 'צ'
        }
        return ''.join(final_letters_map.get(char, char) for char in text)

    @staticmethod
    def position_to_word(index):
        words_map = ["ראשונה", "שניה", "שלישית", "רביעית", "חמישית", "שישית", "שביעית", "שמינית", "תשיעית", "עשירית",
                     "אחת-עשרה", "שתים-עשרה", "שלוש-עשרה", "ארבע-עשרה", "חמש-עשרה", "שש-עשרה", "הפסקתי לספור"]
        if index >= 17:
            index = 17
        return words_map[index]

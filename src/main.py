from src.NameAnalysis import NameAnalysis
import textwrap


def main():
    # # צבעי טקסט שונים באמצעות קודי ANSI
    # print("\033[30m hello world (שחור)\033[0m")
    # print("\033[31m hello world (אדום)\033[0m")
    # print("\033[32m hello world (ירוק)\033[0m")
    # print("\033[33m hello world (צהוב)\033[0m")
    # print("\033[34m hello world (כחול)\033[0m")
    # print("\033[35m hello world (מג'נטה)\033[0m")
    # print("\033[36m hello world (טורקיז)\033[0m")
    # print("\033[37m hello world (לבן)\033[0m")
    #
    # # הדגשת טקסט (בהיר יותר)
    # print("\033[90m hello world (אפור בהיר)\033[0m")
    # print("\033[91m hello world (אדום בהיר)\033[0m")
    # print("\033[92m hello world (ירוק בהיר)\033[0m")
    # print("\033[93m hello world (צהוב בהיר)\033[0m")
    # print("\033[94m hello world (כחול בהיר)\033[0m")
    # print("\033[95m hello world (מג'נטה בהיר)\033[0m")
    # print("\033[96m hello world (טורקיז בהיר)\033[0m")
    # print("\033[97m hello world (לבן בוהק)\033[0m")

    name = input("הכנס את השם שלך: ").strip()

    # מילון שבו נשמרים הניקודים של כל אות
    nikud_dict = {}

    # קלט לכל אות בשם
    for i, letter in enumerate(name):
        nikud = input(f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, כתוב ריק) ")
        if nikud:  # אם הוזן ניקוד
            nikud_dict[i + 1] = nikud  # המיקום הוא אינדקס + 1

    # יצירת אובייקט לניתוח השם
    analysis = NameAnalysis(name, nikud_dict)

    # קבלת התוצאה של ניתוח השם
    result = analysis.analyze_name()

    # הדפסת התוצאה
    wrapper = textwrap.TextWrapper(width=150)  # רוחב שורה

    print("\n")
    for line in result:
        print(line+"\n")
        # אם השורה מכילה "\n", מפרק אותה לרשימת שורות
        """split_lines = line.split("\n")

        for single_line in split_lines:
            if len(single_line) > 150:  # אם השורה ארוכה מדי, עוטפים אותה
                wrapped_lines = wrapper.wrap(single_line)
                for wrapped in wrapped_lines:
                    print(wrapped.rjust(150))  # יישור לימין
            else:
                print(single_line.rjust(150))  # יישור לימין ללא שינוי"""


if __name__ == "__main__":
    main()

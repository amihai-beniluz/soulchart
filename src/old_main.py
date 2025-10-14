import os  # ייבוא מודול ה-OS
from src.name_analysis.NameAnalysis import NameAnalysis
import textwrap


def main():
    name = input("הכנס את השם שלך: ").strip()

    # הגדרת נתיב התיקייה ושם הקובץ
    output_dir = "names"
    output_filename = name + ".txt"
    # בניית הנתיב המלא באופן תואם מערכות הפעלה
    output_path = os.path.join(output_dir, output_filename)

    # ❗ יצירת התיקייה "names" אם היא אינה קיימת ❗
    try:
        # os.makedirs יוצרת את כל תיקיות האב החסרות
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        # אם יש בעיה בהרשאות או משהו אחר
        print(f"❌ אירעה שגיאה קריטית ביצירת התיקייה: {e}")
        return  # עצור את התוכנית כי לא ניתן לשמור את הקובץ

    # מילון שבו נשמרים הניקודים של כל אות
    nikud_dict = {}

    # קלט לכל אות בשם
    for i, letter in enumerate(name):
        nikud = input(f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, כתוב ריק) ")
        if nikud:  # אם הוזן ניקוד
            nikud_dict[i + 1] = nikud  # המיקום הוא אינדקס + 1

    # יצירת אובייקט לניתוח השם
    # הנחה: המחלקה NameAnalysis זמינה
    try:
        analysis = NameAnalysis(name, nikud_dict)
    except NameError:
        print("❌ שגיאה: וודא שהקובץ 'NameAnalysis.py' קיים בתיקיית 'src'.")
        return
    except Exception as e:
        print(f"❌ שגיאה בעת אתחול NameAnalysis: {e}")
        return

    # קבלת התוצאה של ניתוח השם
    result = analysis.analyze_name(False)

    # פתיחת קובץ במצב כתיבה ("w") וכתיבת הפלט אליו
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            wrapper = textwrap.TextWrapper(width=150)

            file.write("\n")
            for line in result:
                file.write(line + "\n")

        print(f"\n✅ התוצאה נשמרה בהצלחה בקובץ: {output_path}")

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בכתיבה לקובץ: {e}")


if __name__ == "__main__":
    main()
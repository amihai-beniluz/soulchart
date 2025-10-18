# src/ui/gui_app.py

import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from datetime import datetime
import threading
import traceback

# --- הייבוא היחסי ---
from src.user import User
from src.name_analysis.NameAnalysis import NameAnalysis
from src.birth_chart_analysis.ChartAnalysis import ChartAnalysis


# --------------------

class SoulChartApp:
    def __init__(self, master):
        self.master = master
        master.title("SoulChart - ניתוח רוחני אינטגרטיבי")
        master.geometry("800x600")

        # 1. יצירת וידג'ט ScrolledText להצגת התוצאות
        self.result_area = scrolledtext.ScrolledText(
            master,
            wrap=tk.WORD,
            width=80,
            height=30,
            font=("Arial", 12),
            state=tk.DISABLED
        )
        self.result_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # --- השלב הקריטי: הגדרת תגית ליישור לימין ---
        self.result_area.tag_configure("right_align", justify="right")

        # 2. כפתור הפעלת הניתוח
        self.analyze_button = tk.Button(
            master,
            text="התחל ניתוח (הזנת פרטים)",
            command=self.run_analysis_gui
        )
        self.analyze_button.pack(pady=10)

        # משתנים לאחסון נתוני משתמש
        self.user = None
        self.nikud_dict = {}

    def insert_text(self, text):
        """פונקציה נוחה להוספת טקסט לאזור התוצאות."""
        # קוראים לזה ב-master.after כדי שזה ירוץ ב-Main Thread
        self.result_area.config(state=tk.NORMAL)
        self.result_area.insert(tk.END, text + "\n")
        self.result_area.config(state=tk.DISABLED)
        self.result_area.see(tk.END)

    def display_results(self, text_to_display):
        # 1. מחיקת תוכן קודם
        self.result_area.delete(1.0, tk.END)

        # 2. הוספת הטקסט החדש
        self.result_area.insert(1.0, text_to_display)

        # 3. **החלת התגית** על כל הטקסט (מ-"1.0" עד "end")
        self.result_area.tag_add("right_align", "1.0", tk.END)

    def get_user_input_gui(self):
        """אוסף נתונים מהמשתמש באמצעות תיבות דו-שיח פשוטות (SimpleDialog)."""

        # 1. שם
        name = simpledialog.askstring("קלט", "הכנס את השם שלך:")
        if not name:
            return None, None

        # 2. תאריך לידה
        birthdate = None
        birthdate_str = simpledialog.askstring("קלט", "הכנס תאריך לידה (YYYY-MM-DD):")
        try:
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messagebox.showerror("שגיאה", "פורמט תאריך לא תקין. אנא נסה שוב.")
            return None, None

        # 3. שעת לידה
        birthtime = None
        birthtime_str = simpledialog.askstring("קלט", "הכנס שעת לידה (HH:MM, אופציונלי):", initialvalue="12:00")
        if birthtime_str:
            try:
                birthtime = datetime.strptime(birthtime_str, '%H:%M').time()
            except ValueError:
                messagebox.showwarning("אזהרה", "פורמט שעת לידה לא תקין. הניתוח ימשיך ללא שעה מדויקת.")

        # 4. מיקום (קואורדינטות)
        location = None
        location_str = simpledialog.askstring("קלט", "הכנס מיקום לידה (Lat, Lon):", initialvalue="31.78, 35.21")

        if location_str:
            try:
                lat_str, lon_str = location_str.split(',')
                location = (float(lat_str.strip()), float(lon_str.strip()))
            except ValueError:
                messagebox.showwarning("אזהרה", "פורמט קואורדינטות לא תקין. הניתוח ימשיך ללא מיקום מדויק.")

        # 5. קלט ניקוד
        nikud_dict = {}
        messagebox.showinfo("ניקוד", "כעת תתבקש להזין ניקוד לכל אות (לחץ OK להתחלה).")
        for i, letter in enumerate(name):
            nikud = simpledialog.askstring("קלט ניקוד", f"מהו הניקוד של האות '{letter}'? (אם אין ניקוד, לחץ OK)")
            if nikud:
                nikud_dict[i + 1] = nikud

        self.user = User(name, birthdate, birthtime, location)
        return self.user, nikud_dict

    def run_analysis_gui(self):
        """מתחיל את תהליך איסוף הקלט, ומפעיל את הניתוח בתהליך נפרד."""

        # איסוף הקלט חייב לקרות ב-Main Thread
        user, nikud_dict = self.get_user_input_gui()

        if not user or not user.name or not user.birthdate:
            self.insert_text("❌ הניתוח בוטל או שחסרים נתונים חיוניים.")
            return

        self.user = user
        self.nikud_dict = nikud_dict

        # ניקוי ממשק והצגת הודעת התחלה
        self.result_area.config(state=tk.NORMAL)
        self.result_area.delete(1.0, tk.END)
        self.result_area.config(state=tk.DISABLED)
        self.insert_text("...⏳ הניתוח מתבצע ברקע. אנא המתן ...\n")
        self.analyze_button.config(state=tk.DISABLED, text="ניתוח מתבצע...")  # נטרול כפתור

        # הפעלת הניתוח בתהליך נפרד
        analysis_thread = threading.Thread(target=self.start_analysis_thread)
        analysis_thread.start()

    def start_analysis_thread(self):
        """מכיל את כל לוגיקת הניתוח הארוכה (רץ בתהליך רקע)."""

        user = self.user
        nikud_dict = self.nikud_dict
        full_report = []

        # --- הצגת פרטי המשתמש ---
        full_report.append(f"--- ניתוח SoulChart עבור {user.name} ---")
        full_report.append(f"פרטים: {user.get_birth_info()}\n")

        # 1. ניתוח שם
        try:
            full_report.append("--- ביצוע ניתוח שם (קבלי/נומרולוגי) ---")
            name_analysis = NameAnalysis(user.name, nikud_dict)
            name_result = name_analysis.analyze_name(False)

            # *** תיקון: איחוד התוצאות למחרוזת אחת ***
            name_text = "\n".join(line.rstrip('\n') for line in name_result)
            full_report.append(name_text)
            full_report.append("✅ ניתוח שם הסתיים בהצלחה.")
        except Exception as e:
            full_report.append(f"❌ אירעה שגיאה בניתוח שם: {e}")

        full_report.append("\n" + "=" * 50 + "\n")

        # 2. ניתוח מפת לידה
        try:
            full_report.append("--- ביצוע ניתוח מפת לידה (אסטרולוגי) ---")

            if user.birthtime and user.location:
                chart_analysis = ChartAnalysis(user)

                chart_result = chart_analysis.analyze_chart(True)

                # *** תיקון: איחוד התוצאות למחרוזת אחת ***
                # שורה 162 מתוקנת: חיבור הרשימה chart_result ישירות
                chart_text = "\n".join(chart_result)
                full_report.append(chart_text)
                full_report.append("✅ ניתוח מפת לידה הסתיים בהצלחה.")
            else:
                full_report.append("⚠️ חסרים שעת לידה ו/או מיקום מדויקים. ניתוח מפת לידה דולג.")

        except Exception as e:
            tb_str = traceback.format_exc()
            full_report.append(f"❌ אירעה שגיאה קריטית בניתוח מפת לידה: {e}")
            full_report.append("\n--- פרטי שגיאה מלאים: ---\n")
            full_report.append(tb_str)
            full_report.append("---")

        # --- העברת הדו"ח המלא בבלוק אחד ל-GUI ---
        final_report_text = "\n".join(full_report)

        # עדכון ה-GUI בקריאה אחת בלבד
        self.master.after(0, lambda: self.set_final_report(final_report_text))

        # שחרור הכפתור
        self.master.after(0, lambda: self.analyze_button.config(state=tk.NORMAL, text="התחל ניתוח (הזנת פרטים)"))

    def set_final_report(self, text):
        """מעדכן את כל הטקסט באזור התוצאות בבת אחת."""
        self.result_area.config(state=tk.NORMAL)
        # ניקוי הטקסט המקורי של 'אנא המתן'
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, text + "\n")
        self.result_area.config(state=tk.DISABLED)
        self.result_area.see(tk.END)


# --- קוד הפעלה ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SoulChartApp(root)
    root.mainloop()

import requests
import json
import os
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
# *** שינוי קריטי: ייבוא Lock ***
from threading import Lock

# --- הגדרות ---

# כתובת ה-API של מודל השפה (Gemini 2.5 Flash)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# **שינוי קריטי: רשימת 5 המפתחות שלך**
# ודא שהרשימה מכילה 5 מפתחות מלאים ומדויקים.
# ami.ben700
# API_KEYS = os.getenv("API_KEYS")
# ami.ben710
API_KEYS = os.getenv("NEW_API_KEYS")

# קובץ קלט המכיל את ההיבטים (שורה לכל היבט)
INPUT_FILE = "planet_house_sign_analysis_errors.txt"

# קובץ פלט אליו ייכתבו הניתוחים
OUTPUT_FILE = "planet_house_sign_analysis_errors_output.txt"

# הגדרת מקסימום הליכים (Threads) מקבילים
MAX_WORKERS = 150

# משתנים גלובליים לניהול מפתחות
CURRENT_KEY_INDEX = 1
# הגדרה ראשונית של המפתח: אם הריצה הקודמת עבדה על מפתח מס' 2, התחל ממנו
# אם אתה רוצה להתחיל מהמפתח הראשון שלא נחסם (למשל מפתח #3), שנה את האינדקס כאן:
# CURRENT_KEY_INDEX = 2
CURRENT_API_KEY = API_KEYS[CURRENT_KEY_INDEX]
QUOTA_EXCEEDED_CURRENT_KEY = False

# **אובייקט Lock גלובלי לניהול גישה למשתנים המשותפים**
KEY_SWITCH_LOCK = Lock()


# --- פונקציות עזר לקריאה וכתיבה ---

def get_completed_aspects_from_output():
    """
    [מנגנון בדיקת תוכן]
    קורא את קובץ הפלט ומחלץ את שמות ההיבטים שעובדו בהצלחה.
    """
    completed_aspects = set()
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]

        for i in range(0, len(lines), 3):
            if i < len(lines) and lines[i]:
                aspect_name = lines[i]
                if not aspect_name.startswith('[שגיאה:'):
                    completed_aspects.add(aspect_name)

    except FileNotFoundError:
        return set()
    except Exception as e:
        tqdm.write(f"שגיאה בקריאת קובץ הפלט: {e}. ממשיך עם הנתונים שנמצאו.")
        return completed_aspects

    return completed_aspects


def read_aspects(filename):
    """קורא את שמות ההיבטים מקובץ הטקסט."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"שגיאה: קובץ הקלט לא נמצא: {filename}")
        return []
    except Exception as e:
        print(f"שגיאה בקריאת קובץ הקלט: {e}")
        return []


def switch_to_next_key():
    """
    מנסה לעבור למפתח ה-API הבא ברשימה, תוך שימוש ב-Lock.
    """
    global CURRENT_KEY_INDEX, CURRENT_API_KEY, QUOTA_EXCEEDED_CURRENT_KEY

    # *** שימוש ב-Lock: רק Thread אחד יכול להיכנס לבלוק הזה ***
    with KEY_SWITCH_LOCK:

        # בדיקה כפולה: אם thread אחר כבר העביר את המפתח, נצא מכאן
        if QUOTA_EXCEEDED_CURRENT_KEY is False:
            tqdm.write("הופעל Lock, אך מפתח כבר הוחלף. ממשיך...")
            return True

        CURRENT_KEY_INDEX += 1

        if CURRENT_KEY_INDEX < len(API_KEYS):
            CURRENT_API_KEY = API_KEYS[CURRENT_KEY_INDEX]
            QUOTA_EXCEEDED_CURRENT_KEY = False
            tqdm.write(f"\n🔑🔑🔑 **עובר למפתח #{CURRENT_KEY_INDEX + 1}** (פרויקט חדש). הריצה ממשיכה! 🔑🔑🔑\n")
            # לאחר מעבר מפתח, נחכה רגע קצר לאתחול
            time.sleep(2)
            return True
        else:
            # אם אין עוד מפתחות, מפסיקים את הריצה
            QUOTA_EXCEEDED_CURRENT_KEY = True
            return False


def get_llm_response(aspect_name):
    """
    שולח את ההיבט הספציפי ל-API ומחזיר את טקסט התשובה.
    """
    global CURRENT_API_KEY, QUOTA_EXCEEDED_CURRENT_KEY

    if QUOTA_EXCEEDED_CURRENT_KEY and CURRENT_KEY_INDEX == len(API_KEYS) - 1:
        return f"[שגיאה: כל המכסות היומיות נגמרו.]"

    full_url = f"{API_URL}?key={CURRENT_API_KEY}"
    headers = {"Content-Type": "application/json"}

    # ... (הגדרת contents ו-payload זהה) ...
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": "תאר את המשמעות האסטרולוגית של : " + aspect_name}
            ]
        }
    ]
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [
                {
                    "text": "אתה אסטרולוג מערבי מנוסה ומומחה. הניתוחים שלך צריכים להיות איכותיים מדויקים ובעלי פרשנות פסיכולוגית. ענה בעברית תקנית ובפסקה אחת עשירה."
                }
            ]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 10000
        }
    }
    # ... (סוף הגדרת contents ו-payload) ...

    # לולאה שתנסה עד שהבקשה תצליח או עד שיגמרו כל המפתחות
    while True:
        try:
            response = requests.post(full_url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    content = candidate.get('content', {})
                    parts = content.get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
                pass

            # **השינוי הקריטי: טיפול בשגיאת 429**
            if response.status_code == 429:
                tqdm.write(f"\n🚨🚨🚨 **שגיאה: 429 - מכסה יומית נגמרה למפתח #{CURRENT_KEY_INDEX + 1}.** 🚨🚨🚨")

                # אם המפתח הוחלף בהצלחה (על ידי thread אחר או זה הנוכחי)
                if switch_to_next_key():
                    full_url = f"{API_URL}?key={CURRENT_API_KEY}"
                    continue  # ממשיך לנסות עם המפתח החדש
                else:
                    # אם נגמרו כל המפתחות
                    return f"[שגיאה חריגה ממכסה יומית: 429. נגמרו כל המפתחות.]"

            # אם קיבלנו שגיאת 503 (זמנית) או שגיאת 400 אחרת (לא 429), מבצעים Backoff קצר
            if response.status_code == 503 or response.status_code >= 400:
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            # טיפול ב-Timeouts או שגיאות רשת אחרות
            wait_time = 5
            tqdm.write(f"  [אזהרה: שגיאת רשת/חיבור/API עבור **{aspect_name}**: {e}. ממתין {wait_time} שניות...]")
            time.sleep(wait_time)
            return f"[שגיאה רשת/חיבור: {e}]"

        except Exception as e:
            return f"[שגיאה פנימית קריטית: {e}]"

    return f"[שגיאה לא ידועה: {response.text}]"


def process_single_aspect(aspect):
    """פונקציית עטיפה ל-get_llm_response שמחזירה את ההיבט והתשובה."""
    llm_answer = get_llm_response(aspect)

    if QUOTA_EXCEEDED_CURRENT_KEY:
        return aspect, "[מכסה נגמרה]"

    return aspect, llm_answer


def save_result(aspect, llm_answer):
    """כתיבה של תוצאה בודדת לקובץ בצורה מוגנת."""
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{aspect.strip()}\n")
        f.write(f"{llm_answer.strip()}\n")
        f.write("\n")


def process_batch():
    """קורא את כל ההיבטים ומעבד אותם במקביל באמצעות ThreadPoolExecutor."""

    # --- 1. בדיקת תוכן וסינון קובץ הקלט (מוודא שלא נעבד שוב) ---
    completed_aspects = get_completed_aspects_from_output()
    all_input_aspects = read_aspects(INPUT_FILE)

    # סינון ההיבטים: משאיר רק את אלו שטרם עובדו
    aspects_to_process = [aspect for aspect in all_input_aspects if aspect not in completed_aspects]

    # כותב מחדש את קובץ הקלט עם ההיבטים הנותרים בלבד
    if len(aspects_to_process) < len(all_input_aspects):
        with open(INPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(aspects_to_process) + '\n')

        tqdm.write(
            f"\n✅ נמחקו {len(all_input_aspects) - len(aspects_to_process)} שורות מעובדות מקובץ הפלט (בדיקת תוכן).")
        tqdm.write(f"   הריצה תמשיך כעת עם {len(aspects_to_process)} היבטים שנותרו.\n")

    aspects = aspects_to_process
    # ----------------------------------------------------

    if not aspects:
        print("כל ההיבטים בקובץ הקלט כבר עובדו. סיום.")
        return

    total_aspects = len(aspects)
    print(f"נמצאו {total_aspects} היבטים חדשים לעיבוד. מתחיל בשליחת בקשות במקביל (עד {MAX_WORKERS} בבת אחת)...")
    print("----------------------------------------------------")
    tqdm.write(f"**מתחיל עם מפתח #{CURRENT_KEY_INDEX + 1}. סך המכסה הזמינה (5 מפתחות): כ-50,000 קריאות.**")
    print("----------------------------------------------------")

    pbar = tqdm(total=total_aspects, desc="עיבוד היבטים", leave=True, unit="item")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_single_aspect, aspect): aspect for aspect in aspects}

        for future in as_completed(futures):
            # אם נגמרו כל המפתחות, יוצאים מהריצה
            if QUOTA_EXCEEDED_CURRENT_KEY and CURRENT_KEY_INDEX == len(API_KEYS) - 1:
                pbar.write("נגמרו כל המפתחות. סיום הריצה.")
                executor.shutdown(wait=False, cancel_futures=True)
                break

            try:
                aspect, llm_answer = future.result()

                # שמירה רק אם לא הייתה שגיאת מכסה גלובלית
                if not llm_answer.endswith("[מכסה נגמרה]"):
                    save_result(aspect, llm_answer)

                    status_char = '✅' if not llm_answer.startswith('[שגיאה:') else '❌'
                    pbar.write(f"**הושלם:** {aspect} {status_char}")

                pbar.update(1)

            except Exception as e:
                failed_aspect = futures[future]
                pbar.write(f"!!! שגיאה קריטית בעיבוד היבט: **{failed_aspect}**. שגיאה: {e}")
                pbar.update(1)

    pbar.close()

    print("\n----------------------------------------------------")
    print(f"סיום עיבוד אצווה. הפלט נשמר ב: {os.path.abspath(OUTPUT_FILE)}")
    print("----------------------------------------------------")


# --- הפעלת הסקריפט ---

if __name__ == "__main__":
    process_batch()
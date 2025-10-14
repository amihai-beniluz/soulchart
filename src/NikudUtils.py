# NikudUtils.py
import requests

from transformers import pipeline

# טוענים את המודל המתאים לניקוד עברי
nlp = pipeline("text2text-generation", model="avichr/heBERT")

def get_nikud(word):
    result = nlp(word)
    return result[0]['generated_text']


def get_nikud_from_site(text):
    url = "https://www.call2all.co.il/ym/api/UploadTextFile"

    # פרמטרים (ה-token שלך צריך להיות כאן)
    params = {
        "token": "0795000000:1234",  # הכנס את ה-token המתאים
        "what": "ivr2/000",
        "tts": "000",  # אתה יכול לבדוק את הערך המתאים
        "contents": text  # הטקסט שברצונך לנקד
    }

    # שליחת הבקשה ל-API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        # אם הכל עבר בהצלחה, נקבל את התוצאה
        return response.text
    else:
        # במידה ויש שגיאה
        print(f"Error: {response.status_code}")
        return None


# פיצול המילה המנוקדת לאותיות ולניקודים
def split_nikud(nikud_word):
    word_parts = []
    current_letter = ''
    current_nikud = ''

    for char in nikud_word:
        if char.isalpha():
            if current_letter:
                word_parts.append((current_letter, current_nikud))
            current_letter = char
            current_nikud = ''
        else:
            current_nikud += char

    if current_letter:
        word_parts.append((current_letter, current_nikud))

    return word_parts

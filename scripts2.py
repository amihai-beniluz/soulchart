import itertools

# 1. הגדרת הקבוצות
H = list(range(1, 13))  # Houses: 1, 2, ..., 12 (i, k)
S = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]  # Signs (j)
B = ["is", "is not"]  # Retrograde/Intercepted options (b1, b2)
D = [1, 2, 3, 0, -1, -2, -3]  # Displacement/Offset (d)

# 2. פונקציית השליט (ruler(S)) - אסטרולוגיה מערבית מודרנית
RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Pluto",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Uranus",
    "Pisces": "Neptune"
}

# 3. יצירת המכפלה הקרטזית של אינדקסים/ערכים
all_combinations = itertools.product(
    H,  # i (House 1)
    range(len(S)),  # j_index (Index for Sign 1)
    B,  # b1 (is/is not retrogated)
    H,  # k (House 2)
    D,  # d (Offset)
    B  # b2 (is/is not intercepted)
)

# 4. הגדרת שם הקובץ ומספר המשפטים הצפוי
file_name = "astrological_sentences.txt"
expected_length = 12 * 12 * 2 * 12 * 7 * 2
sentences_count = 0

# 5. יצירת המשפטים וכתיבתם ישירות לקובץ
print(f"מתחיל ליצור ולשמור את המשפטים לקובץ: {file_name}...")

# פתיחת הקובץ לכתיבה ('w')
with open(file_name, 'w', encoding='utf-8') as f:
    for i, j_idx, b1, k, d, b2 in all_combinations:
        # A. פרמטרים בסיסיים
        sign_j = S[j_idx]
        ruler_planet = RULERS[sign_j]

        # B. חישוב המזל השני: S[j + (k - i) + d]
        j_prime_idx = (j_idx + (k - i) + d) % len(S)

        # ודא שהאינדקס חיובי
        if j_prime_idx < 0:
            j_prime_idx += len(S)

        sign_j_prime = S[j_prime_idx]

        # C. הרכבת המשפט
        sentence = (
            f"House {i} is in {sign_j} when its ruler - {ruler_planet} which {b1} retrogated - "
            f"is in house {k} and in sign {sign_j_prime} which {b2} intercepted"
        )

        # כתיבת המשפט לקובץ, בתוספת שבירת שורה
        f.write(sentence + '\n')
        sentences_count += 1

# 6. סיכום
print("---")
print(f"סיום. הקובץ '{file_name}' נוצר בהצלחה.")
print(f"סה\"כ משפטים שנכתבו לקובץ: {sentences_count}")

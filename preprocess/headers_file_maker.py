# python script to generate 2736 astrology combinations

# הגדרת הקבוצות
planets = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus",
    "Neptune", "Pluto", "North Node", "Lilith", "Chiron", "AC", "MC", "Fortune", "Vertex"
]

planets_transit = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus",
    "Neptune", "Pluto", "North Node", "Lilith", "Chiron"
]


houses = [
    "First house", "Second house", "Third house", "Fourth house", "Fifth house",
    "Sixth house", "Seventh house", "Eighth house", "Ninth house", "Tenth house",
    "Eleventh house", "Twelfth house"
]

signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ASPECTS_DICT = {
    0: 'Conjunction',  # היצמדות
    180: 'Opposition',  # ניגוד
    120: 'Trine',  # טרין
    90: 'Square',  # ריבוע
    60: 'Sextile',  # סקסטייל
    150: 'Inconjunct',  # קווינקונקס
    30: 'SemiSextile',  # סמי-סקסטייל
    45: 'SemiSquare',  # סמי-ריבוע
    135: 'Sesquiquadrate',  # סקווירפיינד
    72: 'Quintile',  # קווינטייל
    144: 'Biquintile'  # ביקווינטייל
}

retro = [
    " retrograde", ""
]

inter = [
    " intercepted", ""
]

# שם הקובץ שייווצר
file_name = "aspects_transit.txt"

# יצירת המכפלה הקרטזית ושמירה לרשימה
all_combinations = []
for planet1 in planets:
    for _, aspect in ASPECTS_DICT.items():
        for planet2 in planets_transit:
            combination = f"Natal {planet1} {aspect} Transit {planet2}"
            all_combinations.append(combination)

# כתיבת השילובים לקובץ טקסט
try:
    with open(file_name, 'w', encoding='utf-8') as f:
        # כותב כל שילוב לשורה חדשה
        for combination in all_combinations:
            f.write(combination + '\n')

    # הודעת הצלחה
    print(f"נוצרה רשימה נקייה של {len(all_combinations)} שילובים.")
    print(f"השילובים נשמרו בהצלחה לקובץ: {file_name}")

except Exception as e:
    # טיפול בשגיאות כתיבה לקובץ
    print(f"אירעה שגיאה בעת כתיבה לקובץ: {e}")

# לבדיקה (אופציונלי): הדפסת מספר השילובים הכולל
print(f"Total combinations generated: {len(all_combinations)}")
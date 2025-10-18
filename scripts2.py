# python script to generate 2736 astrology combinations

# הגדרת הקבוצות
planets = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus",
    "Neptun", "Pluto", "Ciron", "Lilith", "North Node", "Fortune", "Vertex",
    "AC", "DC", "IC", "MC"
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

retro = [
    " retrograde", ""
]

inter = [
    " intercepted", ""
]

# שם הקובץ שייווצר
file_name = "planet_house_sign_whole.txt"

# יצירת המכפלה הקרטזית ושמירה לרשימה
all_combinations = []
for planet in planets:
    for house in houses:
        for sign in signs:
            for r in retro:
                for i in inter:
                    # הפורמט הנדרש: 'כוכב in בית in מזל'
                    combination = f"{planet}{r} in {house} in {sign}{i}"
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
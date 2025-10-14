# src/birth_chart_analysis/CalculationEngine.py

import swisseph as swe
from datetime import datetime
import pytz
import math

# הגדרת שמות המזלות
ZODIAC_SIGNS = ['טלה', 'שור', 'תאומים', 'סרטן', 'אריה', 'בתולה',
                'מאזניים', 'עקרב', 'קשת', 'גדי', 'דלי', 'דגים']
# הגדרת שמות המזלות
ENG_ZODIAC_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# הגדרות היבטים - כל 11 ההיבטים העיקריים והמשניים
# זווית : שם ההיבט
ASPECTS_DICT = {
    0: 'Conjunction',      # היצמדות
    180: 'Opposition',     # ניגוד
    120: 'Trine',          # טרין
    90: 'Square',          # ריבוע
    60: 'Sextile',         # סקסטייל
    150: 'Inconjunct',       # קווינקונקס
    30: 'SemiSextile',    # סמי-סקסטייל
    45: 'SemiSquare',     # סמי-ריבוע
    135: 'Sesquiquadrate',  # סקווירפיינד
    72: 'Quintile',       # קווינטייל
    144: 'Biquintile'      # ביקווינטייל
}

# הגדרות סטיית אורב (פשוטות)
ORB = 6.0  # ניתן להשאיר על 8.0, או להחליט על אורבים שונים לאספקטים משניים



# ----------------------------------------------------
# פונקציות עזר קריטיות
# ----------------------------------------------------

def ensure_float(value) -> float:
    """
    ממיר כל ערך (כולל tuple/list) ל-float בטוח.
    """
    if isinstance(value, (list, tuple)):
        if len(value) > 0:
            return float(value[0])
        return 0.0
    return float(value)


def get_sign_and_house(degree: float, house_cusps: list) -> tuple[str, int]:
    """ מחזיר את המזל ואת הבית שבהם נמצאת מעלה נתונה (0-360) """

    # וידוא שהמעלה היא float תקין
    degree = ensure_float(degree)
    degree = degree % 360  # נרמול לטווח 0-360

    # חישוב מזל
    sign_index = int(degree // 30)
    sign = ZODIAC_SIGNS[sign_index]

    # חישוב בית (התבססות על house_cusps)
    house = 12
    for h in range(1, 13):
        # וידוא שכל הערכים הם float תקינים
        start_cusp = ensure_float(house_cusps[h])
        end_cusp = ensure_float(house_cusps[h % 12 + 1])

        # טיפול במעבר דרך 0 מעלות (טלה-דגים)
        if start_cusp <= end_cusp:
            if start_cusp <= degree < end_cusp:
                house = h
                break
        else:
            if start_cusp <= degree or degree < end_cusp:
                house = h
                break

    return sign, house


def calculate_aspects(planets_data: dict) -> list[dict]:
    """
    מחשב היבטים עיקריים בין כל זוג כוכבים.
    """
    aspects_list = []
    planet_names = list(planets_data.keys())

    # עדכון: שימוש ברשימה מלאה של גופים שחושבו בתוספת נקודות
    major_planets = list(planets_data.keys())

    for i in range(len(major_planets)):
        for j in range(i + 1, len(major_planets)):
            p1_name = major_planets[i]
            p2_name = major_planets[j]

            if p1_name not in planets_data or p2_name not in planets_data:
                continue

            lon1 = planets_data[p1_name]['lon_deg']
            lon2 = planets_data[p2_name]['lon_deg']

            # חישוב ההפרש הזוויתי (הקצר יותר)
            angle_diff = abs(lon1 - lon2)
            angle_diff = min(angle_diff, 360 - angle_diff)

            # מציאת ההיבט הקרוב ביותר (עם האורב הקטן ביותר)
            best_aspect = None
            best_orb = ORB + 1  # אתחול עם ערך גבוה מהאורב המקסימלי

            for angle, name in ASPECTS_DICT.items():
                current_orb = abs(angle_diff - angle)
                if current_orb <= ORB and current_orb < best_orb:
                    best_orb = current_orb
                    best_aspect = {
                        'planet1': p1_name,
                        'planet2': p2_name,
                        'aspect_name_heb': name,
                        'aspect_name_eng': name,
                        'angle_diff': angle_diff,
                        'orb': current_orb
                    }

            # אם נמצא היבט, הוסף אותו לרשימה
            if best_aspect:
                aspects_list.append(best_aspect)

    return aspects_list

def calculate_chart_positions(birth_datetime: datetime, lat: float, lon: float) -> dict:
    """
    מחשב את מפת הלידה המלאה באמצעות pyswisseph.
    """

    # --- הוסף את הקטע הזה ---
    # הגדרת נתיב לקבצי האפמריס (בהנחה שקבצים שמורים בתיקיית 'ephe' בתוך הנתונים של הפרויקט)
    import os
    MODULE_DIR = os.path.dirname(__file__)
    PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
    EPHE_DIR = os.path.join(PROJECT_DIR, 'data', 'ephe')

    # ודא שהנתיב קיים לפני שמנסים להגדיר אותו
    if os.path.exists(EPHE_DIR):
        swe.set_ephe_path(EPHE_DIR)
    # -----------------------

    # הגדרת אזור זמן ויום יוליאני
    local_tz = pytz.timezone('Asia/Jerusalem')
    local_dt = local_tz.localize(birth_datetime)
    utc_dt = local_dt.astimezone(pytz.utc)
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                    utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)

    # 1. חישוב מבנה הבתים (שיטת פלאצידוס)
    cusps_raw, ascmc = swe.houses(jd, lat, lon, b'P')

    # יצירת רשימה מנוקה של house cusps
    house_cusps_list = [0.0]  # אינדקס 0 לא בשימוש

    # המרה בטוחה של כל הערכים
    for i in range(12):
        cusp_value = ensure_float(cusps_raw[i])
        house_cusps_list.append(cusp_value)

    # 2. מיקומי כוכבים
    celestial_bodies = {
        'שמש': swe.SUN, 'ירח': swe.MOON, 'מרקורי': swe.MERCURY,
        'ונוס': swe.VENUS, 'מאדים': swe.MARS, 'צדק': swe.JUPITER,
        'שבתאי': swe.SATURN, 'אורנוס': swe.URANUS, 'נפטון': swe.NEPTUNE,
        'פלוטו': swe.PLUTO, 'ראש דרקון': swe.MEAN_NODE, 'לילית': swe.MEAN_APOG,
        'כירון': swe.CHIRON,
        # Vertex אינו גוף שמימי קלאסי ב-swisseph, נחשב אותו בנפרד אם צריך.
        # בינתיים נסתפק במה שניתן בקלות
    }

    chart_data = {
        'HouseCusps': house_cusps_list,
        'Planets': {},
        'Aspects': []  # נוסף שדה חדש להיבטים
    }

    # 3. לולאה על הכוכבים לחישוב מיקום
    for name, num in celestial_bodies.items():
        try:
            # קריאה ל-calc_ut - מחזיר (position_tuple, flags)
            calc_result = swe.calc_ut(jd, num)

            # בדיקה שהתוצאה היא tuple עם 2 איברים
            if not isinstance(calc_result, tuple) or len(calc_result) != 2:
                print(f"⚠️ אזהרה: תוצאה לא תקינה מ-calc_ut עבור {name}")
                continue

            # פירוק: position_data ו-flags (בסדר הזה!)
            position_data = calc_result[0]
            flags = calc_result[1]

            # וידוא ש-position_data הוא tuple/list עם לפחות 4 ערכים
            if not isinstance(position_data, (list, tuple)) or len(position_data) < 4:
                print(f"⚠️ אזהרה: position_data לא תקין עבור {name}")
                continue

            # פירוק הנתונים מתוך position_data
            lon = float(position_data[0])  # קו אורך אקליפטי
            lat_planet = float(position_data[1])  # קו רוחב אקליפטי
            distance = float(position_data[2])  # מרחק
            vel = float(position_data[3])  # מהירות בקו אורך

            # בדיקת נסיגה
            is_retrograde = vel < 0

            # חישוב מזל ובית
            sign, house = get_sign_and_house(lon, house_cusps_list)

            chart_data['Planets'][name] = {
                'lon_deg': lon,
                'sign': sign,
                'house': house,
                'is_retrograde': is_retrograde
            }

        except Exception as e:
            print(f"⚠️ שגיאה בחישוב {name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # הוספת AC (אופק) ו-MC (רום שמיים)
    # AC הוא קו יתד של בית 1 (אינדקס 1 ב-cusps_raw, ואינדקס 1 ב-house_cusps_list)
    # MC הוא קו יתד של בית 10 (אינדקס 10 ב-cusps_raw, ואינדקס 10 ב-house_cusps_list)

    # AC
    asc_lon = ensure_float(house_cusps_list[1])
    asc_sign, asc_house = get_sign_and_house(asc_lon, house_cusps_list)
    chart_data['Planets']['אופק (AC)'] = {
        'lon_deg': asc_lon,
        'sign': asc_sign,
        'house': 1,  # האופק תמיד בבית 1
        'is_retrograde': False
    }

    # MC
    mc_lon = ensure_float(house_cusps_list[10])
    mc_sign, mc_house = get_sign_and_house(mc_lon, house_cusps_list)
    chart_data['Planets']['רום שמיים (MC)'] = {
        'lon_deg': mc_lon,
        'sign': mc_sign,
        'house': 10,  # רום שמיים תמיד בבית 10
        'is_retrograde': False
    }

    # 4. חישוב היבטים (חדש)
    chart_data['Aspects'] = calculate_aspects(chart_data['Planets'])

    return chart_data

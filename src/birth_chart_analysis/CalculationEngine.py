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

# src/birth_chart_analysis/CalculationEngine.py
# ... (שאר תוכן הקובץ, כולל הייבואים והגדרות הקבועים) ...

# רשימת גופים פלנטריים שבהם נשתמש לחישוב טרנזיטים
# (בניגוד לנטאל, לא נחשב כאן ראשי בתים נוספים כמו MC/AC כי הם סטטיים למיקום הלידה)
# נכלול רק את 10 הגופים הראשיים + כירון, ראש דרקון.
PLANET_IDS_FOR_TRANSIT = {
    'שמש': swe.SUN, 'ירח': swe.MOON, 'מרקורי': swe.MERCURY, 'ונוס': swe.VENUS,
    'מאדים': swe.MARS, 'צדק': swe.JUPITER, 'שבתאי': swe.SATURN, 'אורנוס': swe.URANUS,
    'נפטון': swe.NEPTUNE, 'פלוטו': swe.PLUTO, 'ראש דרקון': swe.MEAN_NODE, 'כירון': swe.CHIRON
}

# הגדרות היבטים - כל 11 ההיבטים העיקריים והמשניים
# זווית : שם ההיבט
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

    # --- הגדרת נתיב לקבצי האפמריס ---
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
        'כירון': swe.CHIRON
        # נקודת מזל (Fortune) תחושב ידנית לאחר מכן.
    }

    chart_data = {
        'HouseCusps': house_cusps_list,
        'Planets': {},
        'Aspects': []
    }

    # רשימת גופים שהם נקודות (לא כוכבים), כדי לא לסמן אותם כנסיגה
    POINT_OBJECTS = [swe.MEAN_NODE, swe.TRUE_NODE, swe.MEAN_APOG, swe.OSCU_APOG]

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

            # ⚠️ נקודות (כמו ראש דרקון, לילית) אינן נחשבות כנסיגה קלאסית
            if num in POINT_OBJECTS:
                is_retrograde = False

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

    # 4. חישוב נקודת מזל (Part of Fortune - PoF) - חישוב ידני
    try:
        asc_lon = chart_data['Planets']['אופק (AC)']['lon_deg']
        moon_lon = chart_data['Planets']['ירח']['lon_deg']
        sun_lon = chart_data['Planets']['שמש']['lon_deg']
        sun_house = chart_data['Planets']['שמש']['house']  # השמש כבר חושבה

        # קביעת סוג המפה: מפת לילה (Sun בבתים 1-6) או מפת יום (Sun בבתים 7-12)
        # אם השמש בבתים 1-6 (מתחת לאופק) - זו מפת לילה
        is_night_chart = 1 <= sun_house <= 6

        if is_night_chart:
            # נוסחת לילה: AC + Sun - Moon
            pof_lon = (asc_lon + sun_lon - moon_lon) % 360.0
        else:
            # נוסחת יום: AC + Moon - Sun
            pof_lon = (asc_lon + moon_lon - sun_lon) % 360.0

        # חישוב מזל ובית
        pof_sign, pof_house = get_sign_and_house(pof_lon, house_cusps_list)

        chart_data['Planets']['פורטונה'] = {
            'lon_deg': pof_lon,
            'sign': pof_sign,
            'house': pof_house,
            'is_retrograde': False  # נקודה מחושבת תמיד מתקדמת
        }
    except KeyError as e:
        # טיפול במקרה שבו חישוב השמש, הירח או האופק נכשל
        print(f"⚠️ שגיאה בחישוב נקודת מזל: חסר הנתון הנדרש {e}. ייתכן וחישוב השמש, הירח או האופק נכשל.")
    except Exception as e:
        print(f"⚠️ שגיאה בלתי צפויה בחישוב נקודת מזל: {e}")

    # 5. חישוב ורטקס (Vertex - VX) - שימוש ב-ascmc
    try:
        # ורטקס נמצא בדרך כלל באינדקס 3 (האיבר הרביעי) במערך ascmc
        vertex_lon = ensure_float(ascmc[3])

        # חישוב מזל ובית
        vertex_sign, vertex_house = get_sign_and_house(vertex_lon, house_cusps_list)

        chart_data['Planets']['ורטקס'] = {  # ✅ שם קצר יותר כדי למנוע טעויות
            'lon_deg': vertex_lon,
            'sign': vertex_sign,
            'house': vertex_house,
            'is_retrograde': False
        }
    except IndexError:
        print("⚠️ אזהרה: לא ניתן היה לחשב ורטקס. מערך ascmc קצר מדי.")
    except Exception as e:
        # ❌ הסר את הקו הזה: print(f"⚠️ שגיאה בחישוב ורטקס (VX): {e}")
        print(f"⚠️ שגיאה בחישוב ורטקס: {e}")

    # 6. חישוב היבטים (התאמת מספר השלב)
    chart_data['Aspects'] = calculate_aspects(chart_data['Planets'])

    return chart_data


def calculate_current_positions(dt_object: datetime, lat: float, lon: float) -> dict:
    """
    מחשב את מיקומי הכוכבים והנקודות לזמן נתון (מעבר).
    """
    chart_data = {'Planets': {}}

    # המרת תאריך ושעה ליום יוליאני (JD) של זמן אוניברסלי (UT)
    jd_ut = swe.julday(dt_object.year, dt_object.month, dt_object.day,
                      dt_object.hour + dt_object.minute / 60.0 + dt_object.second / 3600.0)

    # הגדרת דגלים לחישובים (אורך אקליפטי, גאוצנטרי, אסטרולוגי)
    flags = swe.FLG_SWIEPH | swe.FLG_TOPOCTR | swe.FLG_EQUATORIAL

    # 1. הגדרת מיקום התצפית (המיקום הנוכחי)
    swe.set_topo(lon, lat, 0)  # longitude, latitude, altitude

    # 2. חישוב מיקומי הכוכבים
    for name_heb, planet_id in PLANET_IDS_FOR_TRANSIT.items():
        # xx הוא מערך של 6 ערכים, xx[0] הוא אורך פלנטרי
        xx, retflags = swe.calc_ut(jd_ut, planet_id, flags)

        lon_deg = ensure_float(xx[0])
        speed = ensure_float(xx[3])  # מהירות אורכית (degree/day)

        is_retrograde = speed < 0.0

        # חישוב מזל (הבתים לא רלוונטיים במפת מעבר)
        planet_sign, _ = get_sign_and_house(lon_deg, [0.0] * 13)  # מעבירים רשימה ריקה של בתים

        # ⚠️ נקודות (כמו ראש דרקון) אינן נחשבות כנסיגה קלאסית
        if planet_id in [swe.MEAN_NODE, swe.TRUE_NODE, swe.MEAN_APOG, swe.OSCU_APOG]:
            is_retrograde = False

        # שמירת הנתונים
        chart_data['Planets'][name_heb] = {
            'lon_deg': lon_deg,
            'sign': planet_sign,
            'house': None,  # נשאר None
            'is_retrograde': is_retrograde
        }

    return chart_data


def calculate_transit_aspects(natal_planets: dict, transit_planets: dict, orb: float) -> list:
    """
    מחשב את ההיבטים (Bi-wheel) בין כוכבי מפת הלידה לכוכבי המעבר.

    :param natal_planets: מיקומי כוכבי הלידה (מילון: שם: {lon_deg: X, ...}).
    :param transit_planets: מיקומי כוכבי המעבר (מילון: שם: {lon_deg: X, ...}).
    :param orb: האורב המקסימלי במעלות.
    :return: רשימה של מילונים המייצגים את ההיבטים.
    """
    aspects_list = []

    # 1. עוברים על כל כוכב נטאל
    for p1_name_heb, p1_data in natal_planets.items():
        if 'lon_deg' not in p1_data or p1_data['lon_deg'] is None:
            continue

        p1_lon = ensure_float(p1_data['lon_deg'])

        # 2. עוברים על כל כוכב טרנזיט
        for p2_name_heb, p2_data in transit_planets.items():
            if 'lon_deg' not in p2_data or p2_data['lon_deg'] is None:
                continue

            # היבטי טרנזיט נבדקים בין כל כוכב נטאל לכל כוכב טרנזיט (Bi-wheel)
            # לצורך הדיוק, אנו משווים גם כוכב נטאל לכוכב טרנזיט בעל אותו שם (לדוגמה: מאדים נטאל מול מאדים טרנזיט).

            p2_lon = ensure_float(p2_data['lon_deg'])

            # 1. חישוב המרחק הזוויתי הקצר ביותר
            separation = math.fabs(p1_lon - p2_lon)
            separation = min(separation, 360.0 - separation)

            # 2. בדיקה מול כל זוויות ההיבט
            for angle, aspect_name_eng in ASPECTS_DICT.items():
                difference = math.fabs(separation - angle)

                # אם ההפרש קטן מהאורב המקסימלי
                if difference <= orb:
                    aspects_list.append({
                        'planet1': p1_name_heb,
                        'planet2': p2_name_heb,
                        'p1_type': 'natal',  # הוספה לדיווח
                        'p2_type': 'transit',  # הוספה לדיווח
                        'aspect_name_heb': aspect_name_eng,  # שימוש ב-ENG כבסיס
                        'aspect_name_eng': aspect_name_eng,
                        'orb': difference
                    })

    aspects_list.sort(key=lambda x: x['orb'])
    return aspects_list
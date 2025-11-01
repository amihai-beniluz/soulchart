"""
CalculationEngine - מנוע חישוב אסטרולוגי (גרסה 3.4)
====================================================
🔧 FIX v3.4: תיקון קריטי - מניעת דיווח על היבטים שגויים
- הוספת בדיקת אורבים ב-find_closest_aspect_to_distance
- מניעת בחירת היבט מז'ורי (Square) כשהזווית היא מינורית (SemiSquare)
- הוספת actual_orb לכל exact date
"""

import pytz
import os
import swisseph as swe
from datetime import datetime, timedelta
import math

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
EPHE_DIR = os.path.join(PROJECT_DIR, 'data', 'ephe')

# הגדרת שמות המזלות
ZODIAC_SIGNS = ['טלה', 'שור', 'תאומים', 'סרטן', 'אריה', 'בתולה',
                'מאזניים', 'עקרב', 'קשת', 'גדי', 'דלי', 'דגים']
# הגדרת שמות המזלות
ENG_ZODIAC_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# רשימת גופים פלנטריים שבהם נשתמש לחישוב טרנזיטים
# (בניגוד לנטאל, לא נחשב כאן ראשי בתים נוספים כמו MC/AC כי הם סטטיים למיקום הלידה)
PLANET_IDS_FOR_TRANSIT = {
    'שמש': swe.SUN, 'ירח': swe.MOON, 'מרקורי': swe.MERCURY,
    'ונוס': swe.VENUS, 'מאדים': swe.MARS, 'צדק': swe.JUPITER,
    'שבתאי': swe.SATURN, 'אורנוס': swe.URANUS, 'נפטון': swe.NEPTUNE,
    'פלוטו': swe.PLUTO, 'ראש דרקון': swe.MEAN_NODE, 'לילית': swe.MEAN_APOG,
    'כירון': swe.CHIRON
}

# רשימת גופים שהם נקודות (לא כוכבים), כדי לא לסמן אותם כנסיגה
POINT_OBJECTS = [swe.MEAN_NODE, swe.TRUE_NODE, swe.MEAN_APOG, swe.OSCU_APOG]

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

# הגדרות אורבים ספציפיות לכל היבט
# אורבים מקובלים: מז'וריים (Conjunction, Opposition, Trine, Square, Sextile) עם אורב גבוה,
# ומינוריים (Inconjunct, SemiSextile, SemiSquare, Sesquiquadrate, Quintile, Biquintile) עם אורב נמוך יותר.
# הגדרות אורבים ספציפיות המבטאות העדפה לזוויות רחבות (אורב גבוה יותר)
ASPECT_ORBS = {
    # היבטים מז'וריים - חזקים:
    'Conjunction': 10.0,  # היצמדות
    'Opposition': 10.0,  # ניגוד
    'Square': 9.0,  # ריבוע
    'Trine': 8.0,  # טרין
    'Sextile': 6.0,  # סקסטייל

    # היבטים משניים - חלשים:
    'Inconjunct': 2.5,  # קווינקונקס
    'SemiSquare': 2.0,  # סמי-ריבוע
    'Sesquiquadrate': 2.0,  # סקווירפיינד
    'SemiSextile': 1.5,  # סמי-סקסטייל
    'Quintile': 1.0,  # קווינטייל
    'Biquintile': 1.0  # ביקווינטייל
}


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
    major_planets = list(planets_data.keys())

    for i in range(len(major_planets)):
        for j in range(i + 1, len(major_planets)):
            p1_name = major_planets[i]
            p2_name = major_planets[j]

            if p1_name not in planets_data or p2_name not in planets_data:
                continue

            lon1 = planets_data[p1_name]['lon_deg']
            lon2 = planets_data[p2_name]['lon_deg']
            angle_diff = abs(lon1 - lon2)
            angle_diff = min(angle_diff, 360 - angle_diff)

            best_aspect = None
            # אתחול עם אורב שחורג מהמקסימום בכל המקרים
            best_orb_value = max(ASPECT_ORBS.values()) + 1

            for angle, name in ASPECTS_DICT.items():
                # **שינוי מרכזי: קבלת האורב הספציפי**
                max_orb_for_aspect = ASPECT_ORBS.get(name, 0.5)  # השתמש ב-0.5 כברירת מחדל נמוכה לבטיחות

                current_orb = abs(angle_diff - angle)

                # בדיקה כפולה: 1. האם הוא בתוך האורב המקסימלי? 2. האם הוא קרוב יותר מההיבט שנמצא עד כה?
                if current_orb <= max_orb_for_aspect and current_orb < best_orb_value:
                    best_orb_value = current_orb
                    best_aspect = {
                        'planet1': p1_name,
                        'planet2': p2_name,
                        'aspect_name_heb': name,  # יש לשנות לשם עברי/אנגלי מתאים אם קיים
                        'aspect_name_eng': name,
                        'angle_diff': angle_diff,
                        'orb': current_orb
                    }

            if best_aspect:
                aspects_list.append(best_aspect)

    return aspects_list


def calculate_chart_positions(birth_datetime: datetime, lat: float, lon: float) -> dict:
    """
    מחשב את מפת הלידה המלאה באמצעות pyswisseph.
    """

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

    # 3. לולאה על הכוכבים לחישוב מיקום
    for name, num in celestial_bodies.items():
        try:
            # קריאה ל-calc_ut - מחזיר (position_tuple, flags)
            calc_result = swe.calc_ut(jd, num)

            # בדיקה שהתוצאה היא tuple עם 2 איברים
            if not isinstance(calc_result, tuple) or len(calc_result) != 2:
                print(f"⚠️ אזהרה: תוצאה לא תקינה מ-calc_ut עבור {name}")
                continue

            position_data = calc_result[0]

            # וידוא ש-position_data הוא tuple/list עם לפחות 4 ערכים
            if not isinstance(position_data, (list, tuple)) or len(position_data) < 4:
                print(f"⚠️ אזהרה: position_data לא תקין עבור {name}")
                continue

            # חילוץ בטוח של הערכים
            lon_deg = ensure_float(position_data[0])
            lat_deg = ensure_float(position_data[1])
            speed_deg = ensure_float(position_data[3])

            sign, house = get_sign_and_house(lon_deg, house_cusps_list)

            chart_data['Planets'][name] = {
                'lon_deg': lon_deg,
                'lat_deg': lat_deg,
                'sign': sign,
                'house': house,
                'speed_deg': speed_deg
            }

        except Exception as e:
            print(f"❌ שגיאה בחישוב {name}: {e}")
            continue

    # הוספת ראשי בתים בודדים
    ascmc_float = [ensure_float(val) for val in ascmc]

    asc_deg = ascmc_float[0]
    mc_deg = ascmc_float[1]

    asc_sign, asc_house = get_sign_and_house(asc_deg, house_cusps_list)
    mc_sign, mc_house = get_sign_and_house(mc_deg, house_cusps_list)

    chart_data['Planets']['AC'] = {'lon_deg': asc_deg, 'sign': asc_sign, 'house': asc_house}
    chart_data['Planets']['MC'] = {'lon_deg': mc_deg, 'sign': mc_sign, 'house': mc_house}

    # 4. חישוב נקודת מזל (Part of Fortune) ידנית
    sun_lon = chart_data['Planets']['שמש']['lon_deg']
    moon_lon = chart_data['Planets']['ירח']['lon_deg']
    asc_lon = asc_deg

    part_fortune = (asc_lon + moon_lon - sun_lon) % 360
    sign_fortune, house_fortune = get_sign_and_house(part_fortune, house_cusps_list)

    chart_data['Planets']['נקודת מזל'] = {
        'lon_deg': part_fortune,
        'sign': sign_fortune,
        'house': house_fortune
    }

    # 5. חישוב היבטים
    chart_data['Aspects'] = calculate_aspects(chart_data['Planets'])

    return chart_data


def calculate_current_positions(dt: datetime, lat: float, lon: float) -> dict:
    """
    מחשב את מיקומי הכוכבים במועד נתון (טרנזיטים).
    דומה ל-calculate_chart_positions אבל בלי היבטים ובתים (הם תלויים בנתוני לידה).
    """
    if os.path.exists(EPHE_DIR):
        swe.set_ephe_path(EPHE_DIR)

    local_tz = pytz.timezone('Asia/Jerusalem')
    local_dt = local_tz.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                    utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)

    # חישוב מבנה הבתים
    cusps_raw, ascmc = swe.houses(jd, lat, lon, b'P')
    house_cusps_list = [0.0]

    for i in range(12):
        house_cusps_list.append(ensure_float(cusps_raw[i]))

    # מיקומי כוכבים
    celestial_bodies = {
        'שמש': swe.SUN, 'ירח': swe.MOON, 'מרקורי': swe.MERCURY,
        'ונוס': swe.VENUS, 'מאדים': swe.MARS, 'צדק': swe.JUPITER,
        'שבתאי': swe.SATURN, 'אורנוס': swe.URANUS, 'נפטון': swe.NEPTUNE,
        'פלוטו': swe.PLUTO, 'ראש דרקון': swe.MEAN_NODE, 'לילית': swe.MEAN_APOG,
        'כירון': swe.CHIRON
    }

    positions = {}

    for name, num in celestial_bodies.items():
        try:
            calc_result = swe.calc_ut(jd, num)

            if not isinstance(calc_result, tuple) or len(calc_result) != 2:
                continue

            position_data = calc_result[0]

            if not isinstance(position_data, (list, tuple)) or len(position_data) < 4:
                continue

            lon_deg = ensure_float(position_data[0])
            lat_deg = ensure_float(position_data[1])
            speed_deg = ensure_float(position_data[3])

            sign, house = get_sign_and_house(lon_deg, house_cusps_list)

            positions[name] = {
                'lon_deg': lon_deg,
                'lat_deg': lat_deg,
                'sign': sign,
                'house': house,
                'speed_deg': speed_deg
            }

        except Exception:
            continue

    return {
        'Planets': positions,
        'HouseCusps': house_cusps_list
    }


def calculate_transit_aspects(natal_planets: dict, transit_planets: dict) -> list:
    """
    מחשב היבטים בין כוכבי לידה לכוכבי מעבר.
    """
    aspects = []

    for natal_name, natal_data in natal_planets.items():
        if natal_name in ['AC', 'MC', 'נקודת מזל']:
            continue

        natal_lon = natal_data['lon_deg']

        for transit_name, transit_data in transit_planets.items():
            transit_lon = transit_data['lon_deg']

            angle_diff = abs(transit_lon - natal_lon)
            angle_diff = min(angle_diff, 360 - angle_diff)

            for aspect_angle, aspect_name in ASPECTS_DICT.items():
                max_orb = ASPECT_ORBS.get(aspect_name, 1.0)
                orb = abs(angle_diff - aspect_angle)

                if orb <= max_orb:
                    aspects.append({
                        'planet1': natal_name,
                        'planet2': transit_name,
                        'aspect_name_eng': aspect_name,
                        'exact_angle': aspect_angle,
                        'orb': orb,
                        'max_orb': max_orb
                    })

    return aspects


PLANET_AVG_SPEEDS = {
    swe.SUN: 1.0,
    swe.MOON: 13.0,
    swe.MERCURY: 1.2,
    swe.VENUS: 1.0,
    swe.MARS: 0.5,
    swe.JUPITER: 0.08,
    swe.SATURN: 0.03,
    swe.URANUS: 0.01,
    swe.NEPTUNE: 0.006,
    swe.PLUTO: 0.004,
    swe.MEAN_NODE: 0.05,
    swe.CHIRON: 0.06,
    swe.MEAN_APOG: 0.11
}


def calculate_orb_at_date(natal_lon: float, transit_planet_id: int,
                          aspect_angle: float, date: datetime) -> float:
    """
    מחשב את האורב של היבט בתאריך ושעה מסוימים.
    """
    jd = swe.julday(date.year, date.month, date.day,
                    date.hour + date.minute / 60.0 + date.second / 3600.0)

    xx, _ = swe.calc_ut(jd, transit_planet_id)
    transit_lon = xx[0]

    diff = abs(transit_lon - natal_lon)
    diff = min(diff, 360 - diff)

    orb = abs(diff - aspect_angle)
    return orb


def check_retrograde_at_date(transit_planet_id: int, date: datetime) -> bool:
    """
    בודק האם כוכב נמצא ברטרוגרד בתאריך מסוים.
    """
    if transit_planet_id in POINT_OBJECTS:
        return False

    jd = swe.julday(date.year, date.month, date.day,
                    date.hour + date.minute / 60.0 + date.second / 3600.0)

    xx, _ = swe.calc_ut(jd, transit_planet_id)
    speed = xx[3]

    return speed < 0


def binary_search_boundary(natal_lon: float, transit_planet_id: int,
                           aspect_angle: float, max_orb: float,
                           start_date: datetime, end_date: datetime,
                           direction: str) -> datetime:
    """
    מוצא את הגבול המדויק בין בתוך-אורב ומחוץ-לאורב.
    """
    left = start_date
    right = end_date
    tolerance_seconds = 60

    while (right - left).total_seconds() > tolerance_seconds:
        mid = left + (right - left) / 2
        orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                    aspect_angle, mid)

        if direction == 'backward':
            if orb > max_orb:
                left = mid
            else:
                right = mid
        else:
            if orb <= max_orb:
                left = mid
            else:
                right = mid

    if direction == 'backward':
        return right
    else:
        return left


# 🔧 FIX v3.4: תיקון הבעיה העיקרית - וידוא שה-Exact שנמצא מתאים להיבט המבוקש

def find_exact_date_absolute(natal_lon: float, transit_planet_id: int,
                             aspect_angle: float, reference_date: datetime,
                             avg_speed: float, max_orb: float) -> datetime:
    """
    מוצא את המועד המדויק של היבט באמצעות חיפוש בינארי.

    🔧 FIX v3.4: מוודא שהתאריך שנמצא אכן מתאים להיבט המבוקש,
    ולא להיבט אחר שקרוב יותר.

    CRITICAL: מחזיר None אם מצא Exact של היבט שגוי!
    """
    # חישוב טווח חיפוש
    base_days = int(max_orb / avg_speed) if avg_speed > 0 else 30

    if avg_speed > 1.0:
        max_days = max(7, min(base_days * 3, 30))
    elif avg_speed > 0.1:
        max_days = max(15, min(base_days * 2, 60))
    else:
        max_days = max(30, min(base_days, 120))

    start = reference_date - timedelta(days=max_days)
    end = reference_date + timedelta(days=max_days)

    tolerance_seconds = 60
    left = start
    right = end

    # חיפוש בינארי למציאת המינימום
    while (right - left).total_seconds() > tolerance_seconds:
        mid = left + (right - left) / 2
        mid_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                        aspect_angle, mid)

        left_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                         aspect_angle, left)
        right_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                          aspect_angle, right)

        if left_orb <= mid_orb and left_orb <= right_orb:
            right = mid
        elif right_orb <= mid_orb and right_orb <= left_orb:
            left = mid
        elif mid_orb <= left_orb and mid_orb <= right_orb:
            if abs((left - mid).total_seconds()) < abs((right - mid).total_seconds()):
                right = mid
            else:
                left = mid
        else:
            left = mid

    best_date = left
    best_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                     aspect_angle, left)

    for test_date in [left, mid, right]:
        test_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                         aspect_angle, test_date)
        if test_orb < best_orb:
            best_orb = test_orb
            best_date = test_date

    # בדיקה סופית - האם באמת מצאנו exact סביר?
    orb_threshold = max(max_orb * 1.2, max_orb + 0.5)

    if best_orb > orb_threshold:
        return None

    # 🔧 FIX v3.4: CRITICAL - וידוא שההיבט שמצאנו הוא אכן ההיבט המבוקש!
    # חישוב המרחק הזוויתי בפועל בתאריך שמצאנו
    jd = swe.julday(best_date.year, best_date.month, best_date.day,
                    best_date.hour + best_date.minute / 60.0 + best_date.second / 3600.0)
    xx, _ = swe.calc_ut(jd, transit_planet_id)
    transit_lon = xx[0]

    # חשב מרחק זוויתי
    diff = abs(transit_lon - natal_lon)
    diff = min(diff, 360 - diff)

    # מצא את ההיבט הקרוב ביותר למרחק זה
    closest_angle, closest_aspect_name, distance_from_closest = find_closest_aspect_to_distance(diff)

    # 🎯 CRITICAL CHECK: האם ההיבט הקרוב ביותר הוא אכן ההיבט שחיפשנו?
    if closest_angle != aspect_angle:
        # מצאנו exact של היבט אחר! זה לא ההיבט שחיפשנו
        return None

    # 🔧 FIX v3.4: בדיקה נוספת - האם האורב קטן מהסף המקסימלי?
    # (למרות שכבר בדקנו, נוודא שההיבט המזוהה בטווח הסביר)
    if best_orb > max_orb * 0.8:  # 80% מהאורב המקסימלי
        # האורב גדול מדי - זה לא exact טוב
        return None

    return best_date


def find_closest_aspect_to_distance(angular_distance: float) -> tuple:
    """
    מוצא את ההיבט הקרוב ביותר למרחק זוויתי נתון.
    🔧 FIX: מתחשב באורבים - בוחר רק היבטים שבטווח!

    :param angular_distance: מרחק זוויתי (0-180 מעלות)
    :return: (aspect_angle, aspect_name, distance_from_exact)
    """
    closest_aspect = None
    closest_angle = None
    min_distance = float('inf')

    for aspect_angle_iter, aspect_name in ASPECTS_DICT.items():
        # 🔧 FIX: קבל את האורב המקסימלי להיבט הזה
        max_orb = ASPECT_ORBS.get(aspect_name, 0.5)

        distance = abs(angular_distance - aspect_angle_iter)

        # 🎯 CRITICAL: בחר את ההיבט רק אם הוא בטווח האורב!
        # זה מונע בחירת Square כשהזווית האמיתית היא SemiSquare
        if distance <= max_orb and distance < min_distance:
            min_distance = distance
            closest_aspect = aspect_name
            closest_angle = aspect_angle_iter

    return (closest_angle, closest_aspect, min_distance)


def find_all_exact_dates(natal_lon: float, transit_planet_id: int,
                         aspect_angle: float, start_date: datetime,
                         end_date: datetime, retrograde_turns: list,
                         max_orb: float) -> list:
    """
    מוצא את כל נקודות ה-Exact במחזור (יכול להיות 1-3).
    🔧 FIX: שיפור זיהוי duplicates עם סף דינמי
    """
    exact_dates = []
    avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))

    # 🔧 FIX: חישוב סף דינמי למניעת duplicates
    # פלנטות מהירות: סף קצר יותר, פלנטות איטיות: סף ארוך יותר
    if avg_speed > 5:  # ירח
        duplicate_threshold_hours = 2
    elif avg_speed > 0.5:  # שמש, מרקורי, ונוס, מאדים
        duplicate_threshold_hours = 6
    elif avg_speed > 0.05:  # צדק
        duplicate_threshold_hours = 24
    else:  # פלנטות איטיות
        duplicate_threshold_hours = 48

    if not retrograde_turns:
        # אין נסיגות - Exact אחד פשוט
        # 🔧 FIX: במקום reference_date באמצע, נחפש בכל הטווח
        # נעשה סריקה לאיתור המינימום האמיתי

        min_orb = float('inf')
        best_date = None

        # סריקה ראשונית למציאת האזור עם המינימום
        scan_points = 20  # נבדוק 20 נקודות לאורך הטווח
        for i in range(scan_points + 1):
            test_date = start_date + (end_date - start_date) * (i / scan_points)
            orb = calculate_orb_at_date(natal_lon, transit_planet_id, aspect_angle, test_date)
            if orb < min_orb:
                min_orb = orb
                best_date = test_date

        # עכשיו דייק את המינימום עם find_exact_date_absolute
        if best_date:
            exact_date = find_exact_date_absolute(natal_lon, transit_planet_id, aspect_angle,
                                                  best_date, avg_speed, max_orb)
        else:
            exact_date = None

        if exact_date is not None:
            is_retro = check_retrograde_at_date(transit_planet_id, exact_date)
            # חישוב האורב בפועל בנקודת השיא
            actual_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                               aspect_angle, exact_date)
            exact_dates.append({
                'date': exact_date,
                'is_retrograde': is_retro,
                'actual_orb': round(actual_orb, 4)  # האורב בפועל במעלות
            })
    else:
        # יש נסיגות - חלק לסגמנטים
        segment_boundaries = [start_date] + [t['date'] for t in retrograde_turns] + [end_date]

        for i in range(len(segment_boundaries) - 1):
            seg_start = segment_boundaries[i]
            seg_end = segment_boundaries[i + 1]

            # בדיקה: הסגמנט צריך להיות לפחות יום אחד
            if (seg_end - seg_start).total_seconds() < 3600 * 24:
                continue

            try:
                # 🔧 FIX: סריקה ראשונית למציאת המינימום בסגמנט
                min_orb = float('inf')
                best_date = None

                scan_points = 10  # נבדוק 10 נקודות בכל סגמנט
                for j in range(scan_points + 1):
                    test_date = seg_start + (seg_end - seg_start) * (j / scan_points)
                    orb = calculate_orb_at_date(natal_lon, transit_planet_id, aspect_angle, test_date)
                    if orb < min_orb:
                        min_orb = orb
                        best_date = test_date

                # אם המינימום שנמצא גדול מדי, דלג על הסגמנט
                if min_orb > max_orb:
                    continue

                # דייק את המינימום עם find_exact_date_absolute
                if best_date:
                    exact_date = find_exact_date_absolute(natal_lon, transit_planet_id, aspect_angle,
                                                          best_date, avg_speed, max_orb)
                else:
                    exact_date = None

                if exact_date is None:
                    continue

                # וודא שה-Exact באמת בתוך האורב המקסימלי
                exact_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                                  aspect_angle, exact_date)

                if exact_orb > max_orb * 0.8:
                    continue

                is_retro = check_retrograde_at_date(transit_planet_id, exact_date)

                # חישוב האורב בפועל בנקודת השיא
                actual_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                                   aspect_angle, exact_date)

                # 🔧 FIX: בדיקת duplicates משופרת עם סף דינמי
                is_duplicate = False
                for existing_exact in exact_dates:
                    time_diff_hours = abs((existing_exact['date'] - exact_date).total_seconds()) / 3600
                    if time_diff_hours < duplicate_threshold_hours:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    exact_dates.append({
                        'date': exact_date,
                        'is_retrograde': is_retro,
                        'actual_orb': round(actual_orb, 4)  # האורב בפועל במעלות
                    })
            except Exception as e:
                continue

    # 🔧 FIX: הגבלת מספר exact dates ל-3 מקסימום
    # אם יש יותר מ-3, קח את 3 הקרובים ביותר למרכז הטווח
    if len(exact_dates) > 3:
        reference_date = start_date + (end_date - start_date) / 2
        exact_dates = sorted(exact_dates,
                             key=lambda x: abs((x['date'] - reference_date).total_seconds()))[:3]

    return exact_dates


def get_retrograde_info(transit_planet_id: int, current_date: datetime) -> dict:
    """
    מחזיר מידע מלא על מצב הנסיגה של כוכב.
    is_retrograde_now - האם בנסיגה עכשיו?
    next_station - תאריך שינוי כיוון הבא
    station_type - הכיוון הבא - האם יסוג או ימשיך ישר?
    has_retrograde_in_range - האם יש נסיגה ב400 ימים הקרובים?
    """

    # 🌟 בדיקה 1: כוכבים שלעולם לא נסוגים
    if transit_planet_id in [swe.SUN, swe.MOON]:
        return {
            'is_retrograde_now': False,
            'next_station': None,
            'station_type': None,
            'has_retrograde_in_range': False
        }

    # 🌑 בדיקה 2: נקודות שתמיד נסוגים (בממוצע)
    # MEAN_NODE ו-MEAN_APOG הם נקודות מתמטיות שנעות לאחור באופן ממוצע
    if transit_planet_id in [swe.MEAN_NODE, swe.MEAN_APOG]:
        return {
            'is_retrograde_now': True,
            'next_station': None,  # אין תחנות רטרוגרד אמיתיות
            'station_type': None,
            'has_retrograde_in_range': True
        }

    # 🪐 כוכבים רגילים - בצע את החישוב המלא
    is_retro_now = check_retrograde_at_date(transit_planet_id, current_date)

    next_station = None
    station_type = None

    # חפש תחנה הבאה בטווח של שנה
    prev_is_retro = is_retro_now
    for days_ahead in range(1, 400):
        test_date = current_date + timedelta(days=days_ahead)
        is_retro = check_retrograde_at_date(transit_planet_id, test_date)

        if is_retro != prev_is_retro:
            next_station = test_date
            station_type = 'retrograde' if is_retro else 'direct'
            break

        prev_is_retro = is_retro

    has_retrograde_in_range = (is_retro_now or next_station is not None)

    return {
        'is_retrograde_now': is_retro_now,
        'next_station': next_station,
        'station_type': station_type,
        'has_retrograde_in_range': has_retrograde_in_range
    }


def calculate_aspect_lifecycle(natal_lon: float, transit_planet_id: int,
                               aspect_angle: float, max_orb: float,
                               current_date: datetime) -> dict:
    """
    מחשב את מחזור החיים המלא של היבט (כולל נסיגות).
    """

    # 1. קבל מידע על נסיגות
    retro_info = get_retrograde_info(transit_planet_id, current_date)

    # 2. קבע טווח סריקה
    # TODO check if it's good enough estimation.
    avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))
    estimated_days = (max_orb * 2) / avg_speed if avg_speed > 0 else 90

    # קביעת רזולוציית חיפוש
    if estimated_days < 1:
        search_increment = timedelta(hours=1)
        search_range = int(estimated_days * 24 * 3)
    elif estimated_days < 7:
        search_increment = timedelta(hours=6)
        search_range = int(estimated_days * 4 * 3)
    elif estimated_days < 30:
        search_increment = timedelta(days=1)
        search_range = int(estimated_days * 3)
    else:
        search_increment = timedelta(days=7)
        search_range = int((estimated_days / 7) * 3)

    search_range = max(2, min(1000, search_range))

    if retro_info['has_retrograde_in_range']:
        search_range *= 3

    # ✅ שלב 1: מצא את ה-Exact תחילה
    exact_date = find_exact_date_absolute(
        natal_lon, transit_planet_id, aspect_angle,
        current_date, avg_speed, max_orb
    )

    # 🔧 FIX v3.3: אם לא נמצא exact date תקין - ההיבט לא קיים!
    # (התיקון בfind_exact_date_absolute דוחה היבטים שגויים)
    if exact_date is None:
        return None

    # ✅ שלב 2: חפש את cycle_start - אחורה מה-Exact
    cycle_start = None
    found_start = False

    test_time = exact_date
    for i in range(search_range):
        test_time = test_time - search_increment
        test_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                         aspect_angle, test_time)

        if test_orb > max_orb:
            # מצאנו נקודה מחוץ לאורב - דייק עם binary search
            cycle_start = binary_search_boundary(
                natal_lon, transit_planet_id, aspect_angle, max_orb,
                test_time, test_time + search_increment, 'backward'
            )
            found_start = True
            break

    if not found_start:
        cycle_start = exact_date - (search_increment * search_range)

    # ✅ שלב 3: חפש את cycle_end - קדימה מה-Exact
    cycle_end = None
    found_end = False

    test_time = exact_date
    for i in range(search_range):
        test_time = test_time + search_increment
        test_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                         aspect_angle, test_time)

        if test_orb > max_orb:
            # מצאנו נקודה מחוץ לאורב - דייק עם binary search
            cycle_end = binary_search_boundary(
                natal_lon, transit_planet_id, aspect_angle, max_orb,
                test_time - search_increment, test_time, 'forward'
            )
            found_end = True
            break

    if not found_end:
        cycle_end = exact_date + (search_increment * search_range)

    # 4. חפש נסיגות בטווח
    retrograde_turns = find_retrograde_turns_optimized(
        transit_planet_id, cycle_start, cycle_end
    )
    has_retrograde = len(retrograde_turns) > 0

    # 5. מצא את כל נקודות ה-Exact (עכשיו עם נסיגות)
    exact_dates = find_all_exact_dates(
        natal_lon, transit_planet_id, aspect_angle,
        cycle_start, cycle_end, retrograde_turns,
        max_orb
    )

    # 6. חשב נתונים
    total_days = (cycle_end - cycle_start).days
    num_passes = len(exact_dates)

    return {
        'start': cycle_start,
        'end': cycle_end,
        'exact_dates': exact_dates,
        'total_days': total_days,
        'has_retrograde': has_retrograde,
        'num_passes': num_passes,
        'retrograde_info': retro_info
    }


def get_planet_speed_at_date(transit_planet_id: int, date: datetime) -> float:
    """מחזיר את המהירות האורכית של כוכב בתאריך מסוים."""
    jd = swe.julday(date.year, date.month, date.day,
                    date.hour + date.minute / 60.0 + date.second / 3600.0)
    xx, _ = swe.calc_ut(jd, transit_planet_id)
    return xx[3]


def find_station_date_precise(transit_planet_id: int,
                              start_date: datetime,
                              end_date: datetime,
                              tolerance_hours: float = 0.1) -> datetime:
    """מוצא את הרגע המדויק של תחנה באמצעות Binary Search על המהירות."""
    left = start_date
    right = end_date

    left_speed = get_planet_speed_at_date(transit_planet_id, left)
    right_speed = get_planet_speed_at_date(transit_planet_id, right)

    if (left_speed * right_speed) > 0:
        return left if abs(left_speed) < abs(right_speed) else right

    while (right - left).total_seconds() / 3600 > tolerance_hours:
        mid = left + (right - left) / 2
        mid_speed = get_planet_speed_at_date(transit_planet_id, mid)

        if (left_speed * mid_speed) < 0:
            right = mid
            right_speed = mid_speed
        else:
            left = mid
            left_speed = mid_speed

    return left + (right - left) / 2


def find_retrograde_turns_optimized(transit_planet_id: int,
                                    start_date: datetime,
                                    end_date: datetime) -> list:
    """גרסה משופרת - מוצאת תחנות רטרוגרד עם דיוק של 6 דקות."""
    if transit_planet_id in POINT_OBJECTS:
        return []

    # 🔧 FIX: סף סריקה דינמי לפי מהירות הפלנטה
    avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))

    if avg_speed > 0.5:  # פלנטות מהירות
        scan_interval = timedelta(days=2)
    elif avg_speed > 0.05:  # צדק
        scan_interval = timedelta(days=5)
    else:  # פלנטות איטיות
        scan_interval = timedelta(days=10)

    turns = []
    current = start_date

    prev_speed = get_planet_speed_at_date(transit_planet_id, current)
    prev_date = current
    current += scan_interval

    while current <= end_date:
        current_speed = get_planet_speed_at_date(transit_planet_id, current)

        if (prev_speed * current_speed) < 0:
            precise_station_date = find_station_date_precise(
                transit_planet_id, prev_date, current, tolerance_hours=0.1
            )

            speed_after = get_planet_speed_at_date(
                transit_planet_id,
                precise_station_date + timedelta(hours=1)
            )

            to_retrograde = speed_after < 0

            is_duplicate = False
            for existing_turn in turns:
                time_diff_hours = abs((existing_turn['date'] - precise_station_date).total_seconds() / 3600)
                if time_diff_hours < 24:
                    is_duplicate = True
                    break

            if not is_duplicate:
                turns.append({
                    'date': precise_station_date,
                    'to_retrograde': to_retrograde
                })

        prev_speed = current_speed
        prev_date = current
        current += scan_interval

    return turns


def is_aspect_physically_possible(transit_planet_id: int, aspect_angle: float,
                                  start_date: datetime, end_date: datetime,
                                  current_distance: float = None) -> bool:
    """
    🔧 FIX: בודק אם היבט פיזית אפשרי בטווח זמן נתון

    :param transit_planet_id: מזהה הפלנטה הטרנזיטית
    :param aspect_angle: זווית ההיבט
    :param start_date: תאריך התחלה
    :param end_date: תאריך סיום
    :param current_distance: מרחק נוכחי בין הפלנטות (אופציונלי)
    :return: True אם ההיבט אפשרי, False אחרת
    """
    avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))
    days = (end_date - start_date).days
    max_movement = avg_speed * days * 1.5  # מרווח בטחון של 50%

    # אם הפלנטה לא יכולה לעבור את הזווית הנדרשת - לא אפשרי
    if max_movement < aspect_angle * 0.15:  # לא יגיע גם ל-15% מהזווית
        return False

    # אם יש מידע על המרחק הנוכחי, השתמש בו לסינון מדויק יותר
    if current_distance is not None:
        # בדוק אם המרחק הנוכחי + התנועה המקסימלית יכולים להגיע לזווית
        min_distance_to_aspect = abs(current_distance - aspect_angle)
        if min_distance_to_aspect > max_movement:
            return False

    return True


def find_next_aspect_cycle(natal_lon: float, transit_planet_id: int,
                           aspect_angle: float, max_orb: float,
                           from_date: datetime, to_date: datetime) -> dict:
    """
    מוצא את מחזור החיים הבא של היבט בטווח זמן.
    שונה מ-calculate_aspect_lifecycle - מחפש קדימה בלבד, לא סביב תאריך.
    🔧 FIX: הוספת בדיקת אפשרות פיזית והגבלת exact dates

    :param natal_lon: קו אורך נטאלי (0-360)
    :param transit_planet_id: מזהה כוכב טרנזיט
    :param aspect_angle: זווית ההיבט (0, 60, 90, 120, 180...)
    :param max_orb: אורב מקסימלי
    :param from_date: חפש החל מתאריך זה
    :param to_date: חפש עד תאריך זה
    :return: dict עם start, end, exact_dates או None אם לא נמצא
    """

    # 🔧 FIX: בדיקה מקדימה - האם ההיבט פיזית אפשרי?
    if not is_aspect_physically_possible(transit_planet_id, aspect_angle,
                                         from_date, to_date):
        return None

    # קבע צעד סריקה לפי מהירות הפלנטה
    avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))

    if avg_speed > 5:  # ירח
        scan_step = timedelta(hours=2)
    elif avg_speed > 0.5:  # שמש, מרקורי, ונוס, מאדים
        scan_step = timedelta(hours=12)
    elif avg_speed > 0.05:  # צדק
        scan_step = timedelta(days=2)
    else:  # שבתאי, אורנוס, נפטון, פלוטו
        scan_step = timedelta(days=5)

    # ========================================
    # שלב 1: מצא כניסה לטווח (cycle_start)
    # ========================================
    current = from_date
    cycle_start = None
    prev_orb = None

    while current <= to_date:
        orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                    aspect_angle, current)

        # האם נכנסנו לטווח?
        if orb <= max_orb:
            # מצאנו כניסה! עכשיו דייק את המועד
            if prev_orb is not None and prev_orb > max_orb:
                # חצינו את הגבול - השתמש ב-binary search
                cycle_start = binary_search_boundary(
                    natal_lon, transit_planet_id, aspect_angle, max_orb,
                    current - scan_step, current, 'backward'
                )
            else:
                # כבר בתוך הטווח מההתחלה
                cycle_start = current
            break

        prev_orb = orb
        current += scan_step

    # לא נמצאה כניסה בטווח
    if cycle_start is None:
        return None

    # ========================================
    # שלב 2: חפש תחנות רטרוגרד בטווח צפוי
    # ========================================
    estimated_duration_days = (max_orb * 2) / avg_speed if avg_speed > 0 else 90
    estimated_end = cycle_start + timedelta(days=estimated_duration_days * 3)
    estimated_end = min(estimated_end, to_date + timedelta(days=30))

    retrograde_turns = []
    if transit_planet_id not in POINT_OBJECTS:
        # חפש תחנות מ-cycle_start עד הסוף המוערך
        retrograde_turns = find_retrograde_turns_optimized(
            transit_planet_id,
            cycle_start,
            estimated_end
        )

    # ========================================
    # שלב 3: מצא יציאה מהטווח (cycle_end)
    # ========================================
    current = cycle_start + scan_step
    cycle_end = None
    prev_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                     aspect_angle, cycle_start)

    max_search = min(to_date, cycle_start + timedelta(days=estimated_duration_days * 4))

    while current <= max_search:
        orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                    aspect_angle, current)

        # האם יצאנו מהטווח?
        if orb > max_orb and prev_orb <= max_orb:
            # חצינו את הגבול החוצה - דייק
            cycle_end = binary_search_boundary(
                natal_lon, transit_planet_id, aspect_angle, max_orb,
                current - scan_step, current, 'forward'
            )
            break

        prev_orb = orb
        current += scan_step

    # אם לא מצאנו יציאה - הסתיים הטווח שלנו
    if cycle_end is None:
        cycle_end = max_search

    # ========================================
    # שלב 4: מצא את כל נקודות ה-Exact
    # ========================================
    exact_dates = []

    # 🔧 FIX: סף דינמי למניעת duplicates
    if avg_speed > 5:  # ירח
        duplicate_threshold_hours = 2
    elif avg_speed > 0.5:  # שמש, מרקורי, ונוס, מאדים
        duplicate_threshold_hours = 6
    elif avg_speed > 0.05:  # צדק
        duplicate_threshold_hours = 24
    else:  # פלנטות איטיות
        duplicate_threshold_hours = 48

    if not retrograde_turns:
        # אין רטרוגרד - Exact אחד פשוט
        exact = find_exact_date_absolute(
            natal_lon, transit_planet_id, aspect_angle,
            cycle_start + (cycle_end - cycle_start) / 2,
            avg_speed, max_orb
        )

        if exact:
            is_retro = get_planet_speed_at_date(transit_planet_id, exact) < 0
            actual_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                               aspect_angle, exact)
            exact_dates.append({
                'date': exact,
                'is_retrograde': is_retro,
                'actual_orb': round(actual_orb, 4)
            })
    else:
        # יש רטרוגרד - חלק לסגמנטים
        boundaries = [cycle_start] + [t['date'] for t in retrograde_turns] + [cycle_end]

        for i in range(len(boundaries) - 1):
            seg_start = boundaries[i]
            seg_end = boundaries[i + 1]

            # דלג על סגמנטים קצרים מדי
            if (seg_end - seg_start).total_seconds() < 3600 * 12:
                continue

            # חפש Exact בסגמנט
            exact = find_exact_date_absolute(
                natal_lon, transit_planet_id, aspect_angle,
                seg_start + (seg_end - seg_start) / 2,
                avg_speed, max_orb
            )

            if exact:
                # וודא שבאמת בתוך האורב
                exact_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                                  aspect_angle, exact)

                if exact_orb <= max_orb * 0.8:  # 80% מהאורב המקסימלי
                    is_retro = get_planet_speed_at_date(transit_planet_id, exact) < 0

                    # 🔧 FIX: בדוק כפילויות עם סף דינמי
                    is_duplicate = False
                    for ex in exact_dates:
                        time_diff_hours = abs((ex['date'] - exact).total_seconds()) / 3600
                        if time_diff_hours < duplicate_threshold_hours:
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        exact_dates.append({
                            'date': exact,
                            'is_retrograde': is_retro,
                            'actual_orb': round(exact_orb, 4)  # כבר חישבנו את exact_orb למעלה
                        })

    # 🔧 FIX: הגבלת מספר exact dates ל-3 מקסימום
    if len(exact_dates) > 3:
        reference_date = cycle_start + (cycle_end - cycle_start) / 2
        exact_dates = sorted(exact_dates,
                             key=lambda x: abs((x['date'] - reference_date).total_seconds()))[:3]

    # ========================================
    # שלב 5: החזר תוצאות
    # ========================================
    return {
        'start': cycle_start,
        'end': cycle_end,
        'exact_dates': exact_dates,
        'num_passes': len(exact_dates),
        'has_retrograde': len(retrograde_turns) > 0,
        'total_days': (cycle_end - cycle_start).days
    }
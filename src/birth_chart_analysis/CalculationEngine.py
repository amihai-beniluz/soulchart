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

            # פירוק הנתונים מתוך position_data
            lon = float(position_data[0])  # קו אורך אקליפטי
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

    jd_ut = swe.julday(dt_object.year, dt_object.month, dt_object.day,
                       dt_object.hour + dt_object.minute / 60.0 + dt_object.second / 3600.0)

    # ✅ דגלים נכונים - כמו במפת הלידה
    # אם לא מציינים דגלים, swisseph משתמש בברירת המחדל שכוללת SPEED
    # אבל בואו נהיה מפורשים:

    for name_heb, planet_id in PLANET_IDS_FOR_TRANSIT.items():
        # ✅ ללא flags מיוחדים - ברירת המחדל של swe.calc_ut כוללת מהירות
        calc_result = swe.calc_ut(jd_ut, planet_id)

        if not isinstance(calc_result, tuple) or len(calc_result) != 2:
            print(f"⚠️ אזהרה: תוצאה לא תקינה עבור {name_heb}")
            continue

        position_data = calc_result[0]

        if not isinstance(position_data, (list, tuple)) or len(position_data) < 4:
            print(f"⚠️ אזהרה: position_data לא תקין עבור {name_heb}")
            continue

        lon_deg = float(position_data[0])
        vel = float(position_data[3])

        is_retrograde = vel < 0

        if planet_id in POINT_OBJECTS:
            is_retrograde = False

        planet_sign, _ = get_sign_and_house(lon_deg, [0.0] * 13)

        chart_data['Planets'][name_heb] = {
            'lon_deg': lon_deg,
            'sign': planet_sign,
            'house': None,
            'is_retrograde': is_retrograde,
            'speed': vel,
            'lon_speed_deg_per_day': vel
        }

    return chart_data

def calculate_transit_aspects(natal_planets: dict, transit_planets: dict) -> list[dict]:
    """
    מחשב את ההיבטים (Bi-wheel) בין כוכבי מפת הלידה לכוכבי המעבר.

    :param natal_planets: מיקומי כוכבי הלידה (מילון: שם: {lon_deg: X, ...}).
    :param transit_planets: מיקומי כוכבי המעבר (מילון: שם: {lon_deg: X, ...}).
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

            p2_lon = ensure_float(p2_data['lon_deg'])

            # 3. חישוב המרחק הזוויתי הקצר ביותר
            separation = math.fabs(p1_lon - p2_lon)
            separation = min(separation, 360.0 - separation)

            # 4. בדיקה מול כל זוויות ההיבט
            for angle, aspect_name_eng in ASPECTS_DICT.items():
                difference = math.fabs(separation - angle)  # האורב הנוכחי
                orb_max = ASPECT_ORBS.get(aspect_name_eng, 0.5)

                if difference <= orb_max:
                    # חישוב האם ההיבט מתקרב או מתרחק
                    p2_speed = p2_data.get('lon_speed_deg_per_day', p2_data.get('speed', 0.0))

                    # לוגיקה פשוטה: אם האורב גדול ממחצית האורב המקסימלי = מתקרב
                    # אם האורב קטן ממחצית האורב המקסימלי = מתרחק (עבר את ה-Exact)
                    if difference > (orb_max / 2):
                        is_approaching = True  # עדיין רחוק, מתקרב ל-Exact
                    else:
                        is_approaching = False  # קרוב מדי, כנראה עבר את ה-Exact ומתרחק

                    # הוספת האספקט לרשימה
                    aspects_list.append({
                        'planet1': p1_name_heb,
                        'planet2': p2_name_heb,
                        'p1_type': 'natal',
                        'p2_type': 'transit',
                        'aspect_name_eng': aspect_name_eng,
                        'angle_diff': separation,
                        'exact_angle': angle,
                        'orb': difference,
                        'max_orb': orb_max,
                        'p2_is_retrograde': p2_data.get('is_retrograde', False),
                        'p2_speed': p2_data.get('lon_speed_deg_per_day', 0.0),
                        'is_approaching': is_approaching
                    })

    return aspects_list


# מהירויות ממוצעות של כוכבים (מעלות ליום)
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
    transit_lon = ensure_float(xx[0])

    separation = abs(natal_lon - transit_lon)
    separation = min(separation, 360.0 - separation)

    orb = abs(separation - aspect_angle)

    return orb


def check_retrograde_at_date(transit_planet_id: int, date: datetime) -> bool:
    """
    בודק אם כוכב נמצא בנסיגה בתאריך מסוים.
    """
    # נקודות לא יכולות להיות בנסיגה
    if transit_planet_id in [swe.MEAN_NODE, swe.TRUE_NODE, swe.MEAN_APOG, swe.OSCU_APOG]:
        return False

    jd = swe.julday(date.year, date.month, date.day,
                    date.hour + date.minute / 60.0 + date.second / 3600.0)

    xx, _ = swe.calc_ut(jd, transit_planet_id)
    speed = ensure_float(xx[3])  # מהירות אורכית

    return speed < 0


def binary_search_boundary(natal_lon: float, transit_planet_id: int,
                           aspect_angle: float, max_orb: float,
                           start_date: datetime, end_date: datetime,
                           search_direction: str = 'forward') -> datetime:
    """
    מוצא את הגבול המדויק (כניסה/יציאה מאורב) באמצעות Binary Search.
    """
    tolerance_hours = 1.0

    left = start_date
    right = end_date

    while (right - left).total_seconds() / 3600 > tolerance_hours:
        mid = left + (right - left) / 2

        mid_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                        aspect_angle, mid)

        is_in_orb = mid_orb <= max_orb

        if search_direction == 'backward':
            if is_in_orb:
                right = mid
            else:
                left = mid
        else:  # forward
            if is_in_orb:
                left = mid
            else:
                right = mid

    return left + (right - left) / 2


def find_exact_date(natal_lon: float, transit_planet_id: int,
                    aspect_angle: float, start_date: datetime,
                    end_date: datetime) -> datetime:
    """
    מוצא את התאריך המדויק שבו ההיבט הוא Exact (אורב מינימלי).
    """
    tolerance_hours = 1.0

    left = start_date
    right = end_date

    golden_ratio = (math.sqrt(5) - 1) / 2

    while (right - left).total_seconds() / 3600 > tolerance_hours:
        mid1 = left + (right - left) * (1 - golden_ratio)
        mid2 = left + (right - left) * golden_ratio

        orb1 = calculate_orb_at_date(natal_lon, transit_planet_id,
                                     aspect_angle, mid1)
        orb2 = calculate_orb_at_date(natal_lon, transit_planet_id,
                                     aspect_angle, mid2)

        if orb1 < orb2:
            right = mid2
        else:
            left = mid1

    return left + (right - left) / 2


def find_retrograde_turns(transit_planet_id: int, start_date: datetime,
                          end_date: datetime) -> list:
    """
    מוצא את נקודות התפנית (Direct → Retrograde או להיפך) בטווח זמן נתון.
    """
    turns = []
    current = start_date
    prev_is_retro = None

    while current <= end_date:
        is_retro = check_retrograde_at_date(transit_planet_id, current)

        if prev_is_retro is not None and is_retro != prev_is_retro:
            turns.append({
                'date': current,
                'to_retrograde': is_retro
            })

        prev_is_retro = is_retro
        current += timedelta(days=1)

    return turns


def find_all_exact_dates(natal_lon: float, transit_planet_id: int,
                         aspect_angle: float, start_date: datetime,
                         end_date: datetime, retrograde_turns: list) -> list:
    """
    מוצא את כל נקודות ה-Exact במחזור (יכול להיות 1-3).
    """
    exact_dates = []

    if not retrograde_turns:
        # אין נסיגות - Exact אחד פשוט
        exact_date = find_exact_date(natal_lon, transit_planet_id, aspect_angle,
                                     start_date, end_date)
        is_retro = check_retrograde_at_date(transit_planet_id, exact_date)
        exact_dates.append({
            'date': exact_date,
            'is_retrograde': is_retro
        })
    else:
        # יש נסיגות - חלק לסגמנטים
        segment_boundaries = [start_date] + [t['date'] for t in retrograde_turns] + [end_date]

        for i in range(len(segment_boundaries) - 1):
            seg_start = segment_boundaries[i]
            seg_end = segment_boundaries[i + 1]

            try:
                exact_date = find_exact_date(natal_lon, transit_planet_id,
                                             aspect_angle, seg_start, seg_end)
                is_retro = check_retrograde_at_date(transit_planet_id, exact_date)

                exact_dates.append({
                    'date': exact_date,
                    'is_retrograde': is_retro
                })
            except Exception:
                continue

    return exact_dates


def get_retrograde_info(transit_planet_id: int, current_date: datetime) -> dict:
    """
    מחזיר מידע מלא על מצב הנסיגה של כוכב.
    """
    if transit_planet_id in [swe.MEAN_NODE, swe.TRUE_NODE, swe.MEAN_APOG, swe.OSCU_APOG]:
        return {
            'is_retrograde_now': False,
            'next_station': None,
            'station_type': None,
            'has_retrograde_in_range': False
        }

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
    avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))
    estimated_days = (max_orb * 2) / avg_speed if avg_speed > 0 else 90
    estimated_days = max(7, min(730, estimated_days))

    # אם יש נסיגה בטווח - הרחב את החיפוש
    if retro_info['has_retrograde_in_range']:
        estimated_days = min(730, estimated_days * 3)

    # 3. חיפוש אחורה לתחילת מחזור
    cycle_start = current_date
    for days_back in range(1, int(estimated_days)):
        test_date = current_date - timedelta(days=days_back)
        test_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                         aspect_angle, test_date)
        if test_orb > max_orb:
            cycle_start = binary_search_boundary(
                natal_lon, transit_planet_id, aspect_angle, max_orb,
                test_date, current_date, 'backward'
            )
            break

    # 4. חיפוש קדימה לסוף מחזור
    cycle_end = current_date
    for days_forward in range(1, int(estimated_days)):
        test_date = current_date + timedelta(days=days_forward)
        test_orb = calculate_orb_at_date(natal_lon, transit_planet_id,
                                         aspect_angle, test_date)
        if test_orb > max_orb:
            cycle_end = binary_search_boundary(
                natal_lon, transit_planet_id, aspect_angle, max_orb,
                current_date, test_date, 'forward'
            )
            break

    # 5. חפש נסיגות בטווח
    retrograde_turns = find_retrograde_turns(
        transit_planet_id, cycle_start, cycle_end
    )

    has_retrograde = len(retrograde_turns) > 0

    # 6. מצא את כל נקודות ה-Exact
    exact_dates = find_all_exact_dates(
        natal_lon, transit_planet_id, aspect_angle,
        cycle_start, cycle_end, retrograde_turns
    )

    # 7. חשב נתונים
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
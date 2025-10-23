import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from .CalculationEngine import ASPECT_ORBS

# TODO: הדפסת מפת מעברים

# הגדרת גופן עברי
plt.rcParams['font.family'] = 'DejaVu Sans'


def fix_hebrew_text(text):
    """מתקן טקסט עברי להצגה נכונה ב-matplotlib - הופך לגמרי את כל הטקסט"""
    if not text:
        return text
    return text[::-1]


# מילון סמלי פלנטות (Unicode)
PLANET_SYMBOLS = {
    'שמש': '☉', 'ירח': '☽', 'מרקורי': '☿', 'ונוס': '♀',
    'מאדים': '♂', 'צדק': '♃', 'שבתאי': '♄', 'אורנוס': '♅',
    'נפטון': '♆', 'פלוטו': '♇', 'ראש דרקון': '☊', 'זנב דרקון': '☋',
    'Ascendant': 'AC', 'Midheaven': 'MC', 'אופק (AC)': 'AC', 'רום שמיים (MC)': 'MC', 'כירון': '⚷', 'לילית': '⚸',
    'פורטונה': '⊗', 'ורטקס': '☩'

}

ZODIAC_SYMBOLS = {
    0: '♈', 30: '♉', 60: '♊', 90: '♋', 120: '♌', 150: '♍',
    180: '♎', 210: '♏', 240: '♐', 270: '♑', 300: '♒', 330: '♓'
}

ZODIAC_NAMES = {
    0: 'טלה', 30: 'שור', 60: 'תאומים', 90: 'סרטן', 120: 'אריה', 150: 'בתולה',
    180: 'מאזניים', 210: 'עקרב', 240: 'קשת', 270: 'גדי', 300: 'דלי', 330: 'דגים'
}

# שמות פלנטות בעברית
PLANET_NAMES_HEB = {
    'שמש': 'שמש', 'ירח': 'ירח', 'מרקורי': 'כוכב', 'ונוס': 'נוגה',
    'מאדים': 'מאדים', 'צדק': 'צדק', 'שבתאי': 'שבתאי', 'אורנוס': 'אורנוס',
    'נפטון': 'נפטון', 'פלוטו': 'פלוטו',
    'ראש דרקון': 'ראש', 'זנב דרקון': 'זנב',
    'Ascendant': 'AC', 'Midheaven': 'MC'
}

# צבעי אספקטים
ASPECT_COLORS = {
    'Conjunction': '#FF0000',  # אדום - צמוד (0°)
    'Opposition': '#0000FF',  # כחול - ניגוד (180°)
    'Trine': '#00AA00',  # ירוק - תלת (120°)
    'Square': '#FF6600',  # כתום - ריבוע (90°)
    'Sextile': '#9933FF'  # סגול - שישי (60°)
}


def normalize_angle(angle):
    """מנרמל זווית לטווח 0-360"""
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def convert_to_chart_angle(astrological_degree, ascendant_degree):
    """
    ממיר מעלה אסטרולוגית למערכת הציור של המפה
    :param astrological_degree: מעלה אסטרולוגית (0-360)
    :param ascendant_degree: מעלת האופק
    :return: זווית במערכת matplotlib
    """
    # האופק צריך להיות ב-180° (שמאל) במערכת matplotlib
    # לכן נחסר את מעלת האופק ונוסיף 180
    chart_angle = (astrological_degree - ascendant_degree + 180) % 360
    return chart_angle


def calculate_aspect(angle1, angle2):
    """
    מחשב אספקט בין שתי זוויות
    :param angle1: זווית פלנטה 1
    :param angle2: זווית פלנטה 2
    :param orb: טווח סטייה מותר במעלות (ברירת מחדל: 8°)
    :return: (aspect_type, exact_angle) או (None, None)
    """
    diff = abs(normalize_angle(angle1 - angle2))
    if diff > 180:
        diff = 360 - diff

    aspects = [
        (0, 'Conjunction'),
        (60, 'Sextile'),
        (90, 'Square'),
        (120, 'Trine'),
        (180, 'Opposition')
    ]

    for target_angle, aspect_type in aspects:
        # **שינוי מרכזי: קבלת האורב הספציפי**
        max_orb_for_aspect = ASPECT_ORBS.get(aspect_type, 0.5)  # השתמש ב-0.5 כברירת מחדל נמוכה לבטיחות
        
        if abs(diff - target_angle) <= max_orb_for_aspect:
            return aspect_type, diff

    return None, None


def draw_degree_marks(ax, ascendant_degree, inner_radius=0.75):
    """
    מצייר שנתות מעלות (סרגל דרגות) בתוך טבעת הבתים/מזלות.
    :param ax: ציר matplotlib
    :param ascendant_degree: מעלת האופק
    :param inner_radius: רדיוס התחלה של השנתות (הצד החיצוני של טבעת הפלנטות)
    """
    for degree in range(0, 360):
        chart_angle = convert_to_chart_angle(degree, ascendant_degree)
        angle_rad = np.deg2rad(chart_angle)

        is_ten_deg = (degree % 10) == 0
        is_five_deg = (degree % 5) == 0 and not is_ten_deg

        # קביעת אורך הקו
        if is_ten_deg:
            length_factor = 0.05
            linewidth = 1.0
        elif is_five_deg:
            length_factor = 0.025
            linewidth = 0.7
        else:
            length_factor = 0.0125
            linewidth = 0.5

        # חישוב הרדיוס החיצוני והפנימי של השנתות
        r_start = inner_radius
        r_end = inner_radius + length_factor  # מושך את הקו החוצה

        x_start = r_start * np.cos(angle_rad)
        y_start = r_start * np.sin(angle_rad)
        x_end = r_end * np.cos(angle_rad)
        y_end = r_end * np.sin(angle_rad)

        ax.plot([x_start, x_end], [y_start, y_end],
                color='#34495E', linewidth=linewidth, zorder=5, solid_capstyle='butt')


def draw_aspect_lines(ax, planets_positions, orb=8):
    """
    מצייר קווי אספקטים בין פלנטות
    :param ax: ציר matplotlib
    :param planets_positions: מילון {planet_name: (x, y, original_lon)}
    :param orb: טווח סטייה מותר
    """
    planet_list = list(planets_positions.items())

    for i, (planet1, (x1, y1, original_lon1)) in enumerate(planet_list):
        for planet2, (x2, y2, original_lon2) in planet_list[i + 1:]:
            aspect_type, angle = calculate_aspect(original_lon1, original_lon2)

            if aspect_type:
                color = ASPECT_COLORS.get(aspect_type, '#CCCCCC')
                linewidth = 1.5 if aspect_type in ['Conjunction', 'Opposition'] else 0.8
                alpha = 0.6 if aspect_type in ['Trine', 'Sextile'] else 0.4

                # ציור קו בין הפלנטות דרך המרכז
                inner_radius = 0.68

                ax.plot([x1 * (inner_radius / 0.85), x2 * (inner_radius / 0.85)],
                        [y1 * (inner_radius / 0.85), y2 * (inner_radius / 0.85)],
                        color=color, linewidth=linewidth, alpha=alpha, zorder=1)


def draw_houses(ax, houses_data, ascendant_degree):
    """
    מצייר קווי בתים (Houses) ומוסיף את מספר הבית במרכז הגזרה שלו.
    :param ax: ציר matplotlib
    :param houses_data: מילון נתוני הבתים - {house_num: cusp_deg}
    :param ascendant_degree: מעלת האופק (לחישוב מיקום נכון)
    """
    if not houses_data:
        print("⚠️ אין נתוני בתים לציור")
        return

    # 1. מיון הנתונים לפי סדר הבתים וקבלת מעלות ה-cusp
    cusps = sorted([(house_num, data['cusp_deg'])
                    for house_num, data in houses_data.items()
                    if 'cusp_deg' in data], key=lambda x: x[0])

    if not cusps:
        return

    cusp_degrees = {h: deg for h, deg in cusps}

    # 2. ציור קווי הבתים (ללא שינוי מהותי)
    for house_num in range(1, 13):
        house_key = house_num
        if house_key not in cusp_degrees:
            continue

        cusp_deg = cusp_degrees[house_key]

        # המרת זווית אסטרולוגית למערכת הציור
        chart_angle = convert_to_chart_angle(cusp_deg, ascendant_degree)
        angle_rad = np.deg2rad(chart_angle)

        # ציור קו מהמרכז ועד לטבעת הפנימית (0.75)
        x_outer = 0.75 * np.cos(angle_rad)
        y_outer = 0.75 * np.sin(angle_rad)

        # בתים מיוחדים (1, 4, 7, 10) יהיו עבים יותר
        is_angular_house = house_num in [1, 4, 7, 10]
        # ✅ ניתן להגדיר קו האופק/רום שמיים כקו מיוחד ועבה יותר
        linewidth = 2.5 if is_angular_house else 1.0

        ax.plot([0, x_outer], [0, y_outer],
                color='#000000', linewidth=linewidth, alpha=0.9, zorder=20, solid_capstyle='round')

    # 3. הוספת מספרי הבתים במרכז כל גזרה

    # ✅ הרדיוס החדש למיקום מספרי הבתים - קרוב יותר למרכז, בדומה לדוגמה
    text_radius = 0.15

    # מעבר על כל 12 הבתים לחישוב מרכז הבית
    for i in range(1, 13):
        house_num = i

        # קצה הבית הנוכחי
        current_cusp_deg = cusp_degrees.get(house_num)

        # קצה הבית הקודם (הוא הקצה של הבית הקודם, או 360 מעלות אחורה לבית 1)
        prev_house_num = (house_num - 1) if house_num > 1 else 12
        prev_cusp_deg = cusp_degrees.get(prev_house_num)

        if current_cusp_deg is None or prev_cusp_deg is None:
            continue

        # חישוב הזווית המרכזית של גזרת הבית:
        # הזווית האסטרולוגית משמאל לימין, אז צריך לקחת את הממוצע של הקצה הנוכחי והקצה הקודם.

        # נרמול הפרש הזוויות: בית 12 (330) לבית 1 (15) - הטווח הוא 345-15 (לא 15-330)
        # 1. חישוב המרחק המעגלי
        angle_diff = normalize_angle(current_cusp_deg - prev_cusp_deg)

        # 2. חישוב מרכז הבית (הזווית האסטרולוגית הממוצעת)
        # נוסיף חצי מההפרש לזווית ההתחלה (הקצה של הבית הקודם)
        center_deg = normalize_angle(prev_cusp_deg + angle_diff / 2)

        # 3. המרה למערכת הציור
        chart_angle = convert_to_chart_angle(center_deg, ascendant_degree)
        angle_rad = np.deg2rad(chart_angle)

        # חישוב מיקום ה-X, Y למספר הבית
        x_text = text_radius * np.cos(angle_rad)
        y_text = text_radius * np.sin(angle_rad)

        # 🚨 הדפסת מספר הבית במיקום המרכזי ללא מסגרת (bbox)
        ax.text(x_text, y_text, str((house_num + 11) % 12 if (house_num + 11) % 12 != 0 else 12),
                fontsize=12, ha='center', va='center',
                color='#000000', fontweight='bold', zorder=22)  # Zorder גבוה
        # ✅ הסרת ה-bbox:
        # bbox=dict(boxstyle='circle,pad=0.12', facecolor='white',
        #           edgecolor='#000000', linewidth=1.2, alpha=0.95))


def avoid_planet_overlap(planets_data, min_separation=8):
    """
    מתאם את מיקומי הפלנטות כדי למנוע חפיפה חזותית
    :param planets_data: מילון {planet: chart_angle}
    :param min_separation: מרווח מינימלי במעלות
    :return: מילון מותאם {planet: adjusted_chart_angle}
    """
    if not planets_data:
        return {}

    # מיון פלנטות לפי זווית במערכת הציור
    sorted_planets = sorted(planets_data.items(), key=lambda x: x[1])
    adjusted = {}

    for i, (planet, chart_angle) in enumerate(sorted_planets):
        if i == 0:
            adjusted[planet] = chart_angle
            continue

        prev_planet, prev_angle = sorted_planets[i - 1]
        prev_adjusted = adjusted[prev_planet]

        # בדיקת מרווח מהפלנטה הקודמת
        diff = chart_angle - prev_adjusted
        if diff < min_separation:
            # הזזה קדימה
            adjusted[planet] = prev_adjusted + min_separation
        else:
            adjusted[planet] = chart_angle

    return adjusted


# בתוך BirthChartDrawer.py, הוסף את שתי הפונקציות הבאות:

from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np


# הנחה: פונקציות העזר כמו fix_hebrew_text, convert_to_chart_angle, draw_houses, calculate_aspect,
# וכן המילונים PLANET_SYMBOLS, ZODIAC_SYMBOLS, ASPECT_COLORS מוגדרים בקובץ זה או מיובאים.


def draw_biwheel_planets(ax, planets_data: dict, ascendant_degree: float, is_transit=False) -> dict:
    """
    פונקציית עזר לציור פלנטות, מתאימה רדיוס לנטאל (פנימי) או לטרנזיט (חיצוני).

    מחזירה מילון עם מיקום XY, מעלה גולמית ורדיוס של כל פלנטה, לצורך ציור אספקטים.
    """

    # הגדרות רדיוסים בהתאם לנטאל (פנימי) או טרנזיט (חיצוני)
    # נטאל (is_transit=False) יהיה עכשיו ברדיוס הקטן (0.62)
    # טרנזיט (is_transit=True) יהיה עכשיו ברדיוס הגדול (0.8)
    if is_transit:
        base_planet_radius = 0.8  # רדיוס חיצוני לטרנזיט (כחול)
        planet_color = '#0000FF'  # כחול לטרנזיט
        text_color = '#00008B'
        max_radius = 1.3  # מגדירים טווח רדיוס מקסימלי לטרנזיט
    else:
        base_planet_radius = 0.62  # רדיוס פנימי לנטאל (אדום)
        planet_color = '#E74C3C'  # אדום לנטאל
        text_color = '#2C3E50'
        max_radius = 0.73  # מגדירים טווח רדיוס מקסימלי לנטאל

    line_start_radius = 0.47  # נמתח מטבעת האספקטים
    min_separation_angle = 3
    overlap_offset = 0.05
    planets_positions = {}

    planets_list_for_overlap_check = []
    # סינון ואיסוף רק כוכבים שיוצגו בגלגל
    for name, data in planets_data.items():
        if 'lon_deg' in data and data['lon_deg'] is not None and name not in ['אופק (AC)', 'רום שמיים (MC)', 'ורטקס']:
            original_lon = data['lon_deg']
            # המרה לזווית במערכת הציור, בהתאם ל-AC הנטאלי
            chart_angle = convert_to_chart_angle(original_lon, ascendant_degree)
            planets_list_for_overlap_check.append((name, chart_angle, original_lon))

    # מיון לפי זווית כדי לטפל בחפיפה
    sorted_planets_for_drawing = sorted(planets_list_for_overlap_check, key=lambda k: k[1])
    occupied_slots = {}

    for planet_name, chart_angle, original_lon in sorted_planets_for_drawing:

        # התאמת רדיוס למניעת חפיפה
        current_radius = base_planet_radius
        for occupied_angle, used_radius in occupied_slots.items():
            diff = abs(chart_angle - occupied_angle)
            if diff > 180: diff = 360 - diff
            if diff < min_separation_angle:
                current_radius = max(current_radius, used_radius + overlap_offset)
                max_radius = 1.3 if is_transit else 0.73
                if current_radius > max_radius: break

        occupied_slots[chart_angle] = current_radius
        current_text_radius = current_radius + 0.1

        angle_rad = np.deg2rad(chart_angle)

        # ציור קו רדיאלי
        current_line_end_radius = current_radius - 0.025
        x_start_line = line_start_radius * np.cos(angle_rad)
        y_start_line = line_start_radius * np.sin(angle_rad)
        x_end_line = current_line_end_radius * np.cos(angle_rad)
        y_end_line = current_line_end_radius * np.sin(angle_rad)

        ax.plot([x_start_line, x_end_line], [y_start_line, y_end_line],
                color=planet_color, linewidth=0.5, alpha=0.8, zorder=12, solid_capstyle='butt')

        # ציור סמל הפלנטה
        angle_rad = np.deg2rad(chart_angle)
        x = current_radius * np.cos(angle_rad)
        y = current_radius * np.sin(angle_rad)
        symbol = PLANET_SYMBOLS.get(planet_name, planet_name[:2])

        ax.text(x, y, fix_hebrew_text(symbol), fontsize=20, ha='center', va='center',
                color=planet_color, fontweight='bold', zorder=15, family='DejaVu Sans')

        # 2. ציור טקסט המעלות
        sign_deg = original_lon % 30
        degree_text = f"{sign_deg:.1f}°"
        x_deg = current_text_radius * np.cos(angle_rad)
        y_deg = current_text_radius * np.sin(angle_rad)

        ax.text(x_deg, y_deg, degree_text, fontsize=8,
                ha='center', va='center', color=text_color, zorder=14,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ECF0F1',
                          edgecolor='none', alpha=0.8))

        # שמירת המיקום המנורמל והרדיוס לחיבורי האספקטים
        planets_positions[planet_name] = (x, y, original_lon, current_radius)

    return planets_positions


def draw_and_save_biwheel_chart(natal_chart_data: dict, transit_chart_data: dict, user_obj, current_datetime: datetime,
                                output_path: str):
    """
    מצייר מפת מעברים (Bi-Wheel), כאשר הנטאל בפנים (אדום) והמעברים בחוץ (כחול).
    """
    try:
        # חילוץ נתונים
        natal_planets = natal_chart_data.get('Planets', {})
        natal_house_cusps = natal_chart_data.get('HouseCusps', [])
        transit_planets = transit_chart_data.get('Planets', {})

        # =========================================================================
        # לוגיקת מציאת מעלת האופק הנטאלי (AC) והבתים
        # =========================================================================
        ascendant_degree = None

        # 1. חילוץ AC מתוך רשימת קווי היתד (אינדקס 1)
        if isinstance(natal_house_cusps, (list, tuple)) and len(natal_house_cusps) == 13:
            ascendant_degree = float(natal_house_cusps[1])

        # 2. גיבוי: חילוץ AC מנתוני הפלנטות
        if ascendant_degree is None and 'אופק (AC)' in natal_planets and 'lon_deg' in natal_planets['אופק (AC)']:
            ascendant_degree = natal_planets['אופק (AC)']['lon_deg']

        if ascendant_degree is None:
            print("❌ שגיאה: לא נמצאה מעלת האופק הנטאלי!")
            return

        # 3. עיצוב נתוני הבתים לציור
        houses_data_formatted = {}
        if isinstance(natal_house_cusps, (list, tuple)) and len(natal_house_cusps) == 13:
            for house_num in range(1, 13):
                cusp_deg = float(natal_house_cusps[house_num])
                houses_data_formatted[house_num] = {'cusp_deg': cusp_deg}

        # =========================================================================
        # הגדרת הגרף
        # =========================================================================
        fig, ax = plt.subplots(figsize=(18, 18), facecolor='#F5F5DC')
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.axis('off')

        # =====================================
        # 1. ציור הטבעות המרכזיות
        # =====================================

        # טבעת חיצונית - מזלות (1.0)
        circle_outer = plt.Circle((0, 0), 1.0, color='#2C3E50', fill=False, linewidth=2.5)
        ax.add_artist(circle_outer)

        # טבעת פלנטות פנימית (נטאל) - 0.75
        circle_planets_natal = plt.Circle((0, 0), 0.75, color='#0000FF', fill=False, linewidth=1.5)
        ax.add_artist(circle_planets_natal)

        # ציור שנתות המעלות
        draw_degree_marks(ax, ascendant_degree, inner_radius=0.5)

        # טבעת אספקטים (0.5)
        circle_inner = plt.Circle((0, 0), 0.5, color='#E74C3C', fill=False, linewidth=1.5)
        ax.add_artist(circle_inner)

        # טבעת פנימית - אספקטים (0.47)
        circle_inner = plt.Circle((0, 0), 0.47, color='#7F8C8D', fill=False, linewidth=1.0)
        ax.add_artist(circle_inner)

        # מעגל מרכזי
        circle_center = plt.Circle((0, 0), 0.05, color='#2C3E50', fill=True)
        ax.add_artist(circle_center)

        # =====================================
        # 2. ציור קווי בתים והמזלות
        # =====================================

        # ציור הבתים
        draw_houses(ax, houses_data_formatted, ascendant_degree)

        # ציור קווי חלוקת המזלות וסמלים
        for zodiac_start_deg in range(0, 360, 30):
            chart_angle = convert_to_chart_angle(zodiac_start_deg, ascendant_degree)
            angle_rad = np.deg2rad(chart_angle)

            # קו חלוקה
            x_inner = 0.5 * np.cos(angle_rad)
            y_inner = 0.5 * np.sin(angle_rad)
            x_outer = 1.0 * np.cos(angle_rad)
            y_outer = 1.0 * np.sin(angle_rad)

            ax.plot([x_inner, x_outer], [y_inner, y_outer],
                    color='#95A5A6', linewidth=1.5, zorder=2, alpha=0.7)

            # סמל המזל
            text_chart_angle = convert_to_chart_angle(zodiac_start_deg + 15, ascendant_degree)
            text_angle_rad = np.deg2rad(text_chart_angle)
            text_radius = 0.84
            x_label = text_radius * np.cos(text_angle_rad)
            y_label = text_radius * np.sin(text_angle_rad)

            symbol = ZODIAC_SYMBOLS.get(zodiac_start_deg, '')
            zodiac_name = ZODIAC_NAMES.get(zodiac_start_deg, '')

            ax.text(x_label, y_label, symbol, fontsize=22, ha='center', va='center',
                    color='#2C3E50', fontweight='bold', zorder=3, family='DejaVu Sans')

            zodiac_name_fixed = fix_hebrew_text(zodiac_name)
            ax.text(x_label * 1.1, y_label * 1.1, zodiac_name_fixed, fontsize=12,
                    ha='center', va='center', color='#34495E', zorder=3)

        # =====================================
        # 3. ציור פלנטות הנטאל (פנימי, אדום)
        # =====================================
        natal_positions = draw_biwheel_planets(ax, natal_planets, ascendant_degree, is_transit=False)

        # =====================================
        # 4. ציור פלנטות המעברים (חיצוני, כחול)
        # =====================================
        transit_positions = draw_biwheel_planets(ax, transit_planets, ascendant_degree, is_transit=True)

        # =====================================
        # 5. ציור אספקטים (נטאל-טרנזיט)
        # =====================================
        inner_radius_aspect = 0.45

        for natal_planet, (nx, ny, n_lon, n_rad) in natal_positions.items():
            for transit_planet, (tx, ty, t_lon, t_rad) in transit_positions.items():
                aspect_type, angle = calculate_aspect(n_lon, t_lon)

                if aspect_type:
                    color = ASPECT_COLORS.get(aspect_type, '#CCCCCC')
                    linewidth = 2.0 if aspect_type in ['Conjunction', 'Opposition'] else 1.0
                    alpha = 0.6 if aspect_type in ['Trine', 'Sextile'] else 0.4

                    n_center_x = nx * (inner_radius_aspect / n_rad)
                    n_center_y = ny * (inner_radius_aspect / n_rad)
                    t_center_x = tx * (inner_radius_aspect / t_rad)
                    t_center_y = ty * (inner_radius_aspect / t_rad)

                    ax.plot([n_center_x, t_center_x], [n_center_y, t_center_y],
                            color=color, linewidth=linewidth, alpha=alpha, zorder=1)

        # =====================================
        # 6. כותרת ופרטים
        # =====================================
        user_name = user_obj.name
        birthdate = user_obj.birthdate
        natal_time_str = user_obj.birthtime.strftime('%H:%M') if user_obj.birthtime else "לא ידוע"
        transit_date = current_datetime.strftime('%Y-%m-%d')
        transit_time = current_datetime.strftime('%H:%M')

        title_text = fix_hebrew_text(f"מפת מעברים")
        natal_details = (f" {natal_time_str} " + fix_hebrew_text("| שעת לידה:") +
                         f" {birthdate} " + fix_hebrew_text("תאריך לידה:"))
        transit_details = (f" {transit_time} " + fix_hebrew_text("| שעת מעבר:") +
                           f" {transit_date} " + fix_hebrew_text("תאריך מעבר:"))

        plt.text(0, 1.45, title_text, fontsize=25, ha='center', fontweight='bold', color='#2C3E50')
        plt.text(0, 1.38, natal_details, fontsize=18, ha='center', color='#E74C3C')
        plt.text(0, 1.30, transit_details, fontsize=18, ha='center', color='#0000FF')

        # =====================================
        # 7. שמירת התמונה
        # =====================================
        plt.savefig(output_path, bbox_inches='tight', dpi=150, facecolor='#F5F5DC')
        plt.close()

        print(f"\n✅ מפת המעברים נשמרה בהצלחה בקובץ: {output_path}")

    except Exception as e:
        import traceback
        print(f"❌ אירעה שגיאה בציור מפת המעברים: {e}")
        traceback.print_exc()


def draw_and_save_chart(chart_data: dict, user_obj, output_path: str):
    """
    מצייר גלגל מפת לידה משופר ושומר אותו כתמונה.

    :param chart_data: מילון נתוני המפה (Planets, HouseCusps, Aspects)
    :param user_obj: אובייקט ה-User המכיל את הפרטים (שם, תאריך, מיקום)
    :param output_path: הנתיב המלא לשמירת קובץ התמונה
    """
    try:
        # ✅ תיקון: שימוש במפתחות הנכונים
        planets_data = chart_data.get('Planets', {})
        house_cusps = chart_data.get('HouseCusps', {})
        user_name = user_obj.name
        birthdate = user_obj.birthdate
        birthtime = user_obj.birthtime if user_obj.birthtime else "לא ידוע"

        ascendant_degree = None

        # אם house_cusps הוא מילון
        if isinstance(house_cusps, dict):
            if 1 in house_cusps:
                cusp_value = house_cusps[1]
                if isinstance(cusp_value, (list, tuple)):
                    ascendant_degree = float(cusp_value[0])
                else:
                    ascendant_degree = float(cusp_value)
            elif house_cusps:
                # נסיון לקחת את הערך הראשון
                first_key = list(house_cusps.keys())[0]
                print(f"⚠️ לא נמצא מפתח 1, משתמש במפתח הראשון: {first_key}")
                cusp_value = house_cusps[first_key]
                if isinstance(cusp_value, (list, tuple)):
                    ascendant_degree = float(cusp_value[0])
                else:
                    ascendant_degree = float(cusp_value)

        # אם house_cusps הוא רשימה
        elif isinstance(house_cusps, (list, tuple)) and len(house_cusps) > 1:
            # הבית הראשון הוא באינדקס 1 (האינדקס 0 יכול להיות ריק או אורך הרשימה)
            cusp_value = house_cusps[1] if len(house_cusps) > 1 else house_cusps[0]
            if isinstance(cusp_value, (list, tuple)):
                ascendant_degree = float(cusp_value[0])
            else:
                ascendant_degree = float(cusp_value)

        if ascendant_degree is None:
            print("❌ שגיאה: לא נמצאה מעלת האופק!")
            print(f"   house_cusps type: {type(house_cusps)}")
            print(f"   house_cusps content: {house_cusps}")
            return

        # הגדרת הגרף
        fig, ax = plt.subplots(figsize=(14, 14), facecolor='#F5F5DC')
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.axis('off')

        # =====================================
        # 1. ציור הטבעות המרכזיות
        # =====================================

        # טבעת חיצונית - מזלות (1.0)
        circle_outer = plt.Circle((0, 0), 1.0, color='#2C3E50', fill=False, linewidth=2.5)
        ax.add_artist(circle_outer)

        # טבעת פלנטות (0.75)
        circle_planets = plt.Circle((0, 0), 0.75, color='#34495E', fill=False, linewidth=1.5)
        ax.add_artist(circle_planets)

        # ציור שנתות המעלות
        draw_degree_marks(ax, ascendant_degree, inner_radius=0.75)

        # טבעת פנימית - אספקטים (0.7)
        circle_inner = plt.Circle((0, 0), 0.7, color='#7F8C8D', fill=False, linewidth=1.0)
        ax.add_artist(circle_inner)

        # מעגל מרכזי
        circle_center = plt.Circle((0, 0), 0.05, color='#2C3E50', fill=True)
        ax.add_artist(circle_center)

        # =====================================
        # 2. ציור קווי בתים (Houses) - לפני המזלות!
        # =====================================

        # ✅ בניית מבנה houses_data מ-HouseCusps - תיקון המפתח למספר שלם
        houses_data_formatted = {}
        if house_cusps:
            # .... (הקוד לבדיקה וחלוקה נשאר דומה)
            if isinstance(house_cusps, dict):
                for house_num in range(1, 13):
                    if house_num in house_cusps:
                        cusp_value = house_cusps[house_num]
                        if isinstance(cusp_value, (list, tuple)):
                            cusp_deg = float(cusp_value[0])
                        else:
                            cusp_deg = float(cusp_value)
                        # שינוי המפתח למספר שלם
                        houses_data_formatted[house_num] = {'cusp_deg': cusp_deg}
            elif isinstance(house_cusps, (list, tuple)):
                for house_num in range(1, min(13, len(house_cusps))):
                    cusp_value = house_cusps[house_num]
                    if isinstance(cusp_value, (list, tuple)):
                        cusp_deg = float(cusp_value[0])
                    else:
                        cusp_deg = float(cusp_value)
                    # שינוי המפתח למספר שלם
                    houses_data_formatted[house_num] = {'cusp_deg': cusp_deg}

        draw_houses(ax, houses_data_formatted, ascendant_degree)  # קריאה עם המבנה החדש

        # =====================================
        # 3. ציור קווי חלוקת המזלות וסמלים
        # =====================================

        for zodiac_start_deg in range(0, 360, 30):
            # המרה למערכת הציור
            chart_angle = convert_to_chart_angle(zodiac_start_deg, ascendant_degree)
            angle_rad = np.deg2rad(chart_angle)

            # קו חלוקה מהטבעת הפנימית לחיצונית
            x_inner = 0.75 * np.cos(angle_rad)
            y_inner = 0.75 * np.sin(angle_rad)
            x_outer = 1.0 * np.cos(angle_rad)
            y_outer = 1.0 * np.sin(angle_rad)

            ax.plot([x_inner, x_outer], [y_inner, y_outer],
                    color='#95A5A6', linewidth=1.5, zorder=2, alpha=0.7)

            # סמל המזל במרכז כל מזל (זווית +15)
            text_chart_angle = convert_to_chart_angle(zodiac_start_deg + 15, ascendant_degree)
            text_angle_rad = np.deg2rad(text_chart_angle)

            text_radius = 0.875
            x_label = text_radius * np.cos(text_angle_rad)
            y_label = text_radius * np.sin(text_angle_rad)

            symbol = ZODIAC_SYMBOLS.get(zodiac_start_deg, '')
            zodiac_name = ZODIAC_NAMES.get(zodiac_start_deg, '')

            # סמל המזל
            ax.text(x_label, y_label, symbol, fontsize=20, ha='center', va='center',
                    color='#2C3E50', fontweight='bold', zorder=3, family='DejaVu Sans')

            # שם המזל (קטן יותר, מתחת)
            zodiac_name_fixed = fix_hebrew_text(zodiac_name)
            ax.text(x_label * 1.08, y_label * 1.08, zodiac_name_fixed, fontsize=12,
                    ha='center', va='center', color='#34495E', zorder=3)

        # =====================================
        # 4. הכנת נתוני פלנטות למיקום
        # =====================================

        # המרה לזוויות במערכת הציור
        planets_chart_angles = {}
        planets_original_lon = {}  # שמירת המעלות המקוריות לאספקטים
        planets_list_for_overlap_check = []  # רשימה לאיסוף נתונים ולמיון לצורך ציור

        # סעיף 4 - הגדרות חדשות לטקסט המעלות
        text_radius_base = 1.05
        text_overlap_offset = 0.03  # או 0.05, תלוי בגודל הגופן
        occupied_text_slots = {}

        for name, data in planets_data.items():
            if 'lon_deg' in data and data['lon_deg'] is not None and name not in ['אופק (AC)', 'רום שמיים (MC)']:
                original_lon = data['lon_deg']
                chart_angle = convert_to_chart_angle(original_lon, ascendant_degree)
                planets_chart_angles[name] = chart_angle
                planets_original_lon[name] = original_lon
                # שמירת הנתונים יחד ברשימה למיון
                planets_list_for_overlap_check.append((name, chart_angle, original_lon))

        # מיון הפלנטות לפי זווית הציור המקורית (כדי לבדוק חפיפות בסדר הופעה)
        sorted_planets_for_drawing = sorted(planets_list_for_overlap_check, key=lambda k: k[1])

        # הגדרת הרדיוסים והמרווחים:
        line_start_radius = 0.7
        base_planet_radius = 0.8  # הרדיוס הקבוע החדש שלך (כדי למנוע חפיפה עם סמלי המזלות)
        overlap_offset = 0.05  # הסטה ברדיוס במקרה של צמידות (0.8 -> 0.85 -> 0.90)
        min_separation_angle = 3  # המרווח המינימלי במעלות לבדיקת צמידות חזקה (חפיפת סמלים)

        # מעקב אחר המיקומים התפוסים {chart_angle: [used_radii]}
        occupied_slots = {}
        planets_positions = {}

        # =====================================
        # 5. ציור הפלנטות
        # =====================================

        for planet_name, chart_angle, original_lon in sorted_planets_for_drawing:

            # --- 1. חישוב הרדיוס הדינמי לסמל הפלנטה (R) ---
            current_radius = base_planet_radius

            # בדיקה מול פלנטות קיימות ב-occupied_slots (סמלים)
            for occupied_angle, used_radii in occupied_slots.items():
                diff = abs(chart_angle - occupied_angle)
                # נרמול מעגלי
                if diff > 180:
                    diff = 360 - diff

                # אם יש חפיפת זוויות בטווח המינימלי (3 מעלות)
                if diff < min_separation_angle:
                    # מזיזים את הפלנטה למגש הרדיוס הפנוי הבא (0.8 -> 0.85 -> 0.90 וכו')
                    current_radius = base_planet_radius + len(used_radii) * overlap_offset
                    break

            # עדכון המיקום התפוס לסמלי הפלנטות
            occupied_slots.setdefault(chart_angle, []).append(current_radius)

            # --- 2. חישוב הרדיוס הדינמי לטקסט המעלות (R_Text) ---
            current_text_radius = text_radius_base

            # בדיקה מול פלנטות קיימות ב-occupied_text_slots (טקסט)
            for occupied_angle, used_radii in occupied_text_slots.items():
                diff = abs(chart_angle - occupied_angle)
                if diff > 180:
                    diff = 360 - diff

                if diff < min_separation_angle:
                    # מזיזים את הטקסט לרדיוס הפנוי הבא החוצה (1.05 -> 1.08 -> 1.11 וכו')
                    current_text_radius = text_radius_base + len(used_radii) * text_overlap_offset
                    break

            # עדכון המיקום התפוס לטקסט המעלות
            occupied_text_slots.setdefault(chart_angle, []).append(current_text_radius)

            # --- 3. ציור הפלנטה ---

            # עדכון רדיוס סיום הקו הרדיאלי
            current_line_end_radius = current_radius - 0.025

            # חישוב מיקום XY של סמל הפלנטה (לפי הרדיוס המותאם current_radius)
            angle_rad = np.deg2rad(chart_angle)

            x = current_radius * np.cos(angle_rad)
            y = current_radius * np.sin(angle_rad)

            symbol = PLANET_SYMBOLS.get(planet_name, planet_name[:2])

            # 5א. ציור הקו הרדיאלי האדום
            x_start_line = line_start_radius * np.cos(angle_rad)
            y_start_line = line_start_radius * np.sin(angle_rad)
            x_end_line = current_line_end_radius * np.cos(angle_rad)
            y_end_line = current_line_end_radius * np.sin(angle_rad)

            # ציור הקו האדום (מציג את המיקום המדויק)
            ax.plot([x_start_line, x_end_line], [y_start_line, y_end_line],
                    color='#FF0000', linewidth=0.5, alpha=0.8, zorder=12, solid_capstyle='butt')

            # 5ב. ציור סמל הפלנטה
            ax.text(x, y, symbol, fontsize=20, ha='center', va='center',
                    color='#E74C3C',
                    fontweight='bold', zorder=15,
                    family='DejaVu Sans'
                    )

            # 5ג. ציור טקסט המעלות (משתמש ב-current_text_radius)
            sign_deg = original_lon % 30
            degree_text = f"{sign_deg:.1f}°"

            text_radius_deg = current_text_radius
            x_deg = text_radius_deg * np.cos(angle_rad)
            y_deg = text_radius_deg * np.sin(angle_rad)

            ax.text(x_deg, y_deg, degree_text, fontsize=8,
                    ha='center', va='center', color='#2C3E50', zorder=14,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#ECF0F1',
                              edgecolor='none', alpha=0.8))

            # שמירת מיקום לאספקטים - המיקום ששימש לציור הסמל (R מותאם)
            planets_positions[planet_name] = (x, y, original_lon)

        # =====================================
        # 6. ציור אספקטים
        # =====================================

        draw_aspect_lines(ax, planets_positions, orb=8)

        # =====================================
        # 7. מקרא (Legend)
        # =====================================

        legend_lines_corrected = [
            fix_hebrew_text("אספקטים"),
            "● " + fix_hebrew_text("אדום") + " - (0°) " + fix_hebrew_text("צמידות"),
            "● " + fix_hebrew_text("כחול") + " - (180°) " + fix_hebrew_text("ניגוד"),
            "● " + fix_hebrew_text("ירוק") + " - (120°) " + fix_hebrew_text("משולש"),
            "● " + fix_hebrew_text("כתום") + " - (90°) " + fix_hebrew_text("ריבוע"),
            "● " + fix_hebrew_text("סגול") + " - (60°) " + fix_hebrew_text("משושה")
        ]

        legend_text = "\n".join(legend_lines_corrected)

        ax.text(-1.25, -1.15, legend_text, fontsize=18, ha='left', va='top',
                color='#2C3E50',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='white',
                          edgecolor='#2C3E50', linewidth=1, alpha=0.9))

        # =====================================
        # 8. כותרת ופרטי לידה
        # =====================================

        title_text = fix_hebrew_text(f"מפת לידה - {user_name}")
        # Reverse only the Hebrew labels, keeping the numbers (date/time) in LTR order.
        subtitle_text = (
                f" {birthtime} " + fix_hebrew_text("| שעה:") +
                f" {birthdate} " + fix_hebrew_text("תאריך לידה:")
        )
        plt.text(0, 1.22, title_text, fontsize=18, ha='center',
                 fontweight='bold', color='#2C3E50')
        plt.text(0, 1.15, subtitle_text, fontsize=13, ha='center',
                 color='#34495E')

        # =====================================
        # 9. שמירת התמונה
        # =====================================

        plt.savefig(output_path, bbox_inches='tight', dpi=150, facecolor='#F5F5DC')
        plt.close()

        print(f"\n✅ התוצאה נשמרה בהצלחה בקובץ: {output_path}")

    except Exception as e:
        import traceback
        print(f"❌ אירעה שגיאה בציור המפה: {e}")
        traceback.print_exc()

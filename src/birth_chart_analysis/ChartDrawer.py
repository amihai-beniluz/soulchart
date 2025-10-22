import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math

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
    'conjunction': '#FF0000',  # אדום - צמוד (0°)
    'opposition': '#0000FF',  # כחול - ניגוד (180°)
    'trine': '#00AA00',  # ירוק - תלת (120°)
    'square': '#FF6600',  # כתום - ריבוע (90°)
    'sextile': '#9933FF'  # סגול - שישי (60°)
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


def calculate_aspect(angle1, angle2, orb=8):
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
        (0, 'conjunction'),
        (60, 'sextile'),
        (90, 'square'),
        (120, 'trine'),
        (180, 'opposition')
    ]

    for target_angle, aspect_type in aspects:
        if abs(diff - target_angle) <= orb:
            return aspect_type, diff

    return None, None


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
            aspect_type, angle = calculate_aspect(original_lon1, original_lon2, orb)

            if aspect_type:
                color = ASPECT_COLORS.get(aspect_type, '#CCCCCC')
                linewidth = 1.5 if aspect_type in ['conjunction', 'opposition'] else 0.8
                alpha = 0.6 if aspect_type in ['trine', 'sextile'] else 0.4

                # ציור קו בין הפלנטות דרך המרכז
                inner_radius = 0.45

                ax.plot([x1 * (inner_radius / 0.85), x2 * (inner_radius / 0.85)],
                        [y1 * (inner_radius / 0.85), y2 * (inner_radius / 0.85)],
                        color=color, linewidth=linewidth, alpha=alpha, zorder=1)


def draw_houses(ax, houses_data, ascendant_degree):
    """
    מצייר קווי בתים (Houses)
    :param ax: ציר matplotlib
    :param houses_data: מילון נתוני הבתים
    :param ascendant_degree: מעלת האופק (לחישוב מיקום נכון)
    """
    if not houses_data:
        print("⚠️ אין נתוני בתים לציור")
        return

    print(f"🏠 מצייר {len(houses_data)} בתים...")

    for house_num in range(1, 13):
        house_key = f'בית {house_num}'
        if house_key not in houses_data:
            print(f"⚠️ חסר מפתח: {house_key}")
            continue

        house_info = houses_data[house_key]
        cusp_deg = house_info.get('cusp_deg', None)

        if cusp_deg is None:
            print(f"⚠️ אין cusp_deg לבית {house_num}")
            continue

        # המרת זווית אסטרולוגית למערכת הציור
        chart_angle = convert_to_chart_angle(cusp_deg, ascendant_degree)
        angle_rad = np.deg2rad(chart_angle)

        # ציור קו מהמרכז ועד לטבעת הפנימית
        x_outer = 0.75 * np.cos(angle_rad)
        y_outer = 0.75 * np.sin(angle_rad)

        # בתים מיוחדים (1, 4, 7, 10) יהיו עבים יותר
        is_angular_house = house_num in [1, 4, 7, 10]
        linewidth = 2.5 if is_angular_house else 1.0

        ax.plot([0, x_outer], [0, y_outer],
                color='#000000', linewidth=linewidth, alpha=0.9, zorder=20, solid_capstyle='round')

        # הוספת מספר הבית בצד החיצוני של הקו
        text_radius = 0.65
        x_text = text_radius * np.cos(angle_rad)
        y_text = text_radius * np.sin(angle_rad)

        ax.text(x_text, y_text, str(house_num),
                fontsize=10, ha='center', va='center',
                color='#000000', fontweight='bold', zorder=21,
                bbox=dict(boxstyle='circle,pad=0.12', facecolor='white',
                          edgecolor='#000000', linewidth=1.2, alpha=0.95))

    print(f"✅ {len(houses_data)} קווי בתים צוירו בהצלחה")


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


def draw_and_save_chart(chart_data: dict, user_obj, output_path: str):
    """
    מצייר גלגל מפת לידה משופר ושומר אותו כתמונה.

    :param chart_data: מילון נתוני המפה (Planets, HouseCusps, Aspects)
    :param user_obj: אובייקט ה-User המכיל את הפרטים (שם, תאריך, מיקום)
    :param output_path: הנתיב המלא לשמירת קובץ התמונה
    """
    try:
        # ============ DEBUG: בדיקה מה יש ב-chart_data ============
        print("\n🔍 DEBUG - תוכן chart_data:")
        print(f"Keys ברמה ראשונה: {chart_data.keys()}")

        # ✅ תיקון: שימוש במפתחות הנכונים
        planets_data = chart_data.get('Planets', {})
        house_cusps = chart_data.get('HouseCusps', {})
        aspects_list = chart_data.get('Aspects', [])

        print(f"\n📊 Planets: {len(planets_data)} פלנטות נמצאו")
        print(f"🏠 HouseCusps: {len(house_cusps)} יתדות נמצאו")
        print(f"🔗 Aspects: {len(aspects_list)} אספקטים נמצאו")

        if planets_data:
            print(f"דוגמה לפלנטה: {list(planets_data.keys())[0]} = {planets_data[list(planets_data.keys())[0]]}")

        print("\n" + "=" * 50 + "\n")
        # ============ END DEBUG ============

        user_name = user_obj.name
        birthdate = user_obj.birthdate
        birthtime = user_obj.birthtime if user_obj.birthtime else "לא ידוע"

        # חילוץ מעלת האופק - DEBUG
        print(f"🔍 סוג house_cusps: {type(house_cusps)}")
        print(f"🔍 תוכן house_cusps: {house_cusps}")

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

        print(f"🎯 מעלת האופק: {ascendant_degree:.2f}°")

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

        # טבעת פנימית - אספקטים (0.5)
        circle_inner = plt.Circle((0, 0), 0.5, color='#7F8C8D', fill=False, linewidth=1.0)
        ax.add_artist(circle_inner)

        # מעגל מרכזי
        circle_center = plt.Circle((0, 0), 0.05, color='#2C3E50', fill=True)
        ax.add_artist(circle_center)

        # =====================================
        # 2. ציור קווי בתים (Houses) - לפני המזלות!
        # =====================================

        # ✅ בניית מבנה houses_data מ-HouseCusps
        houses_data_formatted = {}
        if house_cusps:
            if isinstance(house_cusps, dict):
                for house_num in range(1, 13):
                    if house_num in house_cusps:
                        cusp_value = house_cusps[house_num]
                        if isinstance(cusp_value, (list, tuple)):
                            cusp_deg = float(cusp_value[0])
                        else:
                            cusp_deg = float(cusp_value)
                        houses_data_formatted[f'בית {house_num}'] = {'cusp_deg': cusp_deg}
            elif isinstance(house_cusps, (list, tuple)):
                for house_num in range(1, min(13, len(house_cusps))):
                    cusp_value = house_cusps[house_num]
                    if isinstance(cusp_value, (list, tuple)):
                        cusp_deg = float(cusp_value[0])
                    else:
                        cusp_deg = float(cusp_value)
                    houses_data_formatted[f'בית {house_num}'] = {'cusp_deg': cusp_deg}

        draw_houses(ax, houses_data_formatted, ascendant_degree)

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
            ax.text(x_label * 1.08, y_label * 1.08, zodiac_name_fixed, fontsize=8,
                    ha='center', va='center', color='#34495E', zorder=3)

        # =====================================
        # 4. הכנת נתוני פלנטות למיקום
        # =====================================

        # המרה לזוויות במערכת הציור
        planets_chart_angles = {}
        planets_original_lon = {}  # שמירת המעלות המקוריות לאספקטים

        for name, data in planets_data.items():
            if 'lon_deg' in data and data['lon_deg'] is not None:
                original_lon = data['lon_deg']
                chart_angle = convert_to_chart_angle(original_lon, ascendant_degree)
                planets_chart_angles[name] = chart_angle
                planets_original_lon[name] = original_lon

        print(f"🌟 מכין {len(planets_chart_angles)} פלנטות לציור")

        adjusted_positions = avoid_planet_overlap(planets_chart_angles, min_separation=10)

        # =====================================
        # 5. ציור הפלנטות
        # =====================================

        planet_radius = 0.85
        planets_positions = {}  # לשמירת מיקומים לאספקטים

        for planet_name, planet_data in planets_data.items():
            if 'lon_deg' not in planet_data or planet_data['lon_deg'] is None or planet_name in ['אופק (AC)', 'רום שמיים (MC)']:
                continue

            original_lon = planet_data['lon_deg']
            chart_angle = planets_chart_angles[planet_name]
            adjusted_chart_angle = adjusted_positions.get(planet_name, chart_angle)

            angle_rad = np.deg2rad(adjusted_chart_angle)

            x = planet_radius * np.cos(angle_rad)
            y = planet_radius * np.sin(angle_rad)

            symbol = PLANET_SYMBOLS.get(planet_name, planet_name[:2])

            # ציור סמל הפלנטה
            ax.text(x, y, symbol, fontsize=16, ha='center', va='center',
                    color='#E74C3C', fontweight='bold', zorder=15,
                    family='DejaVu Sans',
                    bbox=dict(boxstyle='circle,pad=0.2', facecolor='white',
                              edgecolor='#E74C3C', linewidth=1.5))

            # מעלות המזל
            sign_deg = original_lon % 30
            sign_name = ZODIAC_NAMES.get((original_lon // 30) * 30, '')
            degree_text = f"{sign_deg:.0f}°"

            # טקסט מעלות (קצת יותר רחוק)
            text_radius_deg = 1.05
            x_deg = text_radius_deg * np.cos(angle_rad)
            y_deg = text_radius_deg * np.sin(angle_rad)

            ax.text(x_deg, y_deg, degree_text, fontsize=8,
                    ha='center', va='center', color='#2C3E50', zorder=14,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#ECF0F1',
                              edgecolor='none', alpha=0.8))

            # שמירת מיקום לאספקטים (עם המעלה המקורית)
            planets_positions[planet_name] = (x, y, original_lon)

        print(f"✅ {len(planets_positions)} פלנטות צוירו בהצלחה")

        # =====================================
        # 6. ציור אספקטים
        # =====================================

        draw_aspect_lines(ax, planets_positions, orb=8)

        # =====================================
        # 7. מקרא (Legend)
        # =====================================

        legend_lines = [
            "אספקטים:",
            "● צמידות )0°( - אדום",
            "● ניגוד )180°( - כחול",
            "● משולש )120°( - ירוק",
            "● ריבוע )90°( - כתום",
            "● משושה )60°( - סגול"
        ]

        legend_text = "\n".join([fix_hebrew_text(line) for line in legend_lines])

        ax.text(-1.25, -1.15, legend_text, fontsize=9, ha='left', va='top',
                color='#2C3E50',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                          edgecolor='#2C3E50', linewidth=1, alpha=0.9))

        # =====================================
        # 8. כותרת ופרטי לידה
        # =====================================

        title_text = fix_hebrew_text(f"מפת לידה - {user_name}")
        subtitle_text = fix_hebrew_text(f"תאריך לידה: {birthdate} | שעה: {birthtime}")

        plt.text(0, 1.22, title_text, fontsize=18, ha='center',
                 fontweight='bold', color='#2C3E50')
        plt.text(0, 1.15, subtitle_text, fontsize=11, ha='center',
                 color='#34495E')

        # =====================================
        # 9. שמירת התמונה
        # =====================================

        plt.savefig(output_path, bbox_inches='tight', dpi=150, facecolor='#F5F5DC')
        plt.close()

        print(f"✅ מפת לידה משופרת נוצרה ונשמרה ב: {output_path}")

    except Exception as e:
        import traceback
        print(f"❌ אירעה שגיאה בציור המפה: {e}")
        traceback.print_exc()

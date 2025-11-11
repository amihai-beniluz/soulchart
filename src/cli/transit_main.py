"""
סקריפט CLI לחישוב וניתוח טרנזיטים אסטרולוגיים.
"""
import os
import sys
from datetime import datetime, timedelta
import traceback

# הוספת src לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from user import User
from birth_chart_analysis.ChartAnalysis import ChartAnalysis
from birth_chart_analysis.TransitCalculator import TransitCalculator
from birth_chart_analysis.CalculationEngine import calculate_chart_positions, calculate_current_positions
from birth_chart_analysis.BirthChartDrawer import draw_and_save_biwheel_chart
from core import (
    write_results_to_file,
    get_validated_date,
    get_validated_time,
    get_location_input,
    get_interpretation_choice
)

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
TRANSITS_DIR = os.path.join(PROJECT_DIR, 'output', 'transits')


def get_birth_data_input():
    """אוסף את נתוני הלידה הנדרשים (תאריך, שעה, מיקום)."""
    print("\n--- איסוף נתוני לידה (נטאל) ---\n")

    name = input("הכנס שם המשתמש (לצורך שמירת הקובץ): ").strip() or "User"
    birthdate = get_validated_date("הכנס תאריך לידה (פורמט YYYY-MM-DD): ")
    birthtime = get_validated_time("הכנס שעת לידה (פורמט HH:MM): ", is_optional=False)

    print("\n--- נתוני מיקום לידה ---")
    location = get_location_input(
        single_prompt="הכנס את מקום הלידה (Latitude, Longitude): "
    )

    user = User(name, birthdate, birthtime, location)
    return user


def get_current_location_input():
    """אוסף את נתוני המיקום הנוכחי."""
    print("\n--- איסוף מיקום נוכחי ---\n")
    return get_location_input(
        single_prompt="הכנס מיקום נוכחי (Latitude, Longitude): "
    )


def get_mode_selection():
    """בחירת מצב הרצה."""
    print("\n" + "=" * 80)
    print("בחר מצב הרצה:")
    print("=" * 80)
    print("1. ניתוח טרנזיטים נוכחיים")
    print("2. חישוב טרנזיטים עתידיים")
    print("=" * 80)

    while True:
        choice = input("\nהכנס בחירה (1/2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("❌ בחירה לא תקינה. אנא הזן 1 או 2")


def run_current_transits(user: User, current_location: tuple, is_interpreted: bool = True):
    """מצב 1: ניתוח טרנזיטים נוכחיים"""
    print("\n--- ביצוע ניתוח מעברים נוכחיים ---\n")
    try:
        chart_analysis = ChartAnalysis(user)

        birth_datetime = datetime.combine(user.birthdate, user.birthtime)
        natal_chart_data = calculate_chart_positions(
            birth_datetime,
            user.location[0],
            user.location[1]
        )

        current_datetime = datetime.now()
        transit_chart_data = calculate_current_positions(
            current_datetime,
            current_location[0],
            current_location[1]
        )

        transit_result = chart_analysis.analyze_transits_and_aspects(
            current_location,
            is_interpreted=is_interpreted
        )

        suffix = "_interpreted" if is_interpreted else "_positions"
        birth_time_str = user.birthtime.strftime('%H-%M')
        filename_prefix = f"Natal_{user.birthdate}_at_{birth_time_str}_Transit_to_{current_datetime.strftime('%Y-%m-%d_%H-%M')}{suffix}"

        write_results_to_file(TRANSITS_DIR, filename_prefix, transit_result, ".txt")

        image_filename = os.path.join(TRANSITS_DIR, f"{filename_prefix}_biwheel.png")
        draw_and_save_biwheel_chart(
            natal_chart_data,
            transit_chart_data,
            user,
            current_datetime,
            image_filename
        )

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בניתוח טרנזיטים נוכחיים: {e}")
        traceback.print_exc()


def run_future_transits(user: User, current_location: tuple, is_interpreted: bool = True):
    """מצב 2: חישוב טרנזיטים עתידיים"""
    print("\n--- חישוב טרנזיטים עתידיים ---\n")

    days_str = input("כמה ימים קדימה לחשב? (ברירת מחדל: 30): ").strip()
    try:
        days_ahead = int(days_str) if days_str else 30
    except ValueError:
        print("⚠️ ערך לא תקין, משתמש ב-30 ימים")
        days_ahead = 30

    print("\n" + "=" * 80)
    print("בחר סוג מיון:")
    print("=" * 80)
    print("1. לפי משך זמן ההיבט (מהקצר לארוך)")
    print("2. כרונולוגי לפי רגע תחילת ההיבט")
    print("3. כרונולוגי לפי אירועים (מומלץ!)")
    print("=" * 80)

    while True:
        sort_choice = input("\nהכנס בחירה (1/2/3, ברירת מחדל: 1): ").strip()
        if sort_choice in ['1', '2', '3', '']:
            break
        print("❌ בחירה לא תקינה")

    sort_mode_map = {'1': 'duration', '2': 'chronological', '3': 'events', '': 'duration'}
    sort_mode = sort_mode_map[sort_choice if sort_choice else '']

    try:
        calculator = TransitCalculator(user)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)

        print(f"\n⏳ מחשב טרנזיטים ל-{days_ahead} ימים קדימה...")
        result = calculator.calculate_aspects_in_range(
            start_date,
            end_date,
            current_location
        )

        report_lines = format_future_transits_report(result, sort_mode, is_interpreted)

        suffix = "_interpreted" if is_interpreted else "_positions"
        text_filename = f"future_transits_{user.name}_{datetime.now():%Y%m%d_%H%M}{suffix}.txt"

        write_results_to_file(TRANSITS_DIR, text_filename.replace('.txt', ''), report_lines, ".txt")

    except Exception as e:
        print(f"\n❌ אירעה שגיאה בחישוב טרנזיטים עתידיים: {e}")
        traceback.print_exc()


def format_future_transits_report(result: dict, sort_mode: str, is_interpreted: bool) -> list:
    """
    ממיר את תוצאות ה-TransitCalculator לדוח טקסט קריא ומפורט.
    הותאם לטפל ב-sort_mode (duration, chronological, events).

    :param result: תוצאות החישוב מ-TransitCalculator
    :param sort_mode: מצב המיון הרצוי ('duration', 'chronological', 'events')
    :param is_interpreted: האם להוסיף פרשנות אסטרולוגית
    :return: רשימת שורות לדוח
    """
    from datetime import datetime

    # מיפוי שמות היבטים לעברית
    ASPECTS_HEB = {
        'Conjunction': 'צמוד',
        'Opposition': 'מול',
        'Trine': 'משולש',
        'Square': 'ריבוע',
        'Sextile': 'משושה',
        'Inconjunct': 'קווינקונקס',
        'SemiSextile': 'חצי-משושה',
        'SemiSquare': 'חצי-ריבוע',
        'Sesquiquadrate': 'סקווירפיינד',
        'Quintile': 'קווינטייל',
        'Biquintile': 'ביקווינטייל'
    }

    def format_datetime(iso_str: str) -> str:
        """המרת תאריך לפורמט DD.MM.YYYY HH:MM"""
        if not iso_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime('%d.%m.%Y %H:%M')
        except ValueError:
            return iso_str

    def format_duration_precise(start_str: str, end_str: str) -> str:
        """ממיר משך זמן לפורמט מדויק (שעות/ימים/חודשים)"""
        try:
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)
        except ValueError:
            return "משך לא ידוע"

        total_seconds = (end - start).total_seconds()
        total_hours = total_seconds / 3600
        total_days = total_seconds / (3600 * 24)
        total_months = total_days / 30.5
        total_years = total_days / 365.25

        if total_years >= 1:
            years = int(total_years)
            if years == 1:
                return "שנה"
            return f"{years} שנים"
        elif total_months >= 2:
            months = int(total_months)
            return f"{months} חודשים"
        elif total_months >= 1:
            return "חודש"
        elif total_days >= 2:
            days = int(total_days)
            return f"{days} ימים"
        elif total_days >= 1:
            return "יום"
        elif total_hours >= 2:
            hours = int(total_hours)
            return f"{hours} שעות"
        elif total_hours >= 1:
            return "שעה"
        else:
            minutes = int(total_seconds / 60)
            if minutes <= 1:
                return "דקה"
            return f"{minutes} דקות"

    report = []

    # טעינת נתוני פרשנות אם נדרש
    chart_data = None
    if is_interpreted:
        try:
            from birth_chart_analysis.ChartDataLoaders import load_all_chart_data
            chart_data = load_all_chart_data()
        except ImportError:
            report.append("❌ אירעה שגיאה: מודול ChartDataLoaders אינו מיובא כראוי, לא ניתן לטעון פרשנות.")

    # כותרת ונתוני מטא
    metadata = result.get('metadata', {})
    aspects = result.get('aspects', [])

    if not aspects:
        report.append("⚠️ לא נמצאו היבטי טרנזיט בטווח המבוקש.")
        return report

    interpretation_text = " (עם פרשנות)" if is_interpreted else ""
    report.append("=" * 80)
    report.append(f"=== דוח טרנזיטים עתידיים עבור {metadata.get('user_name', 'המשתמש')}{interpretation_text} ===")
    report.append(f"תאריך לידה: {metadata.get('birth_date', 'N/A')}")
    calculated_at_raw = metadata.get('calculated_at', 'N/A')

    if calculated_at_raw != 'N/A':
        formatted_date = calculated_at_raw.replace('T', ' ').split('.')[0][:16]
    else:
        formatted_date = 'N/A'

    report.append(f"נוצר ב: {formatted_date}")

    range_data = metadata.get('range', ['N/A', 'N/A'])
    start_date_str = range_data[0]
    end_date_str = range_data[1]

    start_date_formatted = format_datetime(start_date_str) if start_date_str != 'N/A' else 'N/A'
    end_date_formatted = format_datetime(end_date_str) if end_date_str != 'N/A' else 'N/A'

    report.append(f"טווח זמנים: {start_date_formatted} - {end_date_formatted}")
    report.append(f"סה\"כ היבטים: {metadata.get('total_aspects', 0)}")
    report.append("")

    # מיון ההיבטים
    if sort_mode == 'chronological':
        aspects = sorted(aspects,
                         key=lambda x: x.get('lifecycle', {}).get('start', '9999-01-01'))
        sort_type_text = "ממוין לפי תאריך התחלה (כרונולוגי)"
    elif sort_mode == 'duration':
        aspects = sorted(aspects,
                         key=lambda x: (
                             (datetime.fromisoformat(x['lifecycle']['end']) -
                              datetime.fromisoformat(x['lifecycle']['start'])).total_seconds()
                             if x.get('lifecycle', {}).get('start') and x.get('lifecycle', {}).get('end')
                             else float('inf')
                         ))
        sort_type_text = "ממוין לפי משך זמן (מהקצר לארוך)"
    else:  # 'events'
        sort_type_text = "ממוין כרונולוגית לפי אירוע (כניסה/שיא/יציאה)"

    report.append("=" * 80)
    report.append(f"רשימת כל ההיבטים העתידיים - {sort_type_text}")
    report.append("=" * 80)
    report.append("")

    # מצב: מיון לפי אירועים (Events)
    if sort_mode == 'events':
        events = []
        for aspect in aspects:
            lifecycle = aspect.get('lifecycle', {})
            aspect_name_heb = ASPECTS_HEB.get(aspect.get('aspect_type', 'N/A'), aspect.get('aspect_type', 'N/A'))
            aspect_line = f"{aspect.get('natal_planet', 'N/A')} (לידה) {aspect_name_heb} {aspect.get('transit_planet', 'N/A')} (מעבר)"

            # יצירת אירועי כניסה, שיא ויציאה
            if lifecycle.get('start'):
                events.append({
                    'date_str': lifecycle['start'],
                    'type': 'כניסה להיבט 🟢',
                    'aspect_line': aspect_line,
                    'aspect_data': aspect
                })

            for exact in lifecycle.get('exact_dates', []):
                retro_marker = " ⟲" if exact.get('is_retrograde') else ""
                events.append({
                    'date_str': exact['date'],
                    'type': f"שיא היבט ⭐{retro_marker}",
                    'aspect_line': aspect_line,
                    'aspect_data': aspect
                })

            if lifecycle.get('end'):
                events.append({
                    'date_str': lifecycle['end'],
                    'type': 'יציאה מהיבט 🔴',
                    'aspect_line': aspect_line,
                    'aspect_data': aspect
                })

        # מיון כל האירועים הכרונולוגיים
        events = sorted(events, key=lambda x: x['date_str'])

        # כתיבת הדוח לפי האירועים
        for event in events:
            report.append(f"📅 {format_datetime(event['date_str'])} - {event['type']}")
            report.append(f"  {event['aspect_line']}")

            # הוספת תקופת פעילות
            aspect_data = event['aspect_data']
            lifecycle = aspect_data.get('lifecycle', {})
            if lifecycle.get('start') and lifecycle.get('end'):
                start_formatted = format_datetime(lifecycle['start'])
                end_formatted = format_datetime(lifecycle['end'])
                duration_str = format_duration_precise(lifecycle['start'], lifecycle['end'])

                passes_suffix = ""
                num_passes = lifecycle.get('num_passes', 0)
                if num_passes > 1:
                    passes_suffix = f", {num_passes} מעברים"

                report.append(f"  תקופת פעילות: {start_formatted} - {end_formatted} ({duration_str}{passes_suffix})")

            # הוספת פרשנות אם נדרש
            if is_interpreted and chart_data:
                analysis_lines = get_interpretation_lines(aspect_data, chart_data)
                report.extend(analysis_lines)
            elif is_interpreted:
                report.append("⚠️ פרשנות לא זמינה או שגיאת טעינה")

            report.append("")

        return report

    # מצבים: מיון לפי משך זמן (duration) ו- chronological
    for i, aspect in enumerate(aspects, 1):
        lifecycle = aspect.get('lifecycle', {})

        # תרגום שם ההיבט לעברית
        aspect_name_heb = ASPECTS_HEB.get(aspect.get('aspect_type', 'N/A'), aspect.get('aspect_type', 'N/A'))
        natal_p = aspect.get('natal_planet', 'N/A')
        transit_p = aspect.get('transit_planet', 'N/A')

        # שורת כותרת ההיבט
        aspect_line = f"{natal_p} (לידה) {aspect_name_heb} {transit_p} (מעבר)"
        report.append(aspect_line)

        # תקופת פעילות
        start_date = lifecycle.get('start')
        end_date = lifecycle.get('end')

        if start_date and end_date:
            start_formatted = format_datetime(start_date)
            end_formatted = format_datetime(end_date)
            duration_str = format_duration_precise(start_date, end_date)

            passes_suffix = ""
            num_passes = lifecycle.get('num_passes', 0)
            if num_passes > 1:
                passes_suffix = f", {num_passes} מעברים"

            report.append(f"    - תקופת פעילות: {start_formatted} - {end_formatted} ({duration_str}{passes_suffix})")
        else:
            report.append(f"    - תקופת פעילות: N/A - N/A (משך לא ידוע)")

        # שיאי ההיבט
        exact_dates = lifecycle.get('exact_dates')
        if exact_dates:
            if len(exact_dates) == 1:
                # שיא בודד
                first_exact = exact_dates[0]
                exact_formatted = format_datetime(first_exact.get('date', 'N/A'))
                retro_marker = " ⟲" if first_exact.get('is_retrograde') else ""
                report.append(f"    - שיא ההיבט: {exact_formatted}{retro_marker}")
            else:
                # מספר שיאים
                report.append(f"    - שיאי ההיבט:")
                for ex in exact_dates:
                    ex_formatted = format_datetime(ex.get('date', 'N/A'))
                    retro_mark = " ⟲" if ex.get('is_retrograde') else ""
                    report.append(f"        {ex_formatted}{retro_mark}")
        else:
            report.append(f"    - שיא ההיבט: N/A")

        # הוספת פרשנות אם נדרש
        if is_interpreted and chart_data:
            analysis_lines = get_interpretation_lines(aspect, chart_data)
            report.extend(analysis_lines)
        elif is_interpreted:
            report.append(f"\n⚠️ פרשנות לא זמינה או שגיאת טעינה")

        report.append("")

        # מפריד כל 10 היבטים
        if i % 10 == 0 and i < len(aspects):
            report.append("-" * 80)
            report.append("")

    return report


def get_interpretation_lines(aspect, chart_data):
    """פונקציית עזר להפקת שורות הפרשנות"""

    PLANET_NAMES_ENG = {
        'שמש': 'Sun', 'ירח': 'Moon', 'מרקורי': 'Mercury',
        'ונוס': 'Venus', 'מאדים': 'Mars', 'צדק': 'Jupiter',
        'שבתאי': 'Saturn', 'אורנוס': 'Uranus', 'נפטון': 'Neptune',
        'פלוטו': 'Pluto', 'ראש דרקון': 'North Node', 'לילית': 'Lilith',
        'כירון': 'Chiron', 'אופק (AC)': 'AC', 'רום שמיים (MC)': 'MC',
        'פורטונה': 'Fortune', 'ורטקס': 'Vertex'
    }

    natal_p = aspect.get('natal_planet', 'N/A')
    transit_p = aspect.get('transit_planet', 'N/A')
    aspect_name_eng = aspect.get('aspect_type', 'N/A')

    p1_eng = PLANET_NAMES_ENG.get(natal_p, natal_p)
    p2_eng = PLANET_NAMES_ENG.get(transit_p, transit_p)

    # המפתח הוא בפורמט: Natal Sun Conjunction Transit Jupiter
    key = f"Natal {p1_eng} {aspect_name_eng} Transit {p2_eng}"
    aspects_transit_data = chart_data.get('aspects_transit', {})
    analysis = aspects_transit_data.get(key)

    lines = []
    if analysis:
        lines.append(f"\n📖 פרשנות:\n{analysis}")
    else:
        lines.append(f"\n⚠️ פרשנות להיבט זה לא נמצאה במאגר (מפתח: {key})")

    return lines


def main():
    """נקודת הכניסה הראשית."""
    print("\n" + "=" * 80)
    print("🌍 מערכת ניתוח טרנזיטים אסטרולוגיים")
    print("=" * 80)

    user = get_birth_data_input()
    current_location = get_current_location_input()

    mode = get_mode_selection()
    is_interpreted = get_interpretation_choice()

    if mode == '1':
        run_current_transits(user, current_location, is_interpreted)
    else:
        run_future_transits(user, current_location, is_interpreted)


if __name__ == "__main__":
    main()

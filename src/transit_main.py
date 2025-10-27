import os
from datetime import datetime, timedelta
import traceback
import json

# ייבוא מהחבילות
from user import User
from birth_chart_analysis.ChartAnalysis import ChartAnalysis
from birth_chart_analysis.TransitCalculator import TransitCalculator  # ← חדש!
from utils import write_results_to_file, get_validated_date, get_validated_time
from birth_chart_analysis.CalculationEngine import calculate_chart_positions, calculate_current_positions
from birth_chart_analysis.BirthChartDrawer import draw_and_save_biwheel_chart

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir))
TRANSITS_DIR = os.path.join(PROJECT_DIR, os.path.join('output', 'transits'))


def get_birth_data_input():
    """אוסף את נתוני הלידה הנדרשים (תאריך, שעה, מיקום)."""
    print("\n--- איסוף נתוני לידה (נטאל) ---\n")

    name = input("הכנס שם המשתמש (לצורך שמירת הקובץ): ").strip() or "User"
    birthdate = get_validated_date("הכנס תאריך לידה (פורמט YYYY-MM-DD): ")
    birthtime = get_validated_time("הכנס שעת לידה (פורמט HH:MM): ", is_optional=False)

    print("\n--- נתוני מיקום לידה ---")
    try:
        location_str = input("הכנס את מקום הלידה (Latitude, Longitude): ").strip()
        lat_str, lon_str = location_str.split(',')
        latitude = float(lat_str.strip())
        longitude = float(lon_str.strip())
        location = (latitude, longitude)
    except ValueError:
        print("❌ פורמט מיקום לא תקין. אנא הזן מחדש.")
        return get_birth_data_input()

    user = User(name, birthdate, birthtime, location)
    return user


def get_current_location_input():
    """אוסף את נתוני המיקום הנוכחי."""
    print("\n--- איסוף מיקום נוכחי ---\n")

    while True:
        try:
            location_str = input("הכנס מיקום נוכחי (Latitude, Longitude): ").strip()
            lat_str, lon_str = location_str.split(',')
            latitude = float(lat_str.strip())
            longitude = float(lon_str.strip())
            return (latitude, longitude)
        except ValueError:
            print("❌ פורמט מיקום לא תקין. אנא הזן מחדש.")


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


def run_current_transits(user: User, current_location: tuple):
    """מצב 1: ניתוח טרנזיטים נוכחיים (כמו הקוד המקורי)"""
    print("\n--- ביצוע ניתוח מעברים נוכחיים ---\n")
    try:
        chart_analysis = ChartAnalysis(user)

        # נתוני נטאל גולמיים
        birth_datetime = datetime.combine(user.birthdate, user.birthtime)
        natal_chart_data = calculate_chart_positions(
            birth_datetime,
            user.location[0],
            user.location[1]
        )

        # נתוני מעבר גולמיים
        current_datetime = datetime.now()
        transit_chart_data = calculate_current_positions(
            current_datetime,
            current_location[0],
            current_location[1]
        )

        # ניתוח טקסטואלי
        transit_result = chart_analysis.analyze_transits_and_aspects(current_location, is_interpreted=True)

        # שמירה
        birth_time_str = user.birthtime.strftime('%H-%M') if user.birthtime else 'Unknown'
        filename_prefix = f"Natal_{user.birthdate}_at_{birth_time_str}_Transit_to_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"

        write_results_to_file(TRANSITS_DIR, filename_prefix, transit_result, ".txt")

        # ציור Bi-Wheel
        image_filename = os.path.join(TRANSITS_DIR, f"{filename_prefix}_biwheel.png")
        draw_and_save_biwheel_chart(
            natal_chart_data,
            transit_chart_data,
            user,
            current_datetime,
            image_filename
        )

        print("✅ ניתוח טרנזיטים נוכחיים הסתיים!")

    except Exception as e:
        print(f"\n❌ שגיאה בניתוח מעברים נוכחיים: {e}")
        traceback.print_exc()


def format_duration(start_str: str, end_str: str) -> str:
    """ממיר משך זמן לפורמט קריא (שנים/ימים/שעות)."""
    start = datetime.fromisoformat(start_str)
    end = datetime.fromisoformat(end_str)

    total_seconds = (end - start).total_seconds()
    total_hours = total_seconds / 3600
    total_days = total_seconds / (3600 * 24)
    total_years = total_days / 365.25

    if total_years >= 1:
        years = total_years
        if years >= 2:
            return f"{years:.1f} שנים"
        else:
            return f"{years:.1f} שנה"
    elif total_days >= 1:
        days = int(total_days)
        if days == 1:
            return "יום אחד"
        elif days == 2:
            return "יומיים"
        else:
            return f"{days} ימים"
    else:
        hours = int(total_hours)
        if hours == 0:
            minutes = int(total_seconds / 60)
            return f"{minutes} דקות"
        elif hours == 1:
            return "שעה אחת"
        elif hours == 2:
            return "שעתיים"
        else:
            return f"{hours} שעות"


def format_future_transits_report(result: dict) -> list:
    """
    ממיר את תוצאות ה-JSON לדוח טקסט קריא.
    פורמט: פלוטו (לידה) חצי-משושה ירח (מעבר)
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
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%d.%m.%Y %H:%M')

    def format_duration_precise(start_str: str, end_str: str) -> str:
        """ממיר משך זמן לפורמט מדויק (שעות/ימים/חודשים)"""
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)

        total_seconds = (end - start).total_seconds()
        total_hours = total_seconds / 3600
        total_days = total_seconds / (3600 * 24)
        total_months = total_days / 30.5

        if total_months >= 2:
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

    # כותרת
    metadata = result['metadata']
    report.append(f"=== טרנזיטים עתידיים עבור {metadata['user_name']} ===")
    report.append(f"תאריך לידה: {metadata['birth_date']}")
    report.append(f"נוצר ב: {metadata['calculated_at'][:19]}")

    start_date = datetime.fromisoformat(metadata['range'][0])
    end_date = datetime.fromisoformat(metadata['range'][1])
    report.append(f"טווח: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
    report.append(f"סה\"כ היבטים: {metadata['total_aspects']}")
    report.append("")

    # מיון ההיבטים לפי משך הזמן (מהקצר לארוך)
    aspects = sorted(result['aspects'],
                     key=lambda x: (
                         (datetime.fromisoformat(x['lifecycle']['end']) -
                          datetime.fromisoformat(x['lifecycle']['start'])).total_seconds()
                         if x['lifecycle']['start'] and x['lifecycle']['end']
                         else float('inf')
                     ))

    report.append("=" * 80)
    report.append("רשימת כל ההיבטים העתידיים")
    report.append("=" * 80)
    report.append("")

    for i, aspect in enumerate(aspects, 1):
        lifecycle = aspect['lifecycle']

        # תרגום שם ההיבט לעברית
        aspect_name_heb = ASPECTS_HEB.get(aspect['aspect_type'], aspect['aspect_type'])

        # שורת כותרת ההיבט - פורמט חדש
        aspect_line = f"{aspect['natal_planet']} (לידה) {aspect_name_heb} {aspect['transit_planet']} (מעבר)"
        report.append(aspect_line)

        # תקופת פעילות עם שעות
        if lifecycle['start'] and lifecycle['end']:
            start_formatted = format_datetime(lifecycle['start'])
            end_formatted = format_datetime(lifecycle['end'])
            duration_str = format_duration_precise(lifecycle['start'], lifecycle['end'])

            passes_suffix = ""
            if lifecycle['num_passes'] > 1:
                passes_suffix = f", {lifecycle['num_passes']} מעברים"

            report.append(f"    - תקופת פעילות: {start_formatted} - {end_formatted} ({duration_str}{passes_suffix})")

        # שיא ההיבט (Exact הראשון)
        if lifecycle['exact_dates']:
            first_exact = lifecycle['exact_dates'][0]
            exact_formatted = format_datetime(first_exact['date'])
            retro_marker = " ⟲" if first_exact['is_retrograde'] else ""

            report.append(f"    - שיא ההיבט: {exact_formatted}{retro_marker}")

            # אם יש יותר מ-exact אחד, הוסף את השאר
            if len(lifecycle['exact_dates']) > 1:
                other_exacts = []
                for ex in lifecycle['exact_dates'][1:]:
                    ex_formatted = format_datetime(ex['date'])
                    retro_mark = " ⟲" if ex['is_retrograde'] else ""
                    other_exacts.append(f"{ex_formatted}{retro_mark}")

                report.append(f"    - שיאים נוספים: {', '.join(other_exacts)}")

        report.append("")

        # מפריד כל 10 היבטים
        if i % 10 == 0 and i < len(aspects):
            report.append("-" * 80)
            report.append("")

    return report

def run_future_transits(user: User, current_location: tuple):
    """מצב 2: חישוב טרנזיטים עתידיים"""
    print("\n--- חישוב טרנזיטים עתידיים ---\n")

    # שאל כמה ימים קדימה
    while True:
        try:
            days_str = input("כמה ימים קדימה לחשב? (ברירת מחדל: 30): ").strip()
            days_ahead = int(days_str) if days_str else 30
            if days_ahead > 0:
                break
            print("❌ יש להזין מספר חיובי")
        except ValueError:
            print("❌ יש להזין מספר שלם")

    try:
        # יצירת מחשבון
        calculator = TransitCalculator(user)

        # חישוב
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)

        print(f"\n🔍 מחשב טרנזיטים מ-{start_date:%Y-%m-%d} עד {end_date:%Y-%m-%d}...")

        result = calculator.calculate_aspects_in_range(
            start_date,
            end_date,
            current_location
        )

        # הצגת סיכום
        print(f"\n📊 נמצאו {result['metadata']['total_aspects']} היבטים!")

        # הצגת 10 האירועים הבאים
        print("\n📅 10 האירועים הקרובים ביותר:")
        print("-" * 80)

        events = calculator.get_next_events(
            from_date=start_date,
            days_ahead=days_ahead,
            limit=10
        )

        for i, event in enumerate(events, 1):
            date_str = datetime.fromisoformat(event['date']).strftime('%d.%m.%Y %H:%M')
            print(f"{i}. [{event['event_type']}] {date_str}")
            print(f"   {event['description']}")

        # שמירה כקובץ טקסט
        text_filename = f"future_transits_{user.name}_{datetime.now():%Y%m%d_%H%M}.txt"
        text_filepath = os.path.join(TRANSITS_DIR, text_filename)

        report_lines = format_future_transits_report(result)  # ✅ המרה לשורות טקסט
        with open(text_filepath, 'w', encoding='utf-8') as f:
            for line in report_lines:
                f.write(line + "\n")

        print(f"✅ דוח טקסט נשמר ב: {text_filepath}")

    except Exception as e:
        print(f"\n❌ שגיאה בחישוב טרנזיטים עתידיים: {e}")
        traceback.print_exc()


def main():
    # איסוף נתוני משתמש
    user = get_birth_data_input()
    current_location = get_current_location_input()

    # בחירת מצב
    mode = get_mode_selection()

    # הרצה לפי הבחירה
    if mode == '1':
        run_current_transits(user, current_location)
    elif mode == '2':
        run_future_transits(user, current_location)
    elif mode == '3':
        run_current_transits(user, current_location)
        run_future_transits(user, current_location)

    print("\n🎉 הסתיים בהצלחה!")


if __name__ == '__main__':
    os.makedirs(TRANSITS_DIR, exist_ok=True)
    main()
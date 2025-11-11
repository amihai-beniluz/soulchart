"""
Handler לניתוח טרנזיטים בבוט הטלגרם - תואם ללוגיקה של הבוט הישן.
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# הוספת src לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from user import User
from birth_chart_analysis.ChartAnalysis import ChartAnalysis
from birth_chart_analysis.TransitCalculator import TransitCalculator
from birth_chart_analysis.CalculationEngine import calculate_chart_positions, calculate_current_positions
from birth_chart_analysis.BirthChartDrawer import draw_and_save_biwheel_chart
from bot.bot_utils import save_user_input, get_main_menu_keyboard, get_user_profile, save_user_profile

logger = logging.getLogger(__name__)

# מצבי שיחה - ממשיכים מאחרי CHART_INTERPRETATION (7)
TRANSIT_NAME = 8
TRANSIT_BIRTH_DATE = 9
TRANSIT_BIRTH_TIME = 10
TRANSIT_BIRTH_LOCATION = 11
TRANSIT_CURRENT_LOCATION = 12
TRANSIT_MODE = 13
TRANSIT_INTERPRETATION = 14
TRANSIT_FUTURE_DAYS = 15
TRANSIT_FUTURE_SORT = 16
MAIN_MENU = 0

# נתיב לשמירת תוצאות
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
TRANSITS_DIR = os.path.join(PROJECT_DIR, 'output', 'transits')


# ============================================================================
# פונקציות עזר לעיצוב דוח
# ============================================================================

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

    key = f"Natal {p1_eng} {aspect_name_eng} Transit {p2_eng}"
    aspects_transit_data = chart_data.get('aspects_transit', {})
    analysis = aspects_transit_data.get(key)

    lines = []
    if analysis:
        lines.append(f"\n📖 פרשנות:\n{analysis}")
    else:
        lines.append(f"\n⚠️ פרשנות להיבט זה לא נמצאה במאגר (מפתח: {key})")

    return lines


def format_future_transits_report(result: dict, sort_mode: str, is_interpreted: bool) -> list:
    """
    ממיר את תוצאות ה-TransitCalculator לדוח טקסט קריא ומפורט.

    :param result: תוצאות החישוב מ-TransitCalculator
    :param sort_mode: מצב המיון הרצוי ('duration', 'chronological', 'events')
    :param is_interpreted: האם להוסיף פרשנות אסטרולוגית
    :return: רשימת שורות לדוח
    """

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


# ============================================================================
# Handlers - זהה לבוט הישן
# ============================================================================

async def transit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מתחיל תהליך טרנזיטים - מותאם לבוט הישן"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    # אם יש פרופיל - עוברים ישירות למיקום נוכחי
    if profile:
        context.user_data['transit_name'] = profile['name']
        context.user_data['transit_birthdate'] = profile['birthdate']
        context.user_data['transit_birthtime'] = profile['birthtime']
        context.user_data['transit_birth_location'] = profile['birth_location']

        await query.edit_message_text(
            f"🌍 *מפת מעברים (טרנזיטית)*\n\n"
            f"✅ משתמש מזוהה: *{profile['name']}*\n"
            f"📅 {profile['birthdate']} | ⏰ {profile['birthtime']}\n"
            f"📍 לידה: {profile['birth_location'][0]}°, {profile['birth_location'][1]}°\n\n"
            "כעת הזן את המיקום הנוכחי שלך:\n"
            "`Latitude, Longitude`\n\n"
            "לדוגמה: `32.08, 34.78`\n"
            "(אם אתה באותו מקום, שלח את אותן קואורדינטות)",
            parse_mode='Markdown'
        )
        return TRANSIT_CURRENT_LOCATION
    else:
        # אין פרופיל - מתחילים מאיסוף נתונים
        await query.edit_message_text(
            "🌍 *מפת מעברים (טרנזיטית)*\n\n"
            "ניתוח אסטרולוגי של המעברים הנוכחיים או העתידיים.\n\n"
            "נתחיל באיסוף נתוני הלידה שלך.\n"
            "אנא שלח את השם המלא:",
            parse_mode='Markdown'
        )
        return TRANSIT_NAME


async def transit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל שם"""
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("❌ השם לא יכול להיות ריק. נסה שוב:")
        return TRANSIT_NAME

    context.user_data['transit_name'] = name

    await update.message.reply_text(
        f"✅ שם התקבל: *{name}*\n\n"
        "כעת הזן את תאריך הלידה בפורמט:\n"
        "`YYYY-MM-DD`\n\n"
        "לדוגמה: `1990-05-15`",
        parse_mode='Markdown'
    )
    return TRANSIT_BIRTH_DATE


async def transit_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל תאריך לידה"""
    date_str = update.message.text.strip()

    try:
        birthdate = datetime.strptime(date_str, "%Y-%m-%d").date()
        context.user_data['transit_birthdate'] = birthdate

        await update.message.reply_text(
            f"✅ תאריך התקבל: *{birthdate}*\n\n"
            "כעת הזן את שעת הלידה בפורמט:\n"
            "`HH:MM`\n\n"
            "לדוגמה: `14:30`",
            parse_mode='Markdown'
        )
        return TRANSIT_BIRTH_TIME

    except ValueError:
        await update.message.reply_text(
            "❌ פורמט תאריך לא תקין!\n"
            "אנא הזן בפורמט: `YYYY-MM-DD`\n"
            "לדוגמה: `1990-05-15`",
            parse_mode='Markdown'
        )
        return TRANSIT_BIRTH_DATE


async def transit_birth_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל שעת לידה"""
    time_str = update.message.text.strip()

    try:
        birthtime = datetime.strptime(time_str, "%H:%M").time()
        context.user_data['transit_birthtime'] = birthtime

        await update.message.reply_text(
            f"✅ שעה התקבלה: *{birthtime}*\n\n"
            "כעת הזן את מיקום הלידה בפורמט:\n"
            "`Latitude, Longitude`\n\n"
            "לדוגמה: `32.08, 34.78`",
            parse_mode='Markdown'
        )
        return TRANSIT_BIRTH_LOCATION

    except ValueError:
        await update.message.reply_text(
            "❌ פורמט שעה לא תקין!\n"
            "אנא הזן בפורמט: `HH:MM`\n"
            "לדוגמה: `14:30`",
            parse_mode='Markdown'
        )
        return TRANSIT_BIRTH_TIME


async def transit_birth_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל מיקום לידה"""
    location_str = update.message.text.strip()

    try:
        lat_str, lon_str = location_str.split(',')
        latitude = float(lat_str.strip())
        longitude = float(lon_str.strip())

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Coordinates out of range")

        context.user_data['transit_birth_location'] = (latitude, longitude)

        await update.message.reply_text(
            f"✅ מיקום לידה התקבל: *{latitude}°, {longitude}°*\n\n"
            "כעת הזן את המיקום הנוכחי שלך בפורמט:\n"
            "`Latitude, Longitude`\n\n"
            "לדוגמה: `32.08, 34.78`\n"
            "(אם אתה עדיין באותו מקום, שלח את אותם קואורדינטות)",
            parse_mode='Markdown'
        )
        return TRANSIT_CURRENT_LOCATION

    except (ValueError, AttributeError):
        await update.message.reply_text(
            "❌ פורמט מיקום לא תקין!\n"
            "אנא הזן בפורמט: `Latitude, Longitude`\n"
            "לדוגמה: `32.08, 34.78`",
            parse_mode='Markdown'
        )
        return TRANSIT_BIRTH_LOCATION


async def transit_current_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל מיקום נוכחי"""
    location_str = update.message.text.strip()

    try:
        lat_str, lon_str = location_str.split(',')
        latitude = float(lat_str.strip())
        longitude = float(lon_str.strip())

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Coordinates out of range")

        context.user_data['transit_current_location'] = (latitude, longitude)

        # בחירת מצב: נוכחי או עתידי
        keyboard = [
            [InlineKeyboardButton("🌍 טרנזיטים נוכחיים (מה קורה עכשיו)", callback_data="transit_current")],
            [InlineKeyboardButton("🔮 טרנזיטים עתידיים (תחזית)", callback_data="transit_future")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ מיקום נוכחי התקבל: *{latitude}°, {longitude}°*\n\n"
            "כעת בחר את סוג הניתוח:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return TRANSIT_MODE

    except (ValueError, AttributeError):
        await update.message.reply_text(
            "❌ פורמט מיקום לא תקין!\n"
            "אנא הזן בפורמט: `Latitude, Longitude`\n"
            "לדוגמה: `32.08, 34.78`",
            parse_mode='Markdown'
        )
        return TRANSIT_CURRENT_LOCATION


async def transit_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """בחירת מצב"""
    query = update.callback_query
    await query.answer()

    context.user_data['transit_mode'] = query.data

    # בחירת סוג דוח
    keyboard = [
        [InlineKeyboardButton("📖 דוח מפורט עם פרשנות", callback_data="transit_interpreted_yes")],
        [InlineKeyboardButton("📊 רק מיקומים (ללא פרשנות)", callback_data="transit_interpreted_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    mode_text = "טרנזיטים נוכחיים" if query.data == "transit_current" else "טרנזיטים עתידיים"

    await query.edit_message_text(
        f"✅ נבחר: *{mode_text}*\n\n"
        "כעת בחר את סוג הדוח:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return TRANSIT_INTERPRETATION


async def transit_interpretation_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """בחירת סוג דוח"""
    query = update.callback_query
    await query.answer()

    is_interpreted = (query.data == "transit_interpreted_yes")
    context.user_data['transit_is_interpreted'] = is_interpreted

    transit_mode = context.user_data['transit_mode']

    # אם זה טרנזיטים עתידיים - צריך לשאול כמה ימים
    if transit_mode == "transit_future":
        await query.edit_message_text(
            "🔮 *טרנזיטים עתידיים*\n\n"
            "כמה ימים קדימה לחשב?\n"
            "שלח מספר (ברירת מחדל: 30)\n\n"
            "לדוגמה: `30` או `90` או `365`",
            parse_mode='Markdown'
        )
        return TRANSIT_FUTURE_DAYS
    else:
        # טרנזיטים נוכחיים - מתחילים מיד
        await query.edit_message_text(
            "⏳ מחשב טרנזיטים נוכחיים... אנא המתן..."
        )
        return await process_current_transits(query, context)


async def transit_future_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל מספר ימים"""
    days_str = update.message.text.strip()

    try:
        days_ahead = int(days_str) if days_str else 30
        if days_ahead <= 0:
            raise ValueError("Must be positive")

        context.user_data['transit_days'] = days_ahead

        # בחירת מיון
        keyboard = [
            [InlineKeyboardButton("⏱️ לפי משך זמן (קצר→ארוך)", callback_data="sort_duration")],
            [InlineKeyboardButton("📅 כרונולוגי לפי היבט", callback_data="sort_chronological")],
            [InlineKeyboardButton("🎯 כרונולוגי לפי אירועים (מומלץ!)", callback_data="sort_events")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ יחושב עבור *{days_ahead} ימים* קדימה\n\n"
            "כעת בחר איך למיין את התוצאות:\n\n"
            "💡 *מיון לפי אירועים* - מציג ציר זמן מלא\n"
            "עם כל אירוע (כניסה/שיא/יציאה) בנפרד",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return TRANSIT_FUTURE_SORT

    except ValueError:
        await update.message.reply_text(
            "❌ אנא הזן מספר שלם חיובי!\n"
            "לדוגמה: `30` או `90`"
        )
        return TRANSIT_FUTURE_DAYS


async def transit_future_sort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """בחירת מיון ומבצע חישוב"""
    query = update.callback_query
    await query.answer()

    # המרת callback_data ל-sort_mode
    sort_mode_map = {
        'sort_duration': 'duration',
        'sort_chronological': 'chronological',
        'sort_events': 'events'
    }
    sort_mode = sort_mode_map.get(query.data, 'duration')
    context.user_data['transit_sort_mode'] = sort_mode

    await query.edit_message_text(
        "⏳ מחשב טרנזיטים עתידיים... אנא המתן (זה עשוי לקחת מספר שניות)..."
    )

    await process_future_transits(query, context)
    return MAIN_MENU


async def process_current_transits(query, context: ContextTypes.DEFAULT_TYPE):
    """מעבד טרנזיטים נוכחיים"""
    try:
        name = context.user_data['transit_name']
        birthdate = context.user_data['transit_birthdate']
        birthtime = context.user_data['transit_birthtime']
        birth_location = context.user_data['transit_birth_location']
        current_location = context.user_data['transit_current_location']
        is_interpreted = context.user_data['transit_is_interpreted']

        user = User(name, birthdate, birthtime, birth_location)

        birth_datetime = datetime.combine(birthdate, birthtime)
        natal_chart_data = calculate_chart_positions(
            birth_datetime,
            birth_location[0],
            birth_location[1]
        )

        current_datetime = datetime.now()
        transit_chart_data = calculate_current_positions(
            current_datetime,
            current_location[0],
            current_location[1]
        )

        chart_analysis = ChartAnalysis(user)
        transit_result = chart_analysis.analyze_transits_and_aspects(
            current_location,
            is_interpreted=is_interpreted
        )

        suffix = "_interpreted" if is_interpreted else "_positions"
        birth_time_str = birthtime.strftime('%H-%M')
        filename_prefix = f"Natal_{birthdate}_at_{birth_time_str}_Transit_to_{current_datetime.strftime('%Y-%m-%d_%H-%M')}{suffix}"

        report_filename = os.path.join(TRANSITS_DIR, f"{filename_prefix}.txt")
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.writelines([line + '\n' for line in transit_result])

        image_filename = os.path.join(TRANSITS_DIR, f"{filename_prefix}_biwheel.png")
        draw_and_save_biwheel_chart(
            natal_chart_data,
            transit_chart_data,
            user,
            current_datetime,
            image_filename
        )

        report_type = "מפורט עם פרשנות" if is_interpreted else "מיקומים בלבד"

        with open(report_filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                caption=f"✅ *ניתוח טרנזיטים נוכחיים של {name} הושלם!*\n\n"
                        f"📄 סוג דוח: {report_type}\n"
                        f"🌍 מיקום נוכחי: {current_location[0]}°, {current_location[1]}°\n"
                        f"📅 {current_datetime.strftime('%Y-%m-%d %H:%M')}",
                parse_mode='Markdown'
            )

        with open(image_filename, 'rb') as f:
            await query.message.reply_photo(
                photo=f,
                caption=f"🖼️ *מפת Bi-Wheel: נטאל + טרנזיט נוכחי*\n\n"
                        f"🔵 מעגל פנימי: מפת לידה\n"
                        f"🟢 מעגל חיצוני: טרנזיטים נוכחיים",
                parse_mode='Markdown'
            )

        user_id = query.from_user.id
        await query.message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

        # שמירת פרופיל
        save_user_profile(user_id, name, birthdate, birthtime, birth_location)

        save_user_input(user_id, {
            'type': 'current_transits',
            'name': name,
            'birthdate': str(birthdate),
            'birthtime': str(birthtime),
            'birth_location': birth_location,
            'current_location': current_location,
            'interpreted': is_interpreted
        })

    except Exception as e:
        logger.error(f"Error in current transits: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ אירעה שגיאה בחישוב טרנזיטים נוכחיים:\n{str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    context.user_data.clear()
    return MAIN_MENU


async def process_future_transits(query, context: ContextTypes.DEFAULT_TYPE):
    """מעבד טרנזיטים עתידיים"""
    try:
        name = context.user_data['transit_name']
        birthdate = context.user_data['transit_birthdate']
        birthtime = context.user_data['transit_birthtime']
        birth_location = context.user_data['transit_birth_location']
        current_location = context.user_data['transit_current_location']
        is_interpreted = context.user_data['transit_is_interpreted']
        days_ahead = context.user_data['transit_days']
        sort_mode = context.user_data.get('transit_sort_mode', 'duration')

        user = User(name, birthdate, birthtime, birth_location)

        calculator = TransitCalculator(user)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)

        result = calculator.calculate_aspects_in_range(
            start_date,
            end_date,
            current_location
        )

        report_lines = format_future_transits_report(result, sort_mode, is_interpreted)

        suffix = "_interpreted" if is_interpreted else "_positions"
        text_filename = f"future_transits_{name}_{datetime.now():%Y%m%d_%H%M}{suffix}.txt"
        text_filepath = os.path.join(TRANSITS_DIR, text_filename)

        with open(text_filepath, 'w', encoding='utf-8') as f:
            for line in report_lines:
                f.write(line + "\n")

        report_type = "מפורט עם פרשנות" if is_interpreted else "מיקומים בלבד"
        sort_type_map = {
            'duration': 'לפי משך זמן',
            'chronological': 'כרונולוגי (לפי היבט)',
            'events': 'כרונולוגי (לפי אירועים)'
        }
        sort_type = sort_type_map.get(sort_mode, 'לפי משך זמן')

        with open(text_filepath, 'rb') as f:
            await query.message.reply_document(
                document=f,
                caption=f"✅ *תחזית טרנזיטים עתידיים של {name} הושלמה!*\n\n"
                        f"📄 סוג דוח: {report_type}\n"
                        f"📅 טווח: {days_ahead} ימים\n"
                        f"🔢 סה\"כ היבטים: {result['metadata']['total_aspects']}\n"
                        f"📊 מיון: {sort_type}",
                parse_mode='Markdown'
            )

        user_id = query.from_user.id
        await query.message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

        # שמירת פרופיל
        save_user_profile(user_id, name, birthdate, birthtime, birth_location)

        save_user_input(user_id, {
            'type': 'future_transits',
            'name': name,
            'birthdate': str(birthdate),
            'birthtime': str(birthtime),
            'birth_location': birth_location,
            'current_location': current_location,
            'days_ahead': days_ahead,
            'sort_mode': sort_mode,
            'interpreted': is_interpreted
        })

    except Exception as e:
        logger.error(f"Error in future transits: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ אירעה שגיאה בחישוב טרנזיטים עתידיים:\n{str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    context.user_data.clear()
    return MAIN_MENU

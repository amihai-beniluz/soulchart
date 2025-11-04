import os
import logging
import re
from datetime import datetime, timedelta
from io import BytesIO

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

# ייבוא המודולים של SoulChart
from src.name_analysis.NameAnalysis import NameAnalysis
from src.birth_chart_analysis.ChartAnalysis import ChartAnalysis
from src.birth_chart_analysis.BirthChartDrawer import draw_and_save_chart, draw_and_save_biwheel_chart
from src.birth_chart_analysis.CalculationEngine import calculate_chart_positions, calculate_current_positions
from src.birth_chart_analysis.TransitCalculator import TransitCalculator
from src.user import User

# נקה ANSI colors
ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

# הגדרת logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# טעינת משתני סביבה
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# מילון לשמירת פרופילי משתמשים (בזיכרון)
# במציאות - כדאי לשמור ב-DB, אבל לצרכים בסיסיים זה מספיק
user_profiles = {}

# הגדרת מצבי שיחה (Conversation States)
MAIN_MENU, NAME_ANALYSIS_NAME, NAME_ANALYSIS_NIKUD = range(3)
CHART_NAME, CHART_DATE, CHART_TIME, CHART_LOCATION, CHART_INTERPRETATION = range(3, 8)
TRANSIT_NAME, TRANSIT_BIRTH_DATE, TRANSIT_BIRTH_TIME, TRANSIT_BIRTH_LOCATION = range(8, 12)
TRANSIT_CURRENT_LOCATION, TRANSIT_MODE, TRANSIT_INTERPRETATION = range(12, 15)
TRANSIT_FUTURE_DAYS, TRANSIT_FUTURE_SORT = range(15, 17)

# תיקיות פלט
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
NAMES_DIR = os.path.join(OUTPUT_DIR, 'names')
CHARTS_DIR = os.path.join(OUTPUT_DIR, 'charts')
TRANSITS_DIR = os.path.join(OUTPUT_DIR, 'transits')

# יצירת תיקיות אם לא קיימות
os.makedirs(NAMES_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(TRANSITS_DIR, exist_ok=True)


def get_main_menu_keyboard(user_id: int = None):
    """יוצר מקלדת לתפריט הראשי"""
    keyboard = [
        [InlineKeyboardButton("📝 ניתוח שם", callback_data="name_analysis")],
        [InlineKeyboardButton("⭐ מפת לידה אסטרולוגית", callback_data="birth_chart")],
        [InlineKeyboardButton("🌍 מפת מעברים (טרנזיטים)", callback_data="transits")],
    ]

    # אם יש פרופיל שמור - הצג כפתור למחיקה
    if user_id and user_id in user_profiles:
        profile = user_profiles[user_id]
        keyboard.append([InlineKeyboardButton(
            f"🔄 משתמש חדש (נוכחי: {profile['name']})",
            callback_data="new_user"
        )])

    keyboard.append([InlineKeyboardButton("ℹ️ עזרה", callback_data="help")])

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """תגובה לפקודת /start - מציג תפריט ראשי"""
    user_id = update.effective_user.id

    # ניקוי context (במקרה שלחצו /start באמצע תהליך)
    context.user_data.clear()

    # בדיקה אם יש פרופיל שמור
    if user_id in user_profiles:
        profile = user_profiles[user_id]
        welcome_text = (
            "🌌 ברוך שובך ל-SoulChart Bot! 🌌\n\n"
            f"👤 משתמש מזוהה: *{profile['name']}*\n"
            f"📅 תאריך לידה: {profile['birthdate']}\n"
            f"⏰ שעת לידה: {profile['birthtime']}\n"
            f"📍 מיקום לידה: {profile['birth_location'][0]}°, {profile['birth_location'][1]}°\n\n"
            "בחר את סוג הניתוח המבוקש:\n"
            "(לא צריך להזין את הפרטים שוב! 😊)"
        )
    else:
        welcome_text = (
            "🌌 ברוכים הבאים ל-SoulChart Bot! 🌌\n\n"
            "מערכת ניתוח רוחני אינטגרטיבי המשלבת:\n"
            "🔤 קבלה ונומרולוגיה\n"
            "⭐ אסטרולוגיה נטאלית\n"
            "🌍 אסטרולוגיה טרנזיטית\n\n"
            "בחר את סוג הניתוח המבוקש:"
        )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )
    return MAIN_MENU


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מטפל בלחיצות על כפתורים"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if query.data == "new_user":
        # מחיקת פרופיל קיים
        if user_id in user_profiles:
            del user_profiles[user_id]

        await query.edit_message_text(
            "✅ *פרופיל נמחק בהצלחה!*\n\n"
            "עכשיו תוכל להזין נתונים חדשים.\n"
            "לחץ /start להתחלה מחדש.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    elif query.data == "name_analysis":
        await query.edit_message_text(
            "📝 *ניתוח שם קבלי ונומרולוגי*\n\n"
            "אנא שלח את השם בעברית שברצונך לנתח.\n"
            "לדוגמה: עמי",
            parse_mode='Markdown'
        )
        return NAME_ANALYSIS_NAME

    elif query.data == "birth_chart":
        # בדיקה אם יש פרופיל שמור
        if user_id in user_profiles:
            profile = user_profiles[user_id]
            # שמירה בcontext
            context.user_data['chart_name'] = profile['name']
            context.user_data['chart_birthdate'] = profile['birthdate']
            context.user_data['chart_birthtime'] = profile['birthtime']
            context.user_data['chart_location'] = profile['birth_location']

            # קפיצה ישירות לבחירת סוג דוח
            keyboard = [
                [InlineKeyboardButton("📖 דוח מפורט עם פרשנות", callback_data="interpreted_yes")],
                [InlineKeyboardButton("📊 רק מיקומים (ללא פרשנות)", callback_data="interpreted_no")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"⭐ *מפת לידה אסטרולוגית*\n\n"
                f"✅ משתמש מזוהה: *{profile['name']}*\n"
                f"📅 {profile['birthdate']} | ⏰ {profile['birthtime']}\n"
                f"📍 {profile['birth_location'][0]}°, {profile['birth_location'][1]}°\n\n"
                "בחר את סוג הדוח:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return CHART_INTERPRETATION
        else:
            await query.edit_message_text(
                "⭐ *מפת לידה אסטרולוגית*\n\n"
                "נתחיל באיסוף הנתונים שלב אחר שלב.\n\n"
                "אנא שלח את השם המלא:",
                parse_mode='Markdown'
            )
            return CHART_NAME

    elif query.data == "transits":
        # בדיקה אם יש פרופיל שמור
        if user_id in user_profiles:
            profile = user_profiles[user_id]
            # שמירה בcontext
            context.user_data['transit_name'] = profile['name']
            context.user_data['transit_birthdate'] = profile['birthdate']
            context.user_data['transit_birthtime'] = profile['birthtime']
            context.user_data['transit_birth_location'] = profile['birth_location']

            # קפיצה ישירות למיקום נוכחי
            await query.edit_message_text(
                f"🌍 *מפת מעברים (טרנזיטים)*\n\n"
                f"✅ משתמש מזוהה: *{profile['name']}*\n"
                f"📅 {profile['birthdate']} | ⏰ {profile['birthtime']}\n"
                f"📍 לידה: {profile['birth_location'][0]}°, {profile['birth_location'][1]}°\n\n"
                "כעת הזן את המיקום הנוכחי שלך:\n"
                "`Latitude, Longitude`\n\n"
                "לדוגמה: `32.08, 34.78`\n"
                "(אם אתה באותו מקום, שלח את אותם קואורדינטות)",
                parse_mode='Markdown'
            )
            return TRANSIT_CURRENT_LOCATION
        else:
            await query.edit_message_text(
                "🌍 *מפת מעברים (טרנזיטים)*\n\n"
                "ניתוח אסטרולוגי של המעברים הנוכחיים או העתידיים.\n\n"
                "נתחיל באיסוף נתוני הלידה שלך.\n"
                "אנא שלח את השם המלא:",
                parse_mode='Markdown'
            )
            return TRANSIT_NAME

    elif query.data == "help":
        help_text = (
            "ℹ️ *מדריך שימוש*\n\n"
            "*ניתוח שם:*\n"
            "1. בחר 'ניתוח שם'\n"
            "2. שלח את השם בעברית\n"
            "3. הזן ניקוד לכל אות (פתח, חיריק, ריק וכו')\n\n"
            "*מפת לידה:*\n"
            "1. בחר 'מפת לידה'\n"
            "2. עקוב אחר ההוראות שלב אחר שלב:\n"
            "   - שם\n"
            "   - תאריך לידה (YYYY-MM-DD)\n"
            "   - שעת לידה (HH:MM)\n"
            "   - מיקום (Latitude, Longitude)\n"
            "   - סוג דוח (עם/בלי פרשנות)\n\n"
            "*מפת מעברים:*\n"
            "1. בחר 'מפת מעברים'\n"
            "2. הזן נתוני לידה (כמו במפת לידה)\n"
            "3. הזן מיקום נוכחי\n"
            "4. בחר מצב: נוכחי או עתידי\n"
            "5. קבל דוח + תמונת Bi-Wheel\n\n"
            "*💡 טיפ:* לאחר שתזין את הפרטים פעם אחת,\n"
            "הם יישמרו ולא תצטרך להזין אותם שוב!\n"
            "כפתור 'משתמש חדש' מאפס את הפרטים.\n\n"
            "לחזרה לתפריט הראשי: /start"
        )
        await query.edit_message_text(help_text, parse_mode='Markdown')
        await query.message.reply_text(
            "בחר פעולה:",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU


# ============================================================================
# ניתוח שם - Name Analysis Flow
# ============================================================================

async def name_analysis_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל את השם לניתוח"""
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("❌ השם לא יכול להיות ריק. נסה שוב:")
        return NAME_ANALYSIS_NAME

    # שמירת השם בהקשר
    context.user_data['name'] = name

    # הסבר על הניקוד עם דוגמה
    example_name = "עֲמִיחַי"
    example_nikud = "פתח חיריק ריק פתח ריק"

    await update.message.reply_text(
        f"✅ שם התקבל: *{name}* ({len(name)} אותיות)\n\n"
        f"כעת שלח את רצף הניקודים להודעה אחת, מופרדים ברווחים.\n\n"
        f"*דוגמה:*\n"
        f"שם: {example_name}\n"
        f"ניקוד: `{example_nikud}`\n\n"
        f"*סוגי ניקוד אפשריים:*\n"
        f"פתח, חיריק, צירה, קמץ, סגול, שווא, חולם, קובוץ, ריק\n\n"
        f"עבור השם *{name}* שלך, שלח {len(name)} ניקודים:",
        parse_mode='Markdown'
    )
    return NAME_ANALYSIS_NIKUD


async def name_analysis_nikud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל את כל הניקודים בבת אחת"""
    nikud_text = update.message.text.strip()
    name = context.user_data['name']

    # פיצול לרשימת ניקודים
    nikud_list = nikud_text.split()

    # ולידציה - בדיקת אורך
    if len(nikud_list) != len(name):
        await update.message.reply_text(
            f"❌ *שגיאה באורך!*\n\n"
            f"השם *{name}* מכיל {len(name)} אותיות,\n"
            f"אבל שלחת {len(nikud_list)} ניקודים.\n\n"
            f"אנא שלח בדיוק {len(name)} ניקודים מופרדים ברווחים.\n"
            f"לדוגמה: `פתח חיריק ריק`",
            parse_mode='Markdown'
        )
        return NAME_ANALYSIS_NIKUD

    # ביצוע הניתוח
    await update.message.reply_text("⏳ מעבד את הניתוח... אנא המתן...")

    try:
        # בניית מילון הניקוד
        nikud_dict = {i + 1: nikud_list[i] for i in range(len(name))}

        # ביצוע הניתוח
        analyzer = NameAnalysis(name, nikud_dict)
        result_lines = analyzer.analyze_name()
        full_text = "\n".join(result_lines)

        # נקה ANSI וקודד ל-bytes
        cleaned = ANSI_RE.sub('', full_text)
        bio = BytesIO(cleaned.encode('utf-8'))
        bio.name = f'{name}_name_analysis.txt'

        # שלח כקובץ
        await update.message.reply_document(
            document=bio,
            caption=f"✅ *ניתוח השם '{name}' הושלם!*\n\n📄 הקובץ המצורף מכיל את הניתוח המלא.",
            parse_mode='Markdown'
        )

        # חזרה לתפריט
        user_id = update.effective_user.id
        await update.message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

    except Exception as e:
        logger.error(f"Error in name analysis: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ אירעה שגיאה בניתוח השם: {str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    # ניקוי המידע
    context.user_data.clear()
    return MAIN_MENU


# ============================================================================
# מפת לידה - Birth Chart Flow
# ============================================================================

async def chart_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל שם למפת לידה"""
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("❌ השם לא יכול להיות ריק. נסה שוב:")
        return CHART_NAME

    context.user_data['chart_name'] = name

    await update.message.reply_text(
        f"✅ שם התקבל: *{name}*\n\n"
        "כעת הזן את תאריך הלידה בפורמט:\n"
        "`YYYY-MM-DD`\n\n"
        "לדוגמה: `1990-05-15`",
        parse_mode='Markdown'
    )
    return CHART_DATE


async def chart_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל תאריך לידה"""
    date_str = update.message.text.strip()

    try:
        birthdate = datetime.strptime(date_str, "%Y-%m-%d").date()
        context.user_data['chart_birthdate'] = birthdate

        await update.message.reply_text(
            f"✅ תאריך התקבל: *{birthdate}*\n\n"
            "כעת הזן את שעת הלידה בפורמט:\n"
            "`HH:MM`\n\n"
            "לדוגמה: `14:30`\n"
            "או שלח `אין` אם השעה לא ידועה.",
            parse_mode='Markdown'
        )
        return CHART_TIME

    except ValueError:
        await update.message.reply_text(
            "❌ פורמט תאריך לא תקין!\n"
            "אנא הזן בפורמט: `YYYY-MM-DD`\n"
            "לדוגמה: `1990-05-15`",
            parse_mode='Markdown'
        )
        return CHART_DATE


async def chart_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל שעת לידה"""
    time_str = update.message.text.strip()

    if time_str.lower() in ['אין', 'לא', 'לא ידוע', 'skip']:
        context.user_data['chart_birthtime'] = None
        await update.message.reply_text(
            "⚠️ ללא שעת לידה, לא ניתן לחשב מפת לידה מדויקת.\n"
            "הבוט דורש שעת לידה למפת לידה.\n\n"
            "אנא הזן שעת לידה או בחר /start לחזרה לתפריט הראשי."
        )
        return CHART_TIME

    try:
        birthtime = datetime.strptime(time_str, "%H:%M").time()
        context.user_data['chart_birthtime'] = birthtime

        await update.message.reply_text(
            f"✅ שעה התקבלה: *{birthtime}*\n\n"
            "כעת הזן את מיקום הלידה בפורמט:\n"
            "`Latitude, Longitude`\n\n"
            "לדוגמה: `32.08, 34.78`\n"
            "או שלח `אין` אם המיקום לא ידוע.",
            parse_mode='Markdown'
        )
        return CHART_LOCATION

    except ValueError:
        await update.message.reply_text(
            "❌ פורמט שעה לא תקין!\n"
            "אנא הזן בפורמט: `HH:MM`\n"
            "לדוגמה: `14:30`",
            parse_mode='Markdown'
        )
        return CHART_TIME


async def chart_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל מיקום לידה"""
    location_str = update.message.text.strip()

    if location_str.lower() in ['אין', 'לא', 'לא ידוע', 'skip']:
        context.user_data['chart_location'] = None
        await update.message.reply_text(
            "⚠️ ללא מיקום לידה, לא ניתן לחשב מפת לידה מדויקת.\n"
            "הבוט דורש מיקום למפת לידה.\n\n"
            "אנא הזן מיקום או בחר /start לחזרה לתפריט הראשי."
        )
        return CHART_LOCATION

    try:
        lat_str, lon_str = location_str.split(',')
        latitude = float(lat_str.strip())
        longitude = float(lon_str.strip())

        # ולידציה בסיסית
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Coordinates out of range")

        context.user_data['chart_location'] = (latitude, longitude)

        # בחירת סוג דוח
        keyboard = [
            [InlineKeyboardButton("📖 דוח מפורט עם פרשנות", callback_data="interpreted_yes")],
            [InlineKeyboardButton("📊 רק מיקומים (ללא פרשנות)", callback_data="interpreted_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ מיקום התקבל: *{latitude}°, {longitude}°*\n\n"
            "כעת בחר את סוג הדוח:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CHART_INTERPRETATION

    except (ValueError, AttributeError):
        await update.message.reply_text(
            "❌ פורמט מיקום לא תקין!\n"
            "אנא הזן בפורמט: `Latitude, Longitude`\n"
            "לדוגמה: `32.08, 34.78`",
            parse_mode='Markdown'
        )
        return CHART_LOCATION


async def chart_interpretation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מטפל בבחירת סוג הדוח ומבצע את הניתוח"""
    query = update.callback_query
    await query.answer()

    is_interpreted = (query.data == "interpreted_yes")

    await query.edit_message_text(
        "⏳ מחשב את מפת הלידה... אנא המתן (זה עשוי לקחת מספר שניות)..."
    )

    try:
        # איסוף כל הנתונים
        name = context.user_data['chart_name']
        birthdate = context.user_data['chart_birthdate']
        birthtime = context.user_data['chart_birthtime']
        location = context.user_data['chart_location']

        # יצירת אובייקט משתמש
        user = User(name, birthdate, birthtime, location)

        # חישוב מפת הלידה
        birth_datetime = datetime.combine(birthdate, birthtime)
        chart_positions = calculate_chart_positions(
            birth_datetime,
            location[0],  # Latitude
            location[1]  # Longitude
        )

        # ביצוע ניתוח
        chart_analysis = ChartAnalysis(user)
        report_text = chart_analysis.analyze_chart(is_interpreted)

        # שמירת הדוח לקובץ
        suffix = "_interpreted" if is_interpreted else "_positions"
        report_filename = os.path.join(CHARTS_DIR, f"{name}_chart{suffix}.txt")
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.writelines([line + '\n' for line in report_text])

        # ציור המפה
        image_filename = os.path.join(CHARTS_DIR, f"{name}_chart.png")
        draw_and_save_chart(chart_positions, user, image_filename)

        # שליחת התוצאות
        report_type = "מפורט עם פרשנות" if is_interpreted else "מיקומים בלבד"

        # שליחת הדוח הטקסטואלי
        with open(report_filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                caption=f"✅ *ניתוח מפת הלידה של {name} הושלם!*\n\n"
                        f"📄 סוג דוח: {report_type}",
                parse_mode='Markdown'
            )

        # שליחת תמונת המפה
        with open(image_filename, 'rb') as f:
            await query.message.reply_photo(
                photo=f,
                caption=f"🖼️ *מפת הלידה של {name}*\n\n"
                        f"📅 {birthdate} | ⏰ {birthtime}\n"
                        f"📍 {location[0]}°, {location[1]}°",
                parse_mode='Markdown'
            )

        # חזרה לתפריט
        user_id = query.from_user.id
        await query.message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

        # שמירת פרופיל למשתמש
        user_profiles[user_id] = {
            'name': name,
            'birthdate': birthdate,
            'birthtime': birthtime,
            'birth_location': location
        }

    except Exception as e:
        logger.error(f"Error in birth chart analysis: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ אירעה שגיאה בחישוב מפת הלידה:\n{str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    # ניקוי המידע
    context.user_data.clear()
    return MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מבטל את השיחה הנוכחית"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ הפעולה בוטלה.\n\n"
        "לחזרה לתפריט הראשי: /start"
    )
    return ConversationHandler.END


# ============================================================================
# מפת מעברים - Transits Flow
# ============================================================================

async def transit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל שם למפת מעברים"""
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
    """מקבל תאריך לידה לטרנזיטים"""
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
    """מקבל שעת לידה לטרנזיטים"""
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
    """מקבל מיקום לידה לטרנזיטים"""
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
    """מקבל מיקום נוכחי לטרנזיטים"""
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
    """מטפל בבחירת מצב טרנזיטים"""
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
    """מטפל בבחירת סוג דוח ומבצע את הניתוח"""
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
        await process_current_transits(query, context)
        return MAIN_MENU


async def transit_future_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל מספר ימים לטרנזיטים עתידיים"""
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
    """מטפל בבחירת מיון ומבצע את החישוב"""
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
    """מעבד ומציג טרנזיטים נוכחיים"""
    try:
        # איסוף כל הנתונים
        name = context.user_data['transit_name']
        birthdate = context.user_data['transit_birthdate']
        birthtime = context.user_data['transit_birthtime']
        birth_location = context.user_data['transit_birth_location']
        current_location = context.user_data['transit_current_location']
        is_interpreted = context.user_data['transit_is_interpreted']

        # יצירת אובייקט משתמש
        user = User(name, birthdate, birthtime, birth_location)

        # נתוני נטאל
        birth_datetime = datetime.combine(birthdate, birthtime)
        natal_chart_data = calculate_chart_positions(
            birth_datetime,
            birth_location[0],
            birth_location[1]
        )

        # נתוני טרנזיט
        current_datetime = datetime.now()
        transit_chart_data = calculate_current_positions(
            current_datetime,
            current_location[0],
            current_location[1]
        )

        # ניתוח טקסטואלי
        chart_analysis = ChartAnalysis(user)
        transit_result = chart_analysis.analyze_transits_and_aspects(
            current_location,
            is_interpreted=is_interpreted
        )

        # שמירת הדוח
        suffix = "_interpreted" if is_interpreted else "_positions"
        birth_time_str = birthtime.strftime('%H-%M')
        filename_prefix = f"Natal_{birthdate}_at_{birth_time_str}_Transit_to_{current_datetime.strftime('%Y-%m-%d_%H-%M')}{suffix}"

        report_filename = os.path.join(TRANSITS_DIR, f"{filename_prefix}.txt")
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.writelines([line + '\n' for line in transit_result])

        # ציור Bi-Wheel
        image_filename = os.path.join(TRANSITS_DIR, f"{filename_prefix}_biwheel.png")
        draw_and_save_biwheel_chart(
            natal_chart_data,
            transit_chart_data,
            user,
            current_datetime,
            image_filename
        )

        # שליחת התוצאות
        report_type = "מפורט עם פרשנות" if is_interpreted else "מיקומים בלבד"

        # שליחת הדוח
        with open(report_filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                caption=f"✅ *ניתוח טרנזיטים נוכחיים של {name} הושלם!*\n\n"
                        f"📄 סוג דוח: {report_type}\n"
                        f"🌍 מיקום נוכחי: {current_location[0]}°, {current_location[1]}°\n"
                        f"📅 {current_datetime.strftime('%Y-%m-%d %H:%M')}",
                parse_mode='Markdown'
            )

        # שליחת תמונת Bi-Wheel
        with open(image_filename, 'rb') as f:
            await query.message.reply_photo(
                photo=f,
                caption=f"🖼️ *מפת Bi-Wheel: נטאל + טרנזיט נוכחי*\n\n"
                        f"🔵 מעגל פנימי: מפת לידה\n"
                        f"🟢 מעגל חיצוני: טרנזיטים נוכחיים",
                parse_mode='Markdown'
            )

        # חזרה לתפריט
        user_id = query.from_user.id
        await query.message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

        # שמירת פרופיל למשתמש
        user_profiles[user_id] = {
            'name': name,
            'birthdate': birthdate,
            'birthtime': birthtime,
            'birth_location': birth_location
        }

    except Exception as e:
        logger.error(f"Error in current transits: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ אירעה שגיאה בחישוב טרנזיטים נוכחיים:\n{str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    # ניקוי המידע (אבל לא הפרופיל!)
    context.user_data.clear()


async def process_future_transits(query, context: ContextTypes.DEFAULT_TYPE):
    """מעבד ומציג טרנזיטים עתידיים"""
    try:
        # איסוף כל הנתונים
        name = context.user_data['transit_name']
        birthdate = context.user_data['transit_birthdate']
        birthtime = context.user_data['transit_birthtime']
        birth_location = context.user_data['transit_birth_location']
        current_location = context.user_data['transit_current_location']
        is_interpreted = context.user_data['transit_is_interpreted']
        days_ahead = context.user_data['transit_days']
        sort_mode = context.user_data.get('transit_sort_mode', 'duration')  # ✅ תוקן!

        # יצירת אובייקט משתמש
        user = User(name, birthdate, birthtime, birth_location)

        # חישוב טרנזיטים
        calculator = TransitCalculator(user)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)

        result = calculator.calculate_aspects_in_range(
            start_date,
            end_date,
            current_location
        )

        # פורמט הדוח
        report_lines = format_future_transits_report(result, sort_mode, is_interpreted)

        # שמירת הדוח
        suffix = "_interpreted" if is_interpreted else "_positions"
        text_filename = f"future_transits_{name}_{datetime.now():%Y%m%d_%H%M}{suffix}.txt"
        text_filepath = os.path.join(TRANSITS_DIR, text_filename)

        with open(text_filepath, 'w', encoding='utf-8') as f:
            for line in report_lines:
                f.write(line + "\n")

        # שליחת הדוח
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

        # חזרה לתפריט
        user_id = query.from_user.id
        await query.message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

        # שמירת פרופיל למשתמש
        user_profiles[user_id] = {
            'name': name,
            'birthdate': birthdate,
            'birthtime': birthtime,
            'birth_location': birth_location
        }

    except Exception as e:
        logger.error(f"Error in future transits: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ אירעה שגיאה בחישוב טרנזיטים עתידיים:\n{str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    # ניקוי המידע (אבל לא הפרופיל!)
    context.user_data.clear()


def format_future_transits_report(result: dict, sort_mode: str = "duration", is_interpreted: bool = False) -> list:
    """
    ממיר את תוצאות ה-JSON לדוח טקסט קריא.

    :param result: תוצאות החישוב מ-TransitCalculator
    :param sort_mode: מצב מיון - "duration" (משך זמן), "chronological" (כרונולוגי לפי היבט), "events" (כרונולוגי לפי אירועים)
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
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%d.%m.%Y %H:%M')

    def format_duration_precise(start_str: str, end_str: str) -> str:
        """ממיר משך זמן לפורמט מדויק"""
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)

        total_seconds = (end - start).total_seconds()
        total_hours = total_seconds / 3600
        total_days = total_seconds / (3600 * 24)
        total_months = total_days / 30.44
        total_years = total_days / 365.25

        if total_years >= 2:
            years = int(total_years)
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

    # כותרת
    metadata = result['metadata']
    interpretation_text = " (עם פרשנות)" if is_interpreted else ""
    report.append(f"=== טרנזיטים עתידיים עבור {metadata['user_name']}{interpretation_text} ===")
    report.append(f"תאריך לידה: {metadata['birth_date']}")
    report.append(f"נוצר ב: {metadata['calculated_at'][:19]}")

    start_date = datetime.fromisoformat(metadata['range'][0])
    end_date = datetime.fromisoformat(metadata['range'][1])
    report.append(f"טווח: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
    report.append(f"סה\"כ היבטים: {metadata['total_aspects']}")
    report.append("")

    # מיון לפי אירועים - מצב חדש!
    if sort_mode == "events":
        try:
            report.append("=" * 80)
            report.append("ציר זמן כרונולוגי - ממוין לפי אירועים")
            report.append("=" * 80)
            report.append("")

            # בניית רשימת אירועים
            events = []

            for aspect in result['aspects']:
                lifecycle = aspect['lifecycle']
                aspect_name_heb = ASPECTS_HEB.get(aspect['aspect_type'], aspect['aspect_type'])
                aspect_title = f"{aspect['natal_planet']} (לידה) {aspect_name_heb} {aspect['transit_planet']} (מעבר)"

                # אירוע כניסה
                if lifecycle['start']:
                    events.append({
                        'date': lifecycle['start'],
                        'type': 'entry',
                        'aspect': aspect,
                        'aspect_title': aspect_title,
                        'aspect_name_heb': aspect_name_heb
                    })

                # אירועי שיא
                if lifecycle.get('exact_dates') and isinstance(lifecycle['exact_dates'], list):
                    for exact in lifecycle['exact_dates']:
                        if exact and 'date' in exact:
                            events.append({
                                'date': exact['date'],
                                'type': 'exact',
                                'aspect': aspect,
                                'aspect_title': aspect_title,
                                'aspect_name_heb': aspect_name_heb,
                                'is_retrograde': exact.get('is_retrograde', False)
                            })

                # אירוע יציאה
                if lifecycle['end']:
                    events.append({
                        'date': lifecycle['end'],
                        'type': 'exit',
                        'aspect': aspect,
                        'aspect_title': aspect_title,
                        'aspect_name_heb': aspect_name_heb
                    })

            # מיון לפי תאריך
            events.sort(key=lambda e: e['date'])

            # טעינת נתוני פרשנות אם נדרש
            chart_data = None
            if is_interpreted:
                try:
                    from src.birth_chart_analysis.ChartDataLoaders import load_all_chart_data
                    chart_data = load_all_chart_data()
                except Exception as e:
                    logger.error(f"Failed to load chart data for interpretation: {e}")
                    # ממשיכים בלי פרשנות
                    chart_data = None

                # הדפסת האירועים
                for i, event in enumerate(events, 1):
                    lifecycle = event['aspect']['lifecycle']

                    # תאריך האירוע
                    event_date = format_datetime(event['date'])

                    # אייקון לפי סוג אירוע
                    if event['type'] == 'entry':
                        icon = "🟢 כניסה להיבט"
                    elif event['type'] == 'exact':
                        retro_mark = " ⟲" if event.get('is_retrograde') else ""
                        icon = f"⭐ שיא היבט{retro_mark}"
                    else:  # exit
                        icon = "🔴 יציאה מהיבט"

                    # הדפס את האירוע
                    report.append(f"📅 {event_date} - {icon}")
                    report.append(f"   {event['aspect_title']}")

                    # פרטים נוספים (רק בכניסה ושיא)
                    if event['type'] == 'entry':
                        if lifecycle['start'] and lifecycle['end']:
                            duration_str = format_duration_precise(lifecycle['start'], lifecycle['end'])
                            report.append(
                                f"   תקופת פעילות: {format_datetime(lifecycle['start'])} - {format_datetime(lifecycle['end'])} ({duration_str})")

                    # פרשנות (רק בשיא)
                    if event['type'] == 'exact' and is_interpreted and chart_data:

                        PLANET_NAMES_ENG = {
                            'שמש': 'Sun', 'ירח': 'Moon', 'מרקורי': 'Mercury',
                            'ונוס': 'Venus', 'מאדים': 'Mars', 'צדק': 'Jupiter',
                            'שבתאי': 'Saturn', 'אורנוס': 'Uranus', 'נפטון': 'Neptune',
                            'פלוטו': 'Pluto', 'ראש דרקון': 'North Node', 'לילית': 'Lilith',
                            'כירון': 'Chiron', 'אופק (AC)': 'AC', 'רום שמיים (MC)': 'MC',
                            'פורטונה': 'Fortune', 'ורטקס': 'Vertex'
                        }

                        p1_eng = PLANET_NAMES_ENG.get(event['aspect']['natal_planet'], event['aspect']['natal_planet'])
                        p2_eng = PLANET_NAMES_ENG.get(event['aspect']['transit_planet'], event['aspect']['transit_planet'])
                        aspect_name_eng = event['aspect']['aspect_type']

                        key = f"Natal {p1_eng} {aspect_name_eng} Transit {p2_eng}"
                        aspects_transit_data = chart_data.get('aspects_transit', {})
                        analysis = aspects_transit_data.get(key)

                        if analysis:
                            report.append(f"\n   📖 פרשנות:\n   {analysis}\n")

                    report.append("")

                    # מפריד כל 10 אירועים
                    if i % 10 == 0 and i < len(events):
                        report.append("-" * 80)
                        report.append("")

                    return report

        except Exception as e:
            logger.error(f"Error in events sorting: {e}", exc_info=True)
            # במקרה של שגיאה, נחזור למיון רגיל
            report.append("⚠️ אירעה שגיאה במיון לפי אירועים, מציג מיון כרונולוגי רגיל")
            report.append("")
            sort_mode = "chronological"  # fallback


    # מיון ההיבטים (מצב ישן - לפי משך או כרונולוגי לפי היבט)
    if sort_mode == "chronological":
        aspects = sorted(result['aspects'],
                         key=lambda x: x['lifecycle']['start'])
    else:  # duration
        aspects = sorted(result['aspects'],
                         key=lambda x: (
                             (datetime.fromisoformat(x['lifecycle']['end']) -
                              datetime.fromisoformat(x['lifecycle']['start'])).total_seconds()
                             if x['lifecycle']['start'] and x['lifecycle']['end']
                             else float('inf')
                         ))

    report.append("=" * 80)
    if sort_mode == "chronological":
        sort_type_text = "ממוין לפי תאריך התחלה (כרונולוגי)"
    else:
        sort_type_text = "ממוין לפי משך זמן (מהקצר לארוך)"
    report.append(f"רשימת כל ההיבטים העתידיים - {sort_type_text}")
    report.append("=" * 80)
    report.append("")

    # טעינת נתוני פרשנות אם נדרש
    chart_data = None
    if is_interpreted:
        from src.birth_chart_analysis.ChartDataLoaders import load_all_chart_data

        chart_data = load_all_chart_data()

    for i, aspect in enumerate(aspects, 1):
        lifecycle = aspect['lifecycle']

        # תרגום שם ההיבט לעברית
        aspect_name_heb = ASPECTS_HEB.get(aspect['aspect_type'], aspect['aspect_type'])

        # שורת כותרת ההיבט
        aspect_line = f"{aspect['natal_planet']} (לידה) {aspect_name_heb} {aspect['transit_planet']} (מעבר)"
        report.append(aspect_line)

        # תקופת פעילות
        if lifecycle['start'] and lifecycle['end']:
            start_formatted = format_datetime(lifecycle['start'])
            end_formatted = format_datetime(lifecycle['end'])
            duration_str = format_duration_precise(lifecycle['start'], lifecycle['end'])

            passes_suffix = ""
            if lifecycle['num_passes'] > 1:
                passes_suffix = f", {lifecycle['num_passes']} מעברים"

            report.append(f"    - תקופת פעילות: {start_formatted} - {end_formatted} ({duration_str}{passes_suffix})")

        # שיא ההיבט
        if lifecycle['exact_dates']:
            first_exact = lifecycle['exact_dates'][0]
            exact_formatted = format_datetime(first_exact['date'])
            retro_marker = " ⟲" if first_exact['is_retrograde'] else ""

            report.append(f"    - שיא ההיבט: {exact_formatted}{retro_marker}")

            # שיאים נוספים
            if len(lifecycle['exact_dates']) > 1:
                other_exacts = []
                for ex in lifecycle['exact_dates'][1:]:
                    ex_formatted = format_datetime(ex['date'])
                    retro_mark = " ⟲" if ex['is_retrograde'] else ""
                    other_exacts.append(f"{ex_formatted}{retro_mark}")

                report.append(f"    - שיאים נוספים: {', '.join(other_exacts)}")

        # הוספת פרשנות אם נדרש
        if is_interpreted and chart_data:
            PLANET_NAMES_ENG = {
                'שמש': 'Sun', 'ירח': 'Moon', 'מרקורי': 'Mercury',
                'ונוס': 'Venus', 'מאדים': 'Mars', 'צדק': 'Jupiter',
                'שבתאי': 'Saturn', 'אורנוס': 'Uranus', 'נפטון': 'Neptune',
                'פלוטו': 'Pluto', 'ראש דרקון': 'North Node', 'לילית': 'Lilith',
                'כירון': 'Chiron', 'אופק (AC)': 'AC', 'רום שמיים (MC)': 'MC',
                'פורטונה': 'Fortune', 'ורטקס': 'Vertex'
            }

            p1_eng = PLANET_NAMES_ENG.get(aspect['natal_planet'], aspect['natal_planet'])
            p2_eng = PLANET_NAMES_ENG.get(aspect['transit_planet'], aspect['transit_planet'])
            aspect_name_eng = aspect['aspect_type']

            key = f"Natal {p1_eng} {aspect_name_eng} Transit {p2_eng}"
            aspects_transit_data = chart_data.get('aspects_transit', {})
            analysis = aspects_transit_data.get(key)

            if analysis:
                report.append(f"\n📖 פרשנות:\n{analysis}")
            else:
                report.append(f"\n⚠️ פרשנות להיבט זה לא נמצאה במאגר")

        report.append("")

        # מפריד כל 10 היבטים
        if i % 10 == 0 and i < len(aspects):
            report.append("-" * 80)
            report.append("")

    return report


def main():
    """נקודת הכניסה הראשית"""

    # בניית האפליקציה
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # הגדרת ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_handler),
                CommandHandler("start", start)  # אפשר /start גם מהתפריט
            ],

            # ניתוח שם
            NAME_ANALYSIS_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_analysis_name),
                CommandHandler("start", start)
            ],
            NAME_ANALYSIS_NIKUD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_analysis_nikud),
                CommandHandler("start", start)
            ],

            # מפת לידה
            CHART_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, chart_name),
                CommandHandler("start", start)
            ],
            CHART_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, chart_date),
                CommandHandler("start", start)
            ],
            CHART_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, chart_time),
                CommandHandler("start", start)
            ],
            CHART_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, chart_location),
                CommandHandler("start", start)
            ],
            CHART_INTERPRETATION: [
                CallbackQueryHandler(chart_interpretation),
                CommandHandler("start", start)
            ],

            # טרנזיטים
            TRANSIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transit_name),
                CommandHandler("start", start)
            ],
            TRANSIT_BIRTH_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transit_birth_date),
                CommandHandler("start", start)
            ],
            TRANSIT_BIRTH_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transit_birth_time),
                CommandHandler("start", start)
            ],
            TRANSIT_BIRTH_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transit_birth_location),
                CommandHandler("start", start)
            ],
            TRANSIT_CURRENT_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transit_current_location),
                CommandHandler("start", start)
            ],
            TRANSIT_MODE: [
                CallbackQueryHandler(transit_mode_selection),
                CommandHandler("start", start)
            ],
            TRANSIT_INTERPRETATION: [
                CallbackQueryHandler(transit_interpretation_selection),
                CommandHandler("start", start)
            ],
            TRANSIT_FUTURE_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transit_future_days),
                CommandHandler("start", start)
            ],
            TRANSIT_FUTURE_SORT: [
                CallbackQueryHandler(transit_future_sort),
                CommandHandler("start", start)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # הוספת error handler גלובלי
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול בשגיאות גלובלי - מונע קריסת הבוט"""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

        # אם יש update, נסה לשלוח הודעה למשתמש
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ אופס! משהו השתבש.\n"
                    "הבוט נתקל בבעיה, אבל הוא עדיין עובד!\n\n"
                    "נסה שוב או לחץ /start לחזרה לתפריט הראשי."
                )
            except Exception:
                pass  # אם גם זה נכשל, לפחות הבוט לא קורס

    app.add_error_handler(error_handler)

    # הרצה לפי סביבה
    if os.getenv("FLY_APP_NAME"):
        # הפעלה ב-Fly.io עם webhook
        url_path = os.environ["WEBHOOK_URL"].rstrip("/").rsplit("/", 1)[-1]
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            url_path=url_path,
            webhook_url=os.environ["WEBHOOK_URL"],
        )
    else:
        # פיתוח מקומי עם polling
        logger.info("Starting bot in polling mode...")
        app.run_polling()


if __name__ == "__main__":
    main()
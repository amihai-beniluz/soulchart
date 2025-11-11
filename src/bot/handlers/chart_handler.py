"""
Handler למפות לידה בבוט הטלגרם.
"""
import os
import sys
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# הוספת src לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from user import User
from chart_analysis.ChartAnalysis import ChartAnalysis
from chart_analysis.ChartDrawer import draw_and_save_chart
from chart_analysis.CalculationEngine import calculate_chart_positions
from bot.bot_utils import (
    save_user_input, save_user_profile, get_main_menu_keyboard,
    CHARTS_DIR, get_user_profile
)

logger = logging.getLogger(__name__)

# מצבי שיחה
CHART_NAME = 3
CHART_DATE = 4
CHART_TIME = 5
CHART_LOCATION = 6
CHART_INTERPRETATION = 7
MAIN_MENU = 0


async def chart_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מתחיל תהליך מפת לידה."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    profile = get_user_profile(user_id)
    if profile:
        context.user_data['chart_name'] = profile['name']
        context.user_data['chart_birthdate'] = profile['birthdate']
        context.user_data['chart_birthtime'] = profile['birthtime']
        context.user_data['chart_location'] = profile['birth_location']

        keyboard = [
            [InlineKeyboardButton("📖 דוח מפורט עם פרשנות", callback_data="interpreted_yes")],
            [InlineKeyboardButton("📊 רק מיקומים (ללא פרשנות)", callback_data="interpreted_no")]
        ]

        await query.edit_message_text(
            f"⭐ *מפת לידה אסטרולוגית*\n\n"
            f"✅ משתמש מזוהה: *{profile['name']}*\n"
            f"📅 {profile['birthdate']} | ⏰ {profile['birthtime']}\n"
            f"📍 {profile['birth_location'][0]}°, {profile['birth_location'][1]}°\n\n"
            "בחר את סוג הדוח:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CHART_INTERPRETATION
    else:
        await query.edit_message_text(
            "⭐ *מפת לידה אסטרולוגית*\n\n"
            "נתחיל באיסוף נתוני הלידה.\n"
            "אנא שלח את השם המלא:",
            parse_mode='Markdown'
        )
        return CHART_NAME


async def chart_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל שם למפת לידה."""
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
    """מקבל תאריך לידה."""
    date_str = update.message.text.strip()

    try:
        birthdate = datetime.strptime(date_str, "%Y-%m-%d").date()
        context.user_data['chart_birthdate'] = birthdate

        await update.message.reply_text(
            f"✅ תאריך התקבל: *{birthdate}*\n\n"
            "כעת הזן את שעת הלידה בפורמט:\n"
            "`HH:MM`\n\n"
            "לדוגמה: `14:30`",
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
    """מקבל שעת לידה."""
    time_str = update.message.text.strip()

    if time_str.lower() in ['אין', 'לא', 'לא ידוע', 'skip']:
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
            "לדוגמה: `32.08, 34.78`",
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
    """מקבל מיקום לידה."""
    location_str = update.message.text.strip()

    try:
        lat_str, lon_str = location_str.split(',')
        latitude = float(lat_str.strip())
        longitude = float(lon_str.strip())

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Coordinates out of range")

        context.user_data['chart_location'] = (latitude, longitude)

        keyboard = [
            [InlineKeyboardButton("📖 דוח מפורט עם פרשנות", callback_data="interpreted_yes")],
            [InlineKeyboardButton("📊 רק מיקומים (ללא פרשנות)", callback_data="interpreted_no")]
        ]

        await update.message.reply_text(
            f"✅ מיקום התקבל: *{latitude}°, {longitude}°*\n\n"
            "כעת בחר את סוג הדוח:",
            reply_markup=InlineKeyboardMarkup(keyboard),
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
    """מטפל בבחירת סוג הדוח ומבצע את הניתוח."""
    query = update.callback_query
    await query.answer()

    is_interpreted = (query.data == "interpreted_yes")

    await query.edit_message_text(
        "⏳ מחשב את מפת הלידה... אנא המתן (זה עשוי לקחת מספר שניות)..."
    )

    try:
        name = context.user_data['chart_name']
        birthdate = context.user_data['chart_birthdate']
        birthtime = context.user_data['chart_birthtime']
        location = context.user_data['chart_location']

        user = User(name, birthdate, birthtime, location)

        birth_datetime = datetime.combine(birthdate, birthtime)
        chart_positions = calculate_chart_positions(
            birth_datetime,
            location[0],
            location[1]
        )

        chart_analysis = ChartAnalysis(user)
        report_text = chart_analysis.analyze_chart(is_interpreted)

        suffix = "_interpreted" if is_interpreted else "_positions"
        report_filename = os.path.join(CHARTS_DIR, f"{name}_chart{suffix}.txt")
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.writelines([line + '\n' for line in report_text])

        image_filename = os.path.join(CHARTS_DIR, f"{name}_chart.png")
        draw_and_save_chart(chart_positions, user, image_filename)

        report_type = "מפורט עם פרשנות" if is_interpreted else "מיקומים בלבד"

        with open(report_filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                caption=f"✅ *ניתוח מפת הלידה של {name} הושלם!*\n\n"
                        f"📄 סוג דוח: {report_type}",
                parse_mode='Markdown'
            )

        with open(image_filename, 'rb') as f:
            await query.message.reply_photo(
                photo=f,
                caption=f"🖼️ *מפת הלידה של {name}*\n\n"
                        f"📅 {birthdate} | ⏰ {birthtime}\n"
                        f"📍 {location[0]}°, {location[1]}°",
                parse_mode='Markdown'
            )

        user_id = query.from_user.id
        await query.message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

        save_user_profile(user_id, name, birthdate, birthtime, location)
        save_user_input(user_id, {
            'type': 'birth_chart',
            'name': name,
            'birthdate': str(birthdate),
            'birthtime': str(birthtime),
            'location': location,
            'interpreted': is_interpreted
        })

    except Exception as e:
        logger.error(f"Error in birth chart analysis: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ אירעה שגיאה בחישוב מפת הלידה:\n{str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    context.user_data.clear()
    return MAIN_MENU

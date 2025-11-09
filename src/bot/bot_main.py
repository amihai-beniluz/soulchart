"""
נקודת כניסה ראשית לבוט הטלגרם של SoulChart.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

# הוספת src לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from bot.bot_utils import get_main_menu_keyboard, delete_user_profile
from bot.handlers import (
    name_analysis_start,
    name_analysis_name,
    name_analysis_nikud,
    NAME_ANALYSIS_NAME,
    NAME_ANALYSIS_NIKUD,
    chart_start,
    chart_name,
    chart_date,
    chart_time,
    chart_location,
    chart_interpretation,
    CHART_NAME,
    CHART_DATE,
    CHART_TIME,
    CHART_LOCATION,
    CHART_INTERPRETATION,
    transit_start,
    transit_name,
    transit_birth_date,
    transit_birth_time,
    transit_birth_location,
    transit_current_location,
    transit_mode_selection,
    transit_interpretation_selection,
    transit_future_days,
    transit_future_sort,
    TRANSIT_NAME,
    TRANSIT_BIRTH_DATE,
    TRANSIT_BIRTH_TIME,
    TRANSIT_BIRTH_LOCATION,
    TRANSIT_CURRENT_LOCATION,
    TRANSIT_MODE,
    TRANSIT_INTERPRETATION,
    TRANSIT_FUTURE_DAYS,
    TRANSIT_FUTURE_SORT
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

MAIN_MENU = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """תגובה לפקודת /start - מציג תפריט ראשי"""
    user_id = update.effective_user.id
    context.user_data.clear()

    from bot.bot_utils import get_user_profile
    profile = get_user_profile(user_id)

    if profile:
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
        if delete_user_profile(user_id):
            await query.edit_message_text(
                "✅ *פרופיל נמחק בהצלחה!*\n\n"
                "עכשיו תוכל להזין נתונים חדשים.\n"
                "לחץ /start להתחלה מחדש.",
                parse_mode='Markdown'
            )
        return ConversationHandler.END

    elif query.data == "name_analysis":
        return await name_analysis_start(update, context)

    elif query.data == "birth_chart":
        return await chart_start(update, context)

    elif query.data == "transits":
        return await transit_start(update, context)

    elif query.data == "help":
        help_text = (
            "ℹ️ *מדריך שימוש*\n\n"
            "*ניתוח שם:*\n"
            "1. בחר 'ניתוח שם'\n"
            "2. שלח את השם בעברית\n"
            "3. הזן ניקוד לכל אות\n\n"
            "*מפת לידה:*\n"
            "1. בחר 'מפת לידה'\n"
            "2. עקוב אחר ההוראות שלב אחר שלב\n\n"
            "*💡 טיפ:* לאחר שתזין את הפרטים פעם אחת,\n"
            "הם יישמרו ולא תצטרך להזין אותם שוב!\n\n"
            "לחזרה לתפריט הראשי: /start"
        )
        await query.edit_message_text(help_text, parse_mode='Markdown')
        await query.message.reply_text(
            "בחר פעולה:",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מבטל את השיחה הנוכחית"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ הפעולה בוטלה.\n\n"
        "לחזרה לתפריט הראשי: /start"
    )
    return ConversationHandler.END


def main():
    """נקודת הכניסה הראשית"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_handler),
                CommandHandler("start", start)
            ],
            NAME_ANALYSIS_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_analysis_name),
                CommandHandler("start", start)
            ],
            NAME_ANALYSIS_NIKUD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_analysis_nikud),
                CommandHandler("start", start)
            ],
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

    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול בשגיאות גלובלי"""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ אופס! משהו השתבש.\n"
                    "הבוט נתקל בבעיה, אבל הוא עדיין עובד!\n\n"
                    "נסה שוב או לחץ /start לחזרה לתפריט הראשי."
                )
            except Exception:
                pass

    app.add_error_handler(error_handler)

    if os.getenv("FLY_APP_NAME"):
        url_path = os.environ["WEBHOOK_URL"].rstrip("/").rsplit("/", 1)[-1]
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            url_path=url_path,
            webhook_url=os.environ["WEBHOOK_URL"],
        )
    else:
        logger.info("Starting bot in polling mode...")
        app.run_polling()


if __name__ == "__main__":
    main()
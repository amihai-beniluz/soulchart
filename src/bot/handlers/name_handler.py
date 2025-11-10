"""
Handler לניתוח שמות בבוט הטלגרם.
"""
import os
import sys
import logging
import re
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# הוספת src לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from name_analysis.NameAnalysis import NameAnalysis
from names_manager import NamesManager, nikud_dict_from_nikud_name
from bot.bot_utils import save_user_input, get_main_menu_keyboard

logger = logging.getLogger(__name__)

# נקה ANSI colors
ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

# מצבי שיחה
NAME_ANALYSIS_NAME = 1
NAME_ANALYSIS_NIKUD = 2
MAIN_MENU = 0


def apply_nikud_to_name(name: str, nikud_dict: dict) -> str:
    """מחבר שם עם דיקשנרי ניקוד ליצירת שם מנוקד לתצוגה."""
    NIKUD_UNICODE = {
        'פתח': '\u05B7',
        'קמץ': '\u05B8',
        'חיריק': '\u05B4',
        'צירה': '\u05B5',
        'סגול': '\u05B6',
        'שווא': '\u05B0',
        'חולם': '\u05B9',
        'קובוץ': '\u05BB',
        'שורוק': '\u05BC',  # דגש עבור ו
        'ריק': ''
    }

    result = []
    for i, char in enumerate(name, 1):
        result.append(char)
        if i in nikud_dict:
            nikud_name = nikud_dict[i]
            if nikud_name in NIKUD_UNICODE:
                result.append(NIKUD_UNICODE[nikud_name])
    return ''.join(result)


async def name_analysis_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מתחיל תהליך ניתוח שם."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 *ניתוח שם קבלי ונומרולוגי*\n\n"
        "אנא שלח את השם בעברית שברצונך לנתח.\n"
        "לדוגמה: עמיחי",
        parse_mode='Markdown'
    )
    return NAME_ANALYSIS_NAME


async def name_analysis_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל את השם לניתוח ובודק אם הוא במאגר."""
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("❌ השם לא יכול להיות ריק. נסה שוב:")
        return NAME_ANALYSIS_NAME

    context.user_data['name'] = name

    # בדיקה אם יש מנהל שמות
    names_manager = context.bot_data.get('names_manager')

    if names_manager:
        nikud_name, nikud_options = names_manager.get_nikud_for_name(name)

        if nikud_name:
            # שם עם ניקוד יחיד
            context.user_data['suggested_nikud'] = nikud_name
            keyboard = [
                [InlineKeyboardButton("הניקוד נכון ✅", callback_data="nikud_correct")],
                [InlineKeyboardButton("הזן ניקוד ידנית ✏️", callback_data="nikud_manual")]
            ]
            await update.message.reply_text(
                f"✅ שמך מופיע במערכת עם הניקוד הבא:\n\n"
                f"*{nikud_name}*\n\n"
                "אם שמך מנוקד באופן שונה אנא בחר 'הזן ניקוד ידנית'.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return NAME_ANALYSIS_NIKUD

        elif len(nikud_options) > 1:
            # מספר אפשרויות ניקוד
            context.user_data['nikud_options'] = nikud_options
            keyboard = []
            for i, option in enumerate(nikud_options):
                keyboard.append([InlineKeyboardButton(option, callback_data=f"nikud_{i}")])
            keyboard.append([InlineKeyboardButton("הזן ניקוד ידנית ✏️", callback_data="nikud_manual")])

            await update.message.reply_text(
                f"⚠️ שמך מופיע במערכת עם {len(nikud_options)} אפשרויות ניקוד.\n"
                "אנא בחר את הניקוד הנכון:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return NAME_ANALYSIS_NIKUD

        else:
            # השם לא נמצא במאגר
            context.user_data['name_not_in_db'] = True

    # fallback להזנה ידנית (אין מנהל או שם לא נמצא)
    example_nikud = "פתח חיריק ריק פתח ריק"
    await update.message.reply_text(
        f"✅ שם התקבל: *{name}* ({len(name)} אותיות)\n\n"
        f"⚠️ שמך לא מופיע במאגר השמות הקיימים.\n"
        f"כעת שלח את רצף הניקודים בהודעה אחת, מופרדים ברווחים.\n\n"
        f"*סוגי ניקוד אפשריים:*\n"
        f"פתח, חיריק, צירה, קמץ, סגול, שווא, חולם, קובוץ, שורוק, ריק\n\n"
        f"עבור השם *{name}* שלך, שלח {len(name)} ניקודים:",
        parse_mode='Markdown'
    )
    return NAME_ANALYSIS_NIKUD


async def name_analysis_nikud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מטפל בקבלת הניקוד - אוטומטית או ידנית."""
    names_manager = context.bot_data.get('names_manager')
    name = context.user_data.get('name')

    # טיפול בבחירה מכפתורים
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data == "nikud_correct":
            # אישור ניקוד מוצע
            suggested_nikud = context.user_data.get('suggested_nikud')
            nikud_dict = nikud_dict_from_nikud_name(name, suggested_nikud)
            context.user_data['nikud_dict'] = nikud_dict
            return await perform_name_analysis(update, context, query.message)

        elif query.data == "nikud_manual":
            # בחירה בהזנה ידנית
            await query.edit_message_text(
                f"✏️ הזן את רצף הניקודים להודעה אחת, מופרדים ברווחים.\n\n"
                f"*סוגי ניקוד:*\n"
                f"פתח, חיריק, צירה, קמץ, סגול, שווא, חולם, קובוץ, שורוק, ריק\n\n"
                f"עבור השם *{name}* ({len(name)} אותיות):",
                parse_mode='Markdown'
            )
            context.user_data['manual_entry'] = True
            return NAME_ANALYSIS_NIKUD

        elif query.data.startswith("nikud_"):
            # בחירת ניקוד מרשימה
            try:
                option_index = int(query.data.split("_")[1])
                nikud_options = context.user_data.get('nikud_options', [])

                if 0 <= option_index < len(nikud_options):
                    selected_nikud = nikud_options[option_index]
                    nikud_dict = nikud_dict_from_nikud_name(name, selected_nikud)
                    context.user_data['nikud_dict'] = nikud_dict
                    return await perform_name_analysis(update, context, query.message)
            except (IndexError, ValueError):
                await query.edit_message_text("⚠️ שגיאה בבחירת הניקוד. נסה שוב.")
                return ConversationHandler.END

    # טיפול בהזנה טקסט (ידנית)
    else:
        nikud_text = update.message.text.strip()
        nikud_list = nikud_text.split()

        if len(nikud_list) != len(name):
            await update.message.reply_text(
                f"❌ *שגיאה באורך!*\n\n"
                f"השם *{name}* מכיל {len(name)} אותיות,\n"
                f"אבל שלחת {len(nikud_list)} ניקודים.\n\n"
                f"אנא שלח בדיוק {len(name)} ניקודים מופרדים ברווחים.",
                parse_mode='Markdown'
            )
            return NAME_ANALYSIS_NIKUD

        nikud_dict = {i + 1: nikud_list[i] for i in range(len(name))}
        context.user_data['nikud_dict'] = nikud_dict

        # אם השם לא היה במאגר, נוסיף אותו
        if context.user_data.get('name_not_in_db') and names_manager:
            nikud_name = apply_nikud_to_name(name, nikud_dict)
            names_manager.add_or_update_name(name, nikud_name)
            await update.message.reply_text(f"✅ שמך נוסף למאגר עם הניקוד: {nikud_name}")

        return await perform_name_analysis(update, context, update.message)


async def perform_name_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, message):
    """מבצע את ניתוח השם ושולח את התוצאות."""
    name = context.user_data.get('name')
    nikud_dict = context.user_data.get('nikud_dict')

    await message.reply_text("⏳ מעבד את הניתוח... אנא המתן...")

    try:
        analyzer = NameAnalysis(name, nikud_dict)
        result_lines = analyzer.analyze_name()
        full_text = "\n".join(result_lines)

        cleaned = ANSI_RE.sub('', full_text)
        bio = BytesIO(cleaned.encode('utf-8'))
        bio.name = f'{name}_name_analysis.txt'

        await message.reply_document(
            document=bio,
            caption=f"✅ *ניתוח השם '{name}' הושלם!*\n\n📄 הקובץ המצורף מכיל את הניתוח המלא.",
            parse_mode='Markdown'
        )

        user_id = update.effective_user.id
        nikud_list = [nikud_dict.get(i+1, 'ריק') for i in range(len(name))]
        save_user_input(user_id, {'type': 'name_analysis', 'name': name, 'nikud': nikud_list})

        await message.reply_text(
            "לניתוח נוסף, בחר מהתפריט:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

    except Exception as e:
        logger.error(f"Error in name analysis: {e}", exc_info=True)
        await message.reply_text(
            f"❌ אירעה שגיאה בניתוח השם: {str(e)}\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

    context.user_data.clear()
    return MAIN_MENU

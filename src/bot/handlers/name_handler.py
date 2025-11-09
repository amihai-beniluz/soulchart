"""
Handler לניתוח שמות בבוט הטלגרם.
"""
import logging
import re
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.name_analysis.NameAnalysis import NameAnalysis
from ..bot_utils import save_user_input, get_main_menu_keyboard

logger = logging.getLogger(__name__)

# נקה ANSI colors
ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

# מצבי שיחה
NAME_ANALYSIS_NAME = 1
NAME_ANALYSIS_NIKUD = 2
MAIN_MENU = 0


async def name_analysis_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מתחיל תהליך ניתוח שם."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 *ניתוח שם קבלי ונומרולוגי*\n\n"
        "אנא שלח את השם בעברית שברצונך לנתח.\n"
        "לדוגמה: עמי",
        parse_mode='Markdown'
    )
    return NAME_ANALYSIS_NAME


async def name_analysis_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל את השם לניתוח."""
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("❌ השם לא יכול להיות ריק. נסה שוב:")
        return NAME_ANALYSIS_NAME

    context.user_data['name'] = name

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
    """מקבל את כל הניקודים ומבצע את הניתוח."""
    nikud_text = update.message.text.strip()
    name = context.user_data['name']

    nikud_list = nikud_text.split()

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

    await update.message.reply_text("⏳ מעבד את הניתוח... אנא המתן...")

    try:
        nikud_dict = {i + 1: nikud_list[i] for i in range(len(name))}

        analyzer = NameAnalysis(name, nikud_dict)
        result_lines = analyzer.analyze_name()
        full_text = "\n".join(result_lines)

        cleaned = ANSI_RE.sub('', full_text)
        bio = BytesIO(cleaned.encode('utf-8'))
        bio.name = f'{name}_name_analysis.txt'

        await update.message.reply_document(
            document=bio,
            caption=f"✅ *ניתוח השם '{name}' הושלם!*\n\n📄 הקובץ המצורף מכיל את הניתוח המלא.",
            parse_mode='Markdown'
        )

        user_id = update.effective_user.id
        save_user_input(user_id, {'type': 'name_analysis', 'name': name, 'nikud': nikud_list})

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

    context.user_data.clear()
    return MAIN_MENU

"""
פונקציות עזר לניהול ניקוד שמות בבוט הטלגרם.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from names_manager import NamesManager, nikud_dict_from_nikud_name


def get_nikud_keyboard(nikud_options):
    """
    יוצר מקלדת inline עם אפשרויות ניקוד.

    Args:
        nikud_options: רשימת אפשרויות ניקוד

    Returns:
        InlineKeyboardMarkup
    """
    keyboard = []

    for i, option in enumerate(nikud_options):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"nikud_{i}")])

    keyboard.append([InlineKeyboardButton("הזן ניקוד ידנית", callback_data="nikud_manual")])

    return InlineKeyboardMarkup(keyboard)


def get_nikud_confirmation_keyboard():
    """
    יוצר מקלדת אישור לניקוד קיים.

    Returns:
        InlineKeyboardMarkup
    """
    keyboard = [
        [InlineKeyboardButton("הניקוד נכון ✅", callback_data="nikud_correct")],
        [InlineKeyboardButton("הזן ניקוד ידנית ✏️", callback_data="nikud_manual")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_name_with_nikud_manager(update, context, name, names_manager: NamesManager):
    """
    מטפל בקבלת ניקוד לשם באמצעות מנהל השמות.

    Args:
        update: Update object של טלגרם
        context: Context object של טלגרם
        name: השם ללא ניקוד
        names_manager: מנהל השמות

    Returns:
        טאפל של (state, message_sent) שבו:
        - state: המצב הבא בשיחה או None אם צריך המשך טיפול
        - message_sent: האם נשלחה הודעה
    """
    nikud_name, nikud_options = names_manager.get_nikud_for_name(name)

    if nikud_name:
        # שם עם ניקוד יחיד
        context.user_data['suggested_nikud'] = nikud_name
        await update.message.reply_text(
            f"✅ שמך מופיע במערכת עם הניקוד הבא:\n\n*{nikud_name}*\n\n"
            "אם שמך מנוקד באופן שונה אנא בחר 'הזן ניקוד ידנית'.",
            reply_markup=get_nikud_confirmation_keyboard(),
            parse_mode='Markdown'
        )
        return None, True

    elif len(nikud_options) > 1:
        # מספר אפשרויות ניקוד
        context.user_data['nikud_options'] = nikud_options
        await update.message.reply_text(
            f"⚠️ שמך מופיע במערכת עם {len(nikud_options)} אפשרויות ניקוד.\n"
            "אנא בחר את הניקוד הנכון:",
            reply_markup=get_nikud_keyboard(nikud_options)
        )
        return None, True

    else:
        # השם לא נמצא במאגר
        context.user_data['name_not_in_db'] = True
        await update.message.reply_text(
            "⚠️ שמך לא מופיע במאגר השמות הקיימים.\n"
            "אנא הזן את ניקוד שמך באופן ידני.\n\n"
            "לדוגמה, עבור השם 'דוד':\n"
            "דָּוִד\n\n"
            "או לחלופין, הזן את הניקוד אות אחר אות כפי שהמערכת תבקש."
        )
        return None, True


def apply_nikud_to_name(name: str, nikud_dict: dict) -> str:
    """
    מחבר שם עם דיקשנרי ניקוד ליצירת שם מנוקד.

    Args:
        name: השם המקורי
        nikud_dict: דיקשנרי הניקוד (1-based indices)

    Returns:
        שם מנוקד
    """
    result = []
    for i, char in enumerate(name, 1):
        result.append(char)
        if i in nikud_dict:
            result.append(nikud_dict[i])
    return ''.join(result)

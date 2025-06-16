import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from src.NameAnalysis import NameAnalysis

# לוודא שהנתיב היחסי 'data/' מיושר לתיקיית הפרויקט
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# הגדרת logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# טעינת טוקן
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """תגובה לפקודת /start"""
    await update.message.reply_text(
        "שלום! שלח שם ואחריו ניקודים לכל אות, לדוגמה: עמי פתח חיריק ריק"
    )

async def handle_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מעבד טקסט בפורמט: שם ניקוד1 ניקוד2 ..."""
    parts = update.message.text.strip().split()
    if len(parts) < 2:
        await update.message.reply_text(
            "פורמט לא תקין. יש לשלוח: שם ניקוד1 ניקוד2 ..."
        )
        return

    name = parts[0]
    nikud_list = parts[1:]
    if len(nikud_list) != len(name):
        await update.message.reply_text(
            f"אורך השם {len(name)}, אך סיפקת {len(nikud_list)} ניקודים. אנא תקן."
        )
        return

    nikud_dict = {i+1: nikud_list[i] for i in range(len(name))}
    try:
        analyzer = NameAnalysis(name, nikud_dict)
        result_lines = analyzer.analyze_name()
        full_text = "\n".join(result_lines)
        for start_idx in range(0, len(full_text), 4096):
            await update.message.reply_text(full_text[start_idx:start_idx+4096])
    except Exception as e:
        logging.error(f"Error analyzing name: {e}")
        await update.message.reply_text(f"שגיאה בניתוח השם: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_analysis))

    # הפעלה באמצעות polling
    app.run_polling()


if __name__ == "__main__":
    main()

import os
import logging
import re
ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from src.name_analysis.NameAnalysis import NameAnalysis

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
        from io import BytesIO

        # נקה ANSI וקודד ל-bytes
        cleaned = ANSI_RE.sub('', full_text)
        bio = BytesIO(cleaned.encode('utf-8'))
        bio.name = 'analysis.txt'

        # שלח כקובץ בודד
        await update.message.reply_document(document=bio)
    except Exception as e:
        logging.error(f"Error analyzing name: {e}")
        await update.message.reply_text(f"שגיאה בניתוח השם: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_analysis))

    import os

    if os.getenv("FLY_APP_NAME"):
        # הפעלה ב-Fly: מאזין ב-PORT ומגדיר webhook
        url_path = os.environ["WEBHOOK_URL"].rstrip("/").rsplit("/", 1)[-1]
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            url_path=url_path,
            webhook_url=os.environ["WEBHOOK_URL"],
        )
    else:
        # פיתוח מקומי
        app.run_polling()


if __name__ == "__main__":
    main()

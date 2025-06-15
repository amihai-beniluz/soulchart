import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from src.api import analyze_name

# טעינת משתנים מהקובץ .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

MAX_LENGTH = 4096

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    if len(parts) < 2:
        await update.message.reply_text("❗ אנא שלח פורמט תקין: שם ניקוד1 ניקוד2 ...")
        return

    name = parts[0]
    nikud_list = parts[1:]

    if len(nikud_list) != len(name):
        await update.message.reply_text(f"❗ אורך הניקוד ({len(nikud_list)}) לא תואם לאורך השם ({len(name)}).")
        return

    nikud_dict = {i + 1: nikud_list[i] for i in range(len(name))}

    try:
        result = analyze_name(name, nikud_dict)

        # שליחה בפיצול אם הפלט ארוך
        for i in range(0, len(result), MAX_LENGTH):
            await update.message.reply_text(result[i:i + MAX_LENGTH])

    except Exception as e:
        await update.message.reply_text("❌ שגיאה:\n" + str(e))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()

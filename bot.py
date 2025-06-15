import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# טען משתנים
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Message received: {update.message.text}")
    text = (update.message.text or "").strip()
    parts = text.split()
    if len(parts) < 2:
        await update.message.reply_text("❗ פורמט: <שם> <ניקוד1> <ניקוד2> ...")
        return
    name, nk = parts[0], parts[1:]
    await update.message.reply_text(f"✔️ קיבלתי את השם {name} עם ניקוד: {nk}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    print("🚀 SoulChart bot starting up!")
    import asyncio

    async def main():
        await app.bot.set_webhook(url=WEBHOOK_URL)

        await app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_path="/webhook",
        )

    asyncio.run(main())


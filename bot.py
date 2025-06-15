import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # למשל: https://amihai.fly.dev/webhook
PORT = int(os.getenv("PORT", 8443))

app = ApplicationBuilder().token(BOT_TOKEN).build()

@app.on_message()
async def handle_message(update, context):
    await update.message.reply_text("התקבל!")

if __name__ == "__main__":
    import asyncio

    async def main():
        print("🚀 SoulChart bot starting up!")
        await app.bot.set_webhook(url=WEBHOOK_URL)

        await app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )

    asyncio.run(main())

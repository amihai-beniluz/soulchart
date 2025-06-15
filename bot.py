from telegram.ext import Application
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8443))

app = Application.builder().token(BOT_TOKEN).build()

if __name__ == "__main__":
    import asyncio

    async def main():
        print("🚀 SoulChart bot starting up!")
        await app.bot.set_webhook(url=WEBHOOK_URL)
        await app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL
        )

    asyncio.run(main())

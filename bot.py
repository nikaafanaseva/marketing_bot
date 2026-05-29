import os, sys, asyncio, logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', force=True)
logger = logging.getLogger(__name__)

TG_TOKEN = os.getenv('TG_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
HF_TOKEN = os.getenv('HF_TOKEN')
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

hf_client = InferenceClient(token=HF_TOKEN)
SYSTEM = "Ты — эксперт по маркетингу в России. Учитывай российские площадки, законы и платежи. Отвечай кратко."

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("👋 Привет! Спрашивай про маркетинг в РФ.")

async def handle(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.chat.send_action("typing")
    try:
        resp = await asyncio.to_thread(
            hf_client.chat,
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":u.message.text}],
            model=HF_MODEL, max_tokens=512, timeout=25
        )
        await u.message.reply_text(resp.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error: {e}")
        await u.message.reply_text("⚠️ Ошибка. Попробуйте позже.")

def main():
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_webhook(listen="0.0.0.0", port=int(os.getenv("PORT",8000)), url_path="webhook", webhook_url=f"{WEBHOOK_URL}/webhook")

if __name__ == "__main__":
    main()

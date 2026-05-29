import os
import sys

# === ОТЛАДКА: вывод с немедленной отправкой в логи ===
print("🚀 BOT STARTED", flush=True)
print(f"🔍 TG_TOKEN: {'✅' if os.getenv('TG_BOT_TOKEN') else '❌'}", flush=True)
print(f"🔍 HF_TOKEN: {'✅' if os.getenv('HF_TOKEN') else '❌'}", flush=True)
print(f"🔍 WEBHOOK_URL: {'✅' if os.getenv('WEBHOOK_URL') else '❌'}", flush=True)
print(f"🐍 Python: {sys.version}", flush=True)

# Проверка переменных
if not all([os.getenv('TG_BOT_TOKEN'), os.getenv('HF_TOKEN'), os.getenv('WEBHOOK_URL')]):
    print("💥 MISSING ENV VARS — проверьте Render!", flush=True)
    sys.exit(1)

# === Основной код ===
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', force=True)
logger = logging.getLogger(__name__)

TG_TOKEN = os.getenv("TG_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

hf = InferenceClient(token=HF_TOKEN)

SYSTEM = (
    "Ты — эксперт по маркетингу в России. Учитывай: российские площадки (VK, Telegram, Яндекс, Ozon, WB), "
    "законы (ФЗ о рекламе, 152-ФЗ), платежи (СБП, ЮKassa). Отвечай кратко и по делу."
)

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("👋 Привет! Спрашивай про маркетинг в РФ.")

async def handle(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.chat.send_action("typing")
    try:
        resp = await asyncio.to_thread(
            hf.chat,
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":u.message.text}],
            model=HF_MODEL, max_tokens=1024, temperature=0.7, timeout=30
        )
        await u.message.reply_text(resp.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error: {e}")
        await u.message.reply_text("⚠️ Ошибка. Попробуйте позже.")

def main():
    print("⚙️ Создаю приложение...", flush=True)
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print(f"🔗 Запускаю webhook: {WEBHOOK_URL}/webhook", flush=True)
    app.run_webhook(listen="0.0.0.0", port=int(os.getenv("PORT",8000)), url_path="webhook", webhook_url=f"{WEBHOOK_URL}/webhook")

if __name__ == "__main__":
    main()

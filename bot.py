import os
import sys
import asyncio
import logging

print("🚀 BOT STARTED", flush=True)
print(f"🐍 Python: {sys.version}", flush=True)

# === ФИКС ДЛЯ PYTHON 3.14+ ===
# Явно создаём event loop, иначе get_event_loop() выбросит ошибку
if sys.version_info >= (3, 14):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
# ============================

# Проверка переменных
tg = os.getenv('TG_BOT_TOKEN')
hf = os.getenv('HF_TOKEN')
webhook = os.getenv('WEBHOOK_URL')

if not all([tg, hf, webhook]):
    print("💥 MISSING ENV VARS!", flush=True)
    sys.exit(1)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', force=True)
logger = logging.getLogger(__name__)

TG_TOKEN = tg
WEBHOOK_URL = webhook
HF_TOKEN = hf
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

hf_client = InferenceClient(token=HF_TOKEN)

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
            hf_client.chat,
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
    
    # === ФИКС: запускаем run_webhook внутри существующего loop ===
    if sys.version_info >= (3, 14):
        # Для Python 3.14+ запускаем асинхронно внутри существующего цикла
        loop = asyncio.get_event_loop()
        loop.run_until_complete(app.initialize())
        loop.run_until_complete(app.updater.start_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook",
        ))
        loop.run_forever()
    else:
        # Для старых версий — обычный запуск
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )

if __name__ == "__main__":
    main()

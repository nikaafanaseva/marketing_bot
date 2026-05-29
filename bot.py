import os
import sys
import asyncio
import logging

# === ФИКС ДЛЯ PYTHON 3.14: явно создаём loop ДО импорта телеграма ===
if sys.version_info >= (3, 14):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()
# ================================================================

print("🚀 BOT STARTED", flush=True)

tg = os.getenv('TG_BOT_TOKEN')
hf = os.getenv('HF_TOKEN')
webhook = os.getenv('WEBHOOK_URL')

if not all([tg, hf, webhook]):
    print("💥 MISSING ENV VARS!", flush=True)
    sys.exit(1)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', force=True)
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"📩 ПОЛУЧЕН /start от {update.effective_user.id}")
    try:
        await update.message.reply_text("👋 Привет! Спрашивай про маркетинг в РФ.")
        logger.info("✅ Ответ отправлен")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    logger.info(f"📩 ПОЛУЧЕНО от {user_id}: '{text}'")
    
    try:
        await update.message.chat.send_action("typing")
        resp = await asyncio.to_thread(
            hf_client.chat,
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":text}],
            model=HF_MODEL, max_tokens=512, temperature=0.7, timeout=25
        )
        await update.message.reply_text(resp.choices[0].message.content)
        logger.info("✅ Ответ отправлен")
    except Exception as e:
        logger.error(f"❌ Ошибка: {type(e).__name__}: {e}")
        await update.message.reply_text("⚠️ Ошибка. Попробуйте позже.")

async def run_bot():
    """Асинхронный запуск — обходит проблему с get_event_loop()"""
    logger.info("⚙️ Создаю приложение...")
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info(f"🔗 Запускаю webhook: {WEBHOOK_URL}/webhook")
    
    # Инициализация и запуск вручную
    await app.initialize()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        url_path="webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook",
    )
    logger.info("✅ Application started")
    await asyncio.Event().wait()  # держим бота живым

def main():
    # Запускаем асинхронную функцию в нашем заранее созданном loop
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    main()

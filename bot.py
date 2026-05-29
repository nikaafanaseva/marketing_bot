# === ОТЛАДКА: простые принты, которые точно появятся в логе ===
print("🚀 bot.py STARTED")
print(f"🔍 TG_TOKEN: {'✅' if __import__('os').environ.get('TG_BOT_TOKEN') else '❌ MISSING'}")
print(f"🔍 HF_TOKEN: {'✅' if __import__('os').environ.get('HF_TOKEN') else '❌ MISSING'}")
print(f"🔍 WEBHOOK_URL: {'✅' if __import__('os').environ.get('WEBHOOK_URL') else '❌ MISSING'}")
# =============================================================

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    force=True  # гарантируем, что логи пойдут в консоль
)
logger = logging.getLogger(__name__)

TG_TOKEN = os.getenv("TG_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

hf_client = InferenceClient(token=HF_TOKEN)

SYSTEM_PROMPT = (
    "Ты — senior-эксперт по маркетингу в России. "
    "Отвечай профессионально, учитывая локальную специфику: "
    "российские площадки (VK, Telegram Ads, Яндекс.Директ, Ozon, Wildberries, Avito), "
    "законодательство (ФЗ «О рекламе», маркировка рекламы, 152-ФЗ), "
    "платёжные системы (СБП, ЮKassa). "
    "Используй данные 2024-2025 гг. Если информации нет — говори честно. "
    "Отвечай структурированно, кратко, используй списки."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-эксперт по маркетингу в РФ.\n"
        "Спрашивай о трендах, рекламе, маркетплейсах или законах."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    user_text = update.message.text
    logger.info(f"Получено: {user_text}")

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
        response = await asyncio.to_thread(
            hf_client.chat,
            messages=messages,
            model=HF_MODEL,
            max_tokens=1024,
            temperature=0.7,
            timeout=30
        )
        bot_reply = response.choices[0].message.content
        await update.message.reply_text(bot_reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Ошибка. Попробуйте позже.")

def main():
    try:
        print("✅ ПЕРЕД созданием Application")
        app = Application.builder().token(TG_TOKEN).build()
        print("✅ ПОСЛЕ создания Application")
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        print(f"🔗 Запуск webhook на порту {os.getenv('PORT', 8000)}")
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА в main(): {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    print("🎯 Вход в __main__")
    main()

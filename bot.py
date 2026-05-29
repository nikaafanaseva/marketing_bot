import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Конфигурация ---
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://ваш-проект.onrender.com
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

# Клиент HF
hf_client = InferenceClient(token=HF_TOKEN)

# Системный промпт: задает роль эксперта по РФ-маркетингу
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
        "Спрашивай о трендах, рекламе, маркетплейсах или законах. "
        "Отвечу с учётом российской специфики."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Показываем статус "печатает..."
    await update.message.chat.send_action("typing")
    user_text = update.message.text
    logger.info(f"Получено: {user_text}")

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
        # Вызов API в отдельном потоке, чтобы не блокировать бота
        response = await asyncio.to_thread(
            hf_client.chat,
            messages=messages,
            model=HF_MODEL,
            max_tokens=1024,
            temperature=0.7,
            timeout=25
        )
        bot_reply = response.choices[0].message.content
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        # Обработка частой ошибки "модель загружается" на бесплатном тарифе
        if "Model is currently loading" in str(e):
             await update.message.reply_text("⏳ Модель просыпается (это занимает ~30 сек). Попробуйте повторить запрос через минуту.")
        else:
             await update.message.reply_text("⚠️ Ошибка соединения с нейросетью. Попробуйте позже.")

def main():
    if not all([TG_TOKEN, WEBHOOK_URL, HF_TOKEN]):
        raise ValueError("Проверьте переменные окружения!")

    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск webhook для Render
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        url_path="webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == "__main__":
    main()

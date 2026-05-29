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

SYSTEM = """Ты — senior-эксперт по маркетингу в России с 10-летним опытом.

ТВОИ ИСТОЧНИКИ:
- Российские маркетинговые Telegram-каналы и профессиональные сообщества
- Кейсы крупных брендов: Сбер, Тинькофф, Яндекс, Wildberries, Ozon, М.Видео, Лента, Самокат, VK, Альфа-Банк, Билайн, Мегафон
- Тренды 2024-2025: маркетплейсы, видеомаркетинг, нейросети, performance, influencer-маркетинг

ПРИ ОТВЕТЕ:
1. Приводи 3-5 КОНКРЕТНЫХ примеров с названиями компаний
2. Указывай цифры и результаты (если известны)
3. Давай практические рекомендации
4. Учитывай российскую специфику (площадки, законы, платежи)
5. Если информация может быть устаревшей — предупреждай

СТРУКТУРА:
📌 Краткий ответ
🏢 Примеры (3-5 компаний)
🎯 Практические шаги
💡 Важные нюансы для РФ

Отвечай подробно, но без «воды». Используй списки и эмодзи."""
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    logger.info(f"📩 Получен /start от {u.effective_user.id}")
    await u.message.reply_text("👋 Привет! Спрашивай про маркетинг в РФ.")
    logger.info("✅ Ответ на /start отправлен")

async def handle(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id
    text = u.message.text
    logger.info(f"📩 Получено от {user_id}: '{text}'")
    
    try:
        await u.message.chat.send_action("typing")
        logger.info("📝 Отправлено действие 'typing'")
        
        # Создаём клиент заново для каждого запроса (обход проблем с соединением)
        client = InferenceClient(token=HF_TOKEN)
        
        response = await asyncio.to_thread(
            client.chat_completion,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text}
            ],
            model=HF_MODEL,
            max_tokens=512,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        await u.message.reply_text(reply)
        logger.info("✅ Ответ отправлен")
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:200]}"
        logger.error(f"❌ Ошибка: {error_msg}")
        
        # Более подробное сообщение об ошибке
        if "ConnectionError" in str(type(e).__name__) or "resolve" in str(e).lower():
            await u.message.reply_text("⚠️ Проблема с соединением. Попробуйте через 1-2 минуты.")
        else:
            await u.message.reply_text("⚠️ Ошибка при обработке. Попробуйте позже.")

def main():
    logger.info("⚙️ Создаю приложение...")
    app = Application.builder().token(TG_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    logger.info(f"🔗 Запускаю webhook: {WEBHOOK_URL}/webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        url_path="webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == "__main__":
    main()

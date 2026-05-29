import os
import sys

print("=" * 60, flush=True)
print("🚀 BOT STARTED", flush=True)
print(f"🐍 Python: {sys.version}", flush=True)
print("=" * 60, flush=True)

# Проверка переменных
print("1️⃣ Проверка переменных окружения...", flush=True)
tg = os.getenv('TG_BOT_TOKEN')
hf = os.getenv('HF_TOKEN')
webhook = os.getenv('WEBHOOK_URL')

print(f"   TG_BOT_TOKEN: {'✅' if tg else '❌'}", flush=True)
print(f"   HF_TOKEN: {'✅' if hf else '❌'}", flush=True)
print(f"   WEBHOOK_URL: {'✅' if webhook else '❌'}", flush=True)

if not all([tg, hf, webhook]):
    print("💥 MISSING ENV VARS!", flush=True)
    sys.exit(1)

print("✅ Все переменные на месте!", flush=True)

# Импорт библиотек
print("2️⃣ Импорт библиотек...", flush=True)
try:
    import telegram
    print(f"   ✅ telegram version: {telegram.__version__}", flush=True)
except Exception as e:
    print(f"   ❌ Ошибка импорта telegram: {e}", flush=True)
    sys.exit(1)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    print("   ✅ telegram.ext импортирован", flush=True)
except Exception as e:
    print(f"   ❌ Ошибка импорта telegram.ext: {e}", flush=True)
    sys.exit(1)

try:
    from huggingface_hub import InferenceClient
    print("   ✅ huggingface_hub импортирован", flush=True)
except Exception as e:
    print(f"   ❌ Ошибка импорта huggingface_hub: {e}", flush=True)
    sys.exit(1)

# Создание приложения
print("3️⃣ Создание Application...", flush=True)
try:
    print("   Создаю builder...", flush=True)
    builder = Application.builder()
    print("   ✅ Builder создан", flush=True)
    
    print("   Добавляю токен...", flush=True)
    builder_with_token = builder.token(tg)
    print("   ✅ Токен добавлен", flush=True)
    
    print("   Building application...", flush=True)
    app = builder_with_token.build()
    print("   ✅ Application создана!", flush=True)
except Exception as e:
    print(f"   ❌ Ошибка при создании Application: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Добавление обработчиков
print("4️⃣ Добавление обработчиков...", flush=True)
try:
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("👋 Привет!")
    
    async def handle(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("Получил сообщение")
    
    app.add_handler(CommandHandler("start", start))
    print("   ✅ CommandHandler добавлен", flush=True)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("   ✅ MessageHandler добавлен", flush=True)
except Exception as e:
    print(f"   ❌ Ошибка при добавлении обработчиков: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Запуск webhook
print("5️⃣ Запуск webhook...", flush=True)
print(f"   URL: {webhook}/webhook", flush=True)
print(f"   PORT: {os.getenv('PORT', 8000)}", flush=True)

try:
    print("   Вызываю run_webhook()...", flush=True)
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        url_path="webhook",
        webhook_url=f"{webhook}/webhook"
    )
    print("   ✅ Webhook запущен!", flush=True)
except Exception as e:
    print(f"   ❌ Ошибка при запуске webhook: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60, flush=True)
print("🎉 БОТ ЗАПУЩЕН УСПЕШНО!", flush=True)
print("=" * 60, flush=True)

import os
import asyncio
import random
import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Загружаем переменные окружения
load_dotenv()
openai.api_key = os.getenv("DEEPSEEK_API_KEY")
openai.api_base = "https://api.deepseek.com"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

SYSTEM_PROMPT = """
Ты — Поварёшка, весёлый и немного дерзкий шеф-повар.
ЖЁСТКИЕ ПРАВИЛА (нарушать нельзя):
1. Отвечаешь ТОЛЬКО когда тебя позвали: упоминание @Povareshka_bot или ответ на твоё сообщение.
2. Ответ всегда не длиннее 2 предложений.
3. 30% ответов — один эмодзи (🔥, 😋, 🍳 и т.п.).
4. Стиль: дерзкий, но заботливый, как старый шеф.
5. Запрещены: политика, религия, медицина, оскорбления.
6. Если вопрос не про еду — переводишь в шутку про готовку.
7. Каждое утро ровно в 10:00 по МСК ты задаёшь в чат вопрос: "Доброе утро, гурманы! Что сегодня планируете на ужин? 🍽️"
"""

CHAT_ID = None  # сюда сохранится ID чата при первом обращении

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    msg = update.message
    if msg is None or msg.text is None:
        return

    chat_id = msg.chat_id
    text = msg.text

    # Сохраняем чат для утренних сообщений
    if CHAT_ID is None:
        CHAT_ID = chat_id
        print(f"Запомнен chat_id: {CHAT_ID}")

    # Проверка: обращаются ли к боту
    bot_username = f"@{context.bot.username}"
    is_mentioned = bot_username.lower() in text.lower()
    is_reply = msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id

    if not (is_mentioned or is_reply):
        return

    # Имитация живого человека
    await asyncio.sleep(random.randint(2, 5))

    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=80
        )
        reply = response.choices[0].message.content.strip()
        await msg.reply_text(reply)
    except Exception as e:
        await msg.reply_text("Упс, прихватка подгорела! 🔥 Попробуй позже.")
        print(f"Ошибка DeepSeek: {e}")

async def morning_question(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID is None:
        return
    try:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="Доброе утро, гурманы! Что сегодня планируете на ужин? 🍽️"
        )
    except Exception as e:
        print(f"Ошибка утреннего сообщения: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Планировщик: 10:00 МСК = 7:00 UTC
    from datetime import time
    app.job_queue.run_daily(
        morning_question,
        time=time(hour=7, minute=0, second=0),
        days=(0, 1, 2, 3, 4, 5, 6)
    )

    print("Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()

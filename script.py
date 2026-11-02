import os
from anthropic import AsyncAnthropic
from telegram.ext import ApplicationBuilder, MessageHandler, filters

claude = AsyncAnthropic()  # ключ берёт из ANTHROPIC_API_KEY
OWNER = int(os.environ["OWNER_ID"])
history = {}

async def reply(update, context):
    if update.effective_user.id != OWNER:
        return
    chat = history.setdefault(update.effective_chat.id, [])
    chat.append({"role": "user", "content": update.message.text})
    r = await claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1000,
        messages=chat[-21:],
    )
    text = r.content[0].text
    chat.append({"role": "assistant", "content": text})
    await update.message.reply_text(text)

app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
app.run_polling()
import os
from anthropic import AsyncAnthropic
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup

claude = AsyncAnthropic()
OWNER = int(os.environ["OWNER_ID"])
MODELS = {
    "haiku": "claude-haiku-5-5",
    "sonnet": "claude-sonnet-5-5",
    "opus": "claude-opus-5-5",
}
history = {}
total = {"in": 0, "out": 0}

BTN_MODELS = {"⚡ Быстрая": "haiku", "⚖️ Средняя": "sonnet", "🧠 Мощная": "opus"}
BTN_STATS = "📊 Статистика"
BTN_CLEAR = "🧹 Очистить"

KB = ReplyKeyboardMarkup(
    [list(BTN_MODELS), [BTN_STATS, BTN_CLEAR]],
    resize_keyboard=True,
)

async def reply(update, context):
    if update.effective_user.id != OWNER:
        return
    model = context.bot_data.get("model", MODELS["sonnet"])
    chat = history.setdefault(update.effective_chat.id, [])
    chat.append({"role": "user", "content": update.message.text})
    r = await claude.messages.create(model=model, max_tokens=1000, messages=chat[-21:])
    text = r.content[0].text
    chat.append({"role": "assistant", "content": text})
    total["in"] += r.usage.input_tokens
    total["out"] += r.usage.output_tokens
    await update.message.reply_text(
        f"{text}\n\n{r.model} | вход {r.usage.input_tokens}, выход {r.usage.output_tokens}"
    )

async def set_model(update, context):
    if update.effective_user.id != OWNER:
        return
    if context.args and context.args[0] in MODELS:
        context.bot_data["model"] = MODELS[context.args[0]]
    now = context.bot_data.get("model", MODELS["sonnet"])
    await update.message.reply_text(f"Сейчас: {now}\nВарианты: /model haiku, /model sonnet, /model opus")

async def stats(update, context):
    if update.effective_user.id != OWNER:
        return
    await update.message.reply_text(f"С запуска: вход {total['in']}, выход {total['out']}")

async def clear(update, context):
    if update.effective_user.id != OWNER:
        return
    history.pop(update.effective_chat.id, None)
    await update.message.reply_text("Диалог очищен")

async def start(update, context):
    if update.effective_user.id != OWNER:
        return
    await update.message.reply_text("Выберите действие", reply_markup=KB)

async def button(update, context):
    if update.effective_user.id != OWNER:
        return
    t = update.message.text
    if t in BTN_MODELS:
        context.bot_data["model"] = MODELS[BTN_MODELS[t]]
        await update.message.reply_text(f"Сейчас: {context.bot_data['model']}")
    elif t == BTN_STATS:
        await stats(update, context)
    elif t == BTN_CLEAR:
        await clear(update, context)

app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("model", set_model))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(MessageHandler(filters.Text(list(BTN_MODELS) + [BTN_STATS, BTN_CLEAR]), button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
app.run_polling()

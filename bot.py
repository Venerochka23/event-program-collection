import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from handlers_add import add_conversation_handler
from handlers_search import list_command, find_conversation_handler, open_project 
from telegram.ext import CallbackQueryHandler
from handlers_manage import (
    my_projects, manage_conversation_handler,
    start_delete, confirm_delete, cancel_delete, stats_command,
)


load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()]

logging.basicConfig(level=logging.INFO)

HELP_TEXT = (
    "Доступные команды:\n\n"
    "/list — список актуальных проектов за последний месяц 📜\n"
    "/find — найти проект по названию, дате/периоду и городу 🔍\n"
    "/add — добавить новый проект ✏️\n"
    "/myprojects — мои проекты (редактирование и удаление) 📓\n"
    "/cancel — отменить текущую операцию 🚫\n"
    "/help — это сообщение ⁉️\n\n"
    "По всем вопросам: @darkendless"
)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Привет! Буду рад быть полезным тебе сегодня🌸\n\n" + HELP_TEXT
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Операция отменена. Возвращаю в главное меню.\n\n" + HELP_TEXT)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("myprojects", my_projects))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(add_conversation_handler)
    app.add_handler(find_conversation_handler)
    app.add_handler(manage_conversation_handler)
    app.add_handler(CallbackQueryHandler(open_project, pattern="^open:"))
    app.add_handler(CallbackQueryHandler(start_delete, pattern="^delete:"))
    app.add_handler(CallbackQueryHandler(confirm_delete, pattern="^delete_confirm:"))
    app.add_handler(CallbackQueryHandler(cancel_delete, pattern="^delete_cancel:"))
    app.add_handler(CommandHandler("cancel", cancel))
    print("Бот проектов запущен, слушает сообщения...")
    app.run_polling()


if __name__ == "__main__":
    main() 
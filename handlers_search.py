from telegram import Update
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)
from datetime import datetime

from database import list_recent_projects, search_projects, get_project
from keyboards import open_project_keyboard, find_skip_keyboard, manage_actions_keyboard
from access import is_admin
from formatting import format_card

FIND_NAME, FIND_DATE, FIND_CITY = range(3)

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = list_recent_projects(days=30)
    if not projects:
        await update.message.reply_text("За последний месяц проектов пока не добавлено.")
        return

    for p in projects:
        await update.message.reply_text(format_card(p), reply_markup=keyboard_for(p, update.effective_user.id))


async def open_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])

    project = get_project(project_id)
    if not project:
        await query.message.reply_text("Этот проект больше не существует.")
        return

    await query.message.reply_text(format_card(project, full=True))


# --- /find ---

async def find_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["find_filters"] = {}
    await update.message.reply_text(
        "Название (часть названия) — или нажми «Пропустить»:",
        reply_markup=find_skip_keyboard("name"),
    )
    return FIND_NAME


async def ask_date(message_target, context: ContextTypes.DEFAULT_TYPE):
    await message_target.reply_text(
        "Дата или период (ДД.ММ.ГГГГ или ДД.ММ.ГГГГ-ДД.ММ.ГГГГ) — или «Пропустить»:",
        reply_markup=find_skip_keyboard("date"),
    )


async def got_find_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["find_filters"]["name"] = update.message.text.strip()
    await ask_date(update.message, context)
    return FIND_DATE


async def skip_find_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    await ask_date(query.message, context)
    return FIND_DATE


def parse_date_or_period(text: str):
    text = text.strip()
    parts = text.split("-")
    try:
        if len(parts) == 2:
            return (
                datetime.strptime(parts[0].strip(), "%d.%m.%Y").date(),
                datetime.strptime(parts[1].strip(), "%d.%m.%Y").date(),
            )
        d = datetime.strptime(text, "%d.%m.%Y").date()
        return d, d
    except ValueError:
        return None


async def ask_city(message_target, context: ContextTypes.DEFAULT_TYPE):
    await message_target.reply_text(
        "Город/место — или «Пропустить»:",
        reply_markup=find_skip_keyboard("city"),
    )


async def got_find_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parsed = parse_date_or_period(update.message.text)
    if not parsed:
        await update.message.reply_text("Не похоже на дату/период. Формат: ДД.ММ.ГГГГ или ДД.ММ.ГГГГ-ДД.ММ.ГГГГ")
        return FIND_DATE

    context.user_data["find_filters"]["date_from"], context.user_data["find_filters"]["date_to"] = parsed
    await ask_city(update.message, context)
    return FIND_CITY


async def skip_find_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    await ask_city(query.message, context)
    return FIND_CITY


async def run_search_and_reply(message_target, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    f = context.user_data.get("find_filters", {})
    results = search_projects(
        name=f.get("name"),
        date_from=f.get("date_from"),
        date_to=f.get("date_to"),
        city=f.get("city"),
    )

    if not results:
        await message_target.reply_text("По этим фильтрам ничего не нашлось.")
    else:
        for p in results:
            await message_target.reply_text(format_card(p), reply_markup=keyboard_for(p, user_id))

    context.user_data.pop("find_filters", None)


async def got_find_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["find_filters"]["city"] = update.message.text.strip()
    await run_search_and_reply(update.message, context, update.effective_user.id)
    return ConversationHandler.END


async def skip_find_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    await run_search_and_reply(query.message, context, update.effective_user.id)
    return ConversationHandler.END


async def find_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("find_filters", None)
    await update.message.reply_text("Поиск отменён.")
    return ConversationHandler.END


def keyboard_for(project: dict, user_id: int):
    if project["created_by_user_id"] == user_id or is_admin(user_id):
        return manage_actions_keyboard(project["id"])
    return open_project_keyboard(project["id"])


find_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("find", find_start)],
    states={
        FIND_NAME: [
            CallbackQueryHandler(skip_find_name, pattern="^find_skip:name$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, got_find_name),
        ],
        FIND_DATE: [
            CallbackQueryHandler(skip_find_date, pattern="^find_skip:date$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, got_find_date),
        ],
        FIND_CITY: [
            CallbackQueryHandler(skip_find_city, pattern="^find_skip:city$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, got_find_city),
        ],
    },
    fallbacks=[CommandHandler("cancel", find_cancel)],
)
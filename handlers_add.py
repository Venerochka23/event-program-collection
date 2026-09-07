from telegram import Update
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)
from datetime import datetime

from database import list_categories, add_project
from keyboards import categories_keyboard, confirm_keyboard, skip_keyboard

TITLE, CATEGORY, START_DATE, END_DATE, VENUE, ORGANIZER, DESCRIPTION, LINK, CONTACT, CONFIRM = range(10)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_project"] = {}
    await update.message.reply_text("Название проекта:")
    return TITLE


async def got_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_project"]["title"] = update.message.text

    categories = list_categories()
    context.user_data["_categories_cache"] = {c["id"]: c for c in categories}

    await update.message.reply_text("Категория:", reply_markup=categories_keyboard(categories))
    return CATEGORY


async def got_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split(":")[1])
    context.user_data["new_project"]["category_id"] = category_id

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text("Дата начала (в формате ДД.ММ.ГГГГ):")
    return START_DATE


async def got_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parsed = datetime.strptime(update.message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text("Не похоже на дату в формате ДД.ММ.ГГГГ, попробуй ещё раз:")
        return START_DATE

    context.user_data["new_project"]["start_date"] = parsed
    await update.message.reply_text(
        "Дата окончания (ДД.ММ.ГГГГ) — необязательно, если её нет, отправь: -"
    )
    return END_DATE


async def got_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "-":
        context.user_data["new_project"]["end_date"] = None
    else:
        try:
            parsed = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            await update.message.reply_text("Не похоже на дату. Введи ДД.ММ.ГГГГ или отправь: -")
            return END_DATE
        context.user_data["new_project"]["end_date"] = parsed

    await update.message.reply_text("Место проведения:")
    return VENUE


async def got_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_project"]["venue"] = update.message.text
    await update.message.reply_text("Организатор:")
    return ORGANIZER


async def got_organizer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_project"]["organizer"] = update.message.text
    await update.message.reply_text("Описание:")
    return DESCRIPTION


async def got_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_project"]["description"] = update.message.text
    await update.message.reply_text(
        "Ссылка (если нет — нажми «Пропустить»):",
        reply_markup=skip_keyboard("link"),
    )
    return LINK


async def ask_contact(message_target, context: ContextTypes.DEFAULT_TYPE):
    await message_target.reply_text(
        "Контактная информация (если нет — нажми «Пропустить»):",
        reply_markup=skip_keyboard("contact"),
    )


async def got_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_project"]["link"] = update.message.text
    await ask_contact(update.message, context)
    return CONTACT


async def skip_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_project"]["link"] = None
    await query.edit_message_reply_markup(reply_markup=None)
    await ask_contact(query.message, context)
    return CONTACT


def build_preview(data: dict, category: dict) -> str:
    end_date_str = data["end_date"].strftime("%d.%m.%Y") if data.get("end_date") else "—"
    return (
        f"Название: {data['title']}\n"
        f"Категория: {category['emoji']} {category['name']}\n"
        f"Дата: {data['start_date'].strftime('%d.%m.%Y')}–{end_date_str}\n"
        f"Место: {data.get('venue') or '—'}\n"
        f"Организатор: {data.get('organizer') or '—'}\n"
        f"Описание: {data.get('description') or '—'}\n"
        f"Ссылка: {data.get('link') or '—'}\n"
        f"Контакт: {data.get('contact_info') or '—'}"
    )


async def show_preview(message_target, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data["new_project"]
    category = context.user_data["_categories_cache"][data["category_id"]]
    await message_target.reply_text(build_preview(data, category), reply_markup=confirm_keyboard())


async def got_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_project"]["contact_info"] = update.message.text
    await show_preview(update.message, context)
    return CONFIRM


async def skip_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_project"]["contact_info"] = None
    await query.edit_message_reply_markup(reply_markup=None)
    await show_preview(query.message, context)
    return CONFIRM


async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]

    await query.edit_message_reply_markup(reply_markup=None)

    if action == "save":
        data = context.user_data["new_project"]
        add_project(data, update.effective_user.id)
        await query.message.reply_text("Сохранено.")
        context.user_data.clear()
        return ConversationHandler.END

    elif action == "cancel":
        await query.message.reply_text("Отменено.")
        context.user_data.clear()
        return ConversationHandler.END

    elif action == "edit":
        context.user_data["new_project"] = {}
        await query.message.reply_text("Хорошо, начнём заново. Название проекта:")
        return TITLE


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Добавление отменено.")
    return ConversationHandler.END


add_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("add", add_start)],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_title)],
        CATEGORY: [CallbackQueryHandler(got_category, pattern="^cat:")],
        START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_start_date)],
        END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_end_date)],
        VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_venue)],
        ORGANIZER: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_organizer)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_description)],
        LINK: [
            CallbackQueryHandler(skip_link, pattern="^skip:link$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, got_link),
        ],
        CONTACT: [
            CallbackQueryHandler(skip_contact, pattern="^skip:contact$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, got_contact),
        ],
        CONFIRM: [CallbackQueryHandler(handle_confirm, pattern="^confirm:")],
    },
    fallbacks=[CommandHandler("cancel", add_cancel)],
)
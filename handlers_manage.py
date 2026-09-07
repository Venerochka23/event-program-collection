from telegram import Update
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)
from datetime import datetime

from database import (
    list_user_projects, get_project, update_project, delete_project,
    list_categories, count_total_projects, count_projects_by_category,
)
from keyboards import manage_actions_keyboard, field_choice_keyboard, categories_keyboard, delete_confirm_keyboard, FIELD_LABELS
from formatting import format_card
from access import is_admin

CHOOSE_FIELD, EDIT_VALUE = range(2)
DATE_FIELDS = {"start_date", "end_date"}


def can_manage(project: dict, user_id: int) -> bool:
    return project["created_by_user_id"] == user_id or is_admin(user_id)


async def my_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    projects = list_user_projects(user_id)
    if not projects:
        await update.message.reply_text("У тебя пока нет добавленных проектов.")
        return
    for p in projects:
        await update.message.reply_text(format_card(p), reply_markup=manage_actions_keyboard(p["id"]))


# --- Редактирование ---

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])

    project = get_project(project_id)
    if not project or not can_manage(project, update.effective_user.id):
        await query.message.reply_text("Нет доступа к редактированию этого проекта.")
        return ConversationHandler.END

    context.user_data["editing_project_id"] = project_id
    await query.message.reply_text("Что редактируем?", reply_markup=field_choice_keyboard(project_id))
    return CHOOSE_FIELD


async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")

    if parts[0] == "editdone":
        project_id = int(parts[1])
        project = get_project(project_id)
        await query.message.reply_text("Готово. Итоговая карточка:")
        await query.message.reply_text(format_card(project), reply_markup=manage_actions_keyboard(project_id))
        context.user_data.pop("editing_project_id", None)
        context.user_data.pop("editing_field", None)
        return ConversationHandler.END

    _, project_id_str, field = parts
    project_id = int(project_id_str)
    context.user_data["editing_field"] = field

    if field == "category_id":
        categories = list_categories()
        await query.message.reply_text("Новая категория:", reply_markup=categories_keyboard(categories))
        return CHOOSE_FIELD

    label = FIELD_LABELS[field]
    await query.message.reply_text(f"Новое значение для «{label}»:")
    return EDIT_VALUE


async def got_new_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split(":")[1])
    project_id = context.user_data["editing_project_id"]

    update_project(project_id, {"category_id": category_id})
    await query.message.reply_text("Категория обновлена.", reply_markup=field_choice_keyboard(project_id))
    return CHOOSE_FIELD


async def got_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_id = context.user_data["editing_project_id"]
    field = context.user_data["editing_field"]
    text = update.message.text.strip()

    if field in DATE_FIELDS:
        if field == "end_date" and text == "-":
            value = None
        else:
            try:
                value = datetime.strptime(text, "%d.%m.%Y").date()
            except ValueError:
                await update.message.reply_text("Не похоже на дату ДД.ММ.ГГГГ, попробуй ещё раз:")
                return EDIT_VALUE
    else:
        value = text

    update_project(project_id, {field: value})
    await update.message.reply_text("Обновлено.", reply_markup=field_choice_keyboard(project_id))
    return CHOOSE_FIELD


async def manage_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("editing_project_id", None)
    context.user_data.pop("editing_field", None)
    await update.message.reply_text("Редактирование отменено.")
    return ConversationHandler.END


manage_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_edit, pattern="^edit:")],
    states={
        CHOOSE_FIELD: [
            CallbackQueryHandler(choose_field, pattern="^editfield:|^editdone:"),
            CallbackQueryHandler(got_new_category, pattern="^cat:"),
        ],
        EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_new_value)],
    },
    fallbacks=[CommandHandler("cancel", manage_cancel)],
)


# --- Удаление ---

async def start_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])

    project = get_project(project_id)
    if not project or not can_manage(project, update.effective_user.id):
        await query.message.reply_text("Нет доступа к удалению этого проекта.")
        return

    await query.message.reply_text(
        f"Удалить проект «{project['title']}»?",
        reply_markup=delete_confirm_keyboard(project_id),
    )


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])

    project = get_project(project_id)
    if not project or not can_manage(project, update.effective_user.id):
        await query.edit_message_text("Нет доступа.")
        return

    delete_project(project_id)
    await query.edit_message_text("Удалено.")


async def cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Удаление отменено.")


# --- Статистика (только админ) ---

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Команда доступна только администратору.")
        return

    total = count_total_projects()
    by_category = count_projects_by_category()

    lines = [f"Всего проектов: {total}", ""]
    for row in by_category:
        lines.append(f"{row['emoji']} {row['category_name']}: {row['count']}")

    await update.message.reply_text("\n".join(lines))
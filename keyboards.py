from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def categories_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:
    """Список категорий кнопками — по одной в ряд, для выбора при добавлении/поиске."""
    buttons = [
        [InlineKeyboardButton(f"{c['emoji']} {c['name']}", callback_data=f"cat:{c['id']}")]
        for c in categories
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Предпросмотр перед сохранением нового проекта (по ТЗ, пункт 7)."""
    buttons = [[
        InlineKeyboardButton("✅ Сохранить", callback_data="confirm:save"),
        InlineKeyboardButton("✏️ Изменить", callback_data="confirm:edit"),
        InlineKeyboardButton("❌ Отмена", callback_data="confirm:cancel"),
    ]]
    return InlineKeyboardMarkup(buttons)


def project_actions_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Под каждой записью в /myprojects."""
    buttons = [[
        InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit:{project_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{project_id}"),
    ]]
    return InlineKeyboardMarkup(buttons)


def delete_confirm_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Подтверждение перед реальным удалением (по ТЗ, пункт про 'Мои проекты')."""
    buttons = [[
        InlineKeyboardButton("Да, удалить", callback_data=f"delete_confirm:{project_id}"),
        InlineKeyboardButton("Отмена", callback_data=f"delete_cancel:{project_id}"),
    ]]
    return InlineKeyboardMarkup(buttons)


def open_project_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Кнопка 'Открыть' под карточкой в результатах поиска/списка."""
    buttons = [[InlineKeyboardButton("Открыть", callback_data=f"open:{project_id}")]]
    return InlineKeyboardMarkup(buttons) 

def skip_keyboard(field: str) -> InlineKeyboardMarkup:
    """Кнопка 'Пропустить' для необязательных полей (ссылка, контакт)."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data=f"skip:{field}")]]) 

def find_skip_keyboard(field: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data=f"find_skip:{field}")]])

FIELD_LABELS = {
    "title": "Название",
    "category_id": "Категория",
    "start_date": "Дата начала",
    "end_date": "Дата окончания",
    "venue": "Место проведения",
    "organizer": "Организатор",
    "description": "Описание",
    "link": "Ссылка",
    "contact_info": "Контактная информация",
}


def manage_actions_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Открыть/редактировать/удалить — показываем владельцу проекта или админу."""
    buttons = [[
        InlineKeyboardButton("Открыть", callback_data=f"open:{project_id}"),
        InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit:{project_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{project_id}"),
    ]]
    return InlineKeyboardMarkup(buttons)


def field_choice_keyboard(project_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"editfield:{project_id}:{field}")]
        for field, label in FIELD_LABELS.items()
    ]
    buttons.append([InlineKeyboardButton("✅ Готово", callback_data=f"editdone:{project_id}")])
    return InlineKeyboardMarkup(buttons)
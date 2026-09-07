def format_card(p: dict, full: bool = False) -> str:
    """full=False — карточка в списке/результатах поиска. full=True — при нажатии 'Открыть', добавляет контакт."""
    end_date_str = p["end_date"].strftime("%d.%m.%Y") if p.get("end_date") else ""
    start_date_str = p["start_date"].strftime("%d.%m.%Y") if isinstance(p["start_date"], type(p["start_date"])) else str(p["start_date"])
    date_range = f"{start_date_str}–{end_date_str}" if end_date_str else start_date_str

    lines = [
        f"{p.get('category_emoji', '')} {p['title']}",
        "",
        f"📅 {date_range}",
        f"📍 {p.get('venue') or 'не указано'}",
        f"👤 Организатор: {p.get('organizer') or 'не указан'}",
        "",
        "Описание:",
        p.get("description") or "—",
    ]
    if p.get("link"):
        lines.append(f"\n🔗 {p['link']}")
    if full:
        lines.append(f"\n☎️ Контакт: {p.get('contact_info') or 'не указан'}")
    return "\n".join(lines) 
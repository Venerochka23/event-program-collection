import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
    )


def list_categories() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categories ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def add_project(data: dict, user_id: int) -> int:
    """data содержит: title, category_id, start_date, end_date, venue, organizer, description, link, contact_info"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO projects
            (title, category_id, start_date, end_date, venue, organizer, description, link, contact_info, created_by_user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data["title"],
        data["category_id"],
        data["start_date"],
        data.get("end_date"),
        data.get("venue"),
        data.get("organizer"),
        data.get("description"),
        data.get("link"),
        data.get("contact_info"),
        user_id,
    ))
    new_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return new_id


def get_project(project_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, c.name AS category_name, c.emoji AS category_emoji
        FROM projects p
        JOIN categories c ON c.id = p.category_id
        WHERE p.id = %s
    """, (project_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def list_recent_projects(days: int = 30) -> list[dict]:
    """Для /list — проекты, добавленные за последние N дней."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, c.name AS category_name, c.emoji AS category_emoji
        FROM projects p
        JOIN categories c ON c.id = p.category_id
        WHERE p.created_at >= (NOW() - INTERVAL %s DAY)
        ORDER BY p.start_date ASC
    """, (days,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def search_projects(name: str = None, date_from=None, date_to=None, city: str = None) -> list[dict]:
    """
    Для /find. Все параметры необязательны и комбинируются через AND.
    date_from/date_to — либо оба заданы одинаковыми (поиск на одну дату),
    либо разными (поиск по периоду). Логика пересечения периодов:
    project.start_date <= date_to AND (project.end_date IS NULL OR project.end_date >= date_from)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT p.*, c.name AS category_name, c.emoji AS category_emoji
        FROM projects p
        JOIN categories c ON c.id = p.category_id
    """
    conditions = []
    params = []

    if name:
        conditions.append("p.title LIKE %s")
        params.append(f"%{name}%")
    if city:
        conditions.append("p.venue LIKE %s")
        params.append(f"%{city}%")
    if date_from and date_to:
        conditions.append("p.start_date <= %s AND (p.end_date IS NULL OR p.end_date >= %s)")
        params.append(date_to)
        params.append(date_from)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY p.start_date ASC"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def list_user_projects(user_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, c.name AS category_name, c.emoji AS category_emoji
        FROM projects p
        JOIN categories c ON c.id = p.category_id
        WHERE p.created_by_user_id = %s
        ORDER BY p.start_date DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_project(project_id: int, fields: dict):
    """fields — словарь вида {"title": "новое название", "venue": "новое место"} и т.д."""
    if not fields:
        return
    conn = get_connection()
    cursor = conn.cursor()
    set_clause = ", ".join(f"{key} = %s" for key in fields)
    params = list(fields.values()) + [project_id]
    cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = %s", params)
    conn.commit()
    cursor.close()
    conn.close()


def delete_project(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    conn = get_connection()
    print("Соединение с базой установлено успешно.")
    conn.close()

def count_total_projects() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total


def count_projects_by_category() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.name AS category_name, c.emoji, COUNT(p.id) AS count
        FROM categories c
        LEFT JOIN projects p ON p.category_id = c.id
        GROUP BY c.id
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
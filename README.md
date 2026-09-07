# event-program-collection
Telegram-бот для централизованного каталога творческих и культурных мероприятий: кинопоказы, выставки, лекции, театр, концерты и другие проекты. Пользователи добавляют мероприятия сами, ищут по названию/дате/городу, администратор модерирует любые записи. Предложения: @darkendless 

Стек: 
- Python 3.12
- `python-telegram-bot` (`ConversationHandler` для многошаговых диалогов)
- MySQL (`mysql-connector-python`)
- Развёрнут на Ubuntu VPS, управляется через systemd

Архитектура: 
| Файл | Назначение |
|---|---|
| `database.py` | CRUD-операции: проекты, категории, поиск, статистика |
| `keyboards.py` | Инлайн-клавиатуры: категории, подтверждение, управление записью |
| `formatting.py` | Форматирование карточки проекта для вывода в Telegram |
| `access.py` | Проверка прав администратора |
| `handlers_add.py` | Диалог добавления проекта (`ConversationHandler`, 9 шагов) |
| `handlers_search.py` | Просмотр списка и поиск по фильтрам |
| `handlers_manage.py` | «Мои проекты»: редактирование по полям, удаление, статистика |
| `bot.py` | Точка входа: регистрация всех обработчиков |

.env_example 
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MYSQL_HOST=localhost
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=your_database_name
ADMIN_USER_IDS=your_telegram_user_id

Технические решения: 
- **Многошаговые диалоги** реализованы через `ConversationHandler` с явными состояниями — позволяет боту «помнить», на каком вопросе находится пользователь, и корректно обрабатывать отмену (`/cancel`) на любом шаге.
- **Редактирование по отдельным полям**, а не пересозданием записи целиком — пользователь выбирает конкретное поле для правки, не переотвечая на все 9 вопросов заново.
- **Проверка прав** (`created_by_user_id == user_id or is_admin(user_id)`) — единая функция, переиспользуется во всех операциях изменения данных.

Схема MySQL:
-- Категории проектов (расширяемые, не зашиты в код)
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    emoji VARCHAR(10)
);

-- Сами проекты/мероприятия
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    category_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    venue VARCHAR(300),
    organizer VARCHAR(300),
    description TEXT,
    link VARCHAR(500),
    contact_info VARCHAR(300),
    created_by_user_id BIGINT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Начальный набор категорий
INSERT INTO categories (name, emoji) VALUES
('Кино / кинопоказы', '🎬'),
('Выставки', '🖼'),
('Лекции', '🎤'),
('Театр', '🎭'),
('Музыка / концерты', '🎵'),
('Творческие проекты', '🧑‍🎨'),
('Образовательные мероприятия', '📚'),
('Другое', '❓');

Установка: 
```bash
git clone <repo_url>
cd creative_projects_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # заполнить реальными значениями
python3 database.py   # проверка соединения с БД
python3 bot.py
```
<img width="643" height="773" alt="Снимок экрана — 2026-09-07 в 11 17 11" src="https://github.com/user-attachments/assets/c2f51a07-e92b-4e14-9346-135148a39a34" />
<img width="643" height="773" alt="Снимок экрана — 2026-09-07 в 11 16 55" src="https://github.com/user-attachments/assets/21b0dc7d-b7d0-4c68-b1df-2c0e99aadff3" />




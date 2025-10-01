import aiosqlite
from typing import Optional

# Глобальный объект соединения — будет создан при запуске
_db_connection = None

async def init_db():
    """Инициализирует соединение с базой данных. Вызывать ОДИН РАЗ при старте бота."""
    global _db_connection
    _db_connection = await aiosqlite.connect("Vilka_base1.db")
    _db_connection.row_factory = aiosqlite.Row  # Позволяет обращаться к столбцам по имени
    await create_table()

async def create_table():
    """Создаёт таблицу, если её нет"""
    # Удаляет таблицу (была необходиомсть)
    # await _db_connection.execute('DROP TABLE IF EXISTS quiz_state')
    await _db_connection.execute('''
        CREATE TABLE IF NOT EXISTS quiz_state (
            user_id INTEGER PRIMARY KEY,
            question_index INTEGER DEFAULT 0,
            current_correct INTEGER DEFAULT 0,
            achieved_achievements TEXT,
            score INTEGER DEFAULT 0,
            lang TEXT DEFAULT 'ru',
            completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await _db_connection.commit()


async def get_quiz_index(user_id: int) -> int:
    """Получает текущий индекс вопроса для пользователя"""
    async with _db_connection.execute(
        "SELECT question_index FROM quiz_state WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row["question_index"] if row else 0

async def update_quiz_index(user_id: int, index: int):
    """Обновляет только индекс вопроса в БД"""
    # Проверяем, существует ли запись
    async with _db_connection.execute(
        "SELECT 1 FROM quiz_state WHERE user_id = ?", (user_id,)
    ) as cursor:
        exists = await cursor.fetchone()
    
    if exists:
        # Обновляем только индекс
        await _db_connection.execute(
            "UPDATE quiz_state SET question_index = ? WHERE user_id = ?",
            (index, user_id)
        )
    else:
        # Создаем новую запись
        await _db_connection.execute(
            "INSERT INTO quiz_state (user_id, question_index) VALUES (?, ?)",
            (user_id, index)
        )
    await _db_connection.commit()

async def reset_current_correct(user_id: int):
    """Сбрасывает счётчик правильных ответов пользователя в БД"""
    await _db_connection.execute(
        "UPDATE quiz_state SET current_correct = 0 WHERE user_id = ?",
        (user_id,)
    )
    await _db_connection.commit()

async def up_current_correct(user_id: int, current: int):
    """Увеличивает количество правильных ответов пользователя в БД"""
    await _db_connection.execute(
        "UPDATE quiz_state SET current_correct = ? WHERE user_id = ?",
        (current, user_id)
    )
    await _db_connection.commit()

async def get_current_correct(user_id: int) -> int:
    """Получает количество правильных ответов для пользователя"""
    async with _db_connection.execute(
        "SELECT current_correct FROM quiz_state WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row["current_correct"] if row else 0

async def get_achieved_achievements(user_id: int) -> str:
    """Получает достижения пользователя"""
    async with _db_connection.execute(
        "SELECT achieved_achievements FROM quiz_state WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row["achieved_achievements"] if row else ""

async def update_achieved_achievements(user_id: int, achieve: str):
    """Записывает достижения пользователя"""
    # Проверяем, существует ли запись
    async with _db_connection.execute(
        "SELECT 1 FROM quiz_state WHERE user_id = ?", (user_id,)
    ) as cursor:
        exists = await cursor.fetchone()
    
    if exists:
        # Обновляем только достижения
        await _db_connection.execute(
            "UPDATE quiz_state SET achieved_achievements = ? WHERE user_id = ?",
            (achieve, user_id)
        )
    else:
        # Создаем новую запись
        await _db_connection.execute(
            "INSERT INTO quiz_state (user_id, achieved_achievements) VALUES (?, ?)",
            (user_id, achieve)
        )
    await _db_connection.commit()

# Добавьте эту функцию для отладки
async def debug_user_state(user_id: int):
    """Выводит отладочную информацию о пользователе"""
    async with _db_connection.execute(
        "SELECT * FROM quiz_state WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            print(f"🔍 DEBUG: user_id={row['user_id']}, index={row['question_index']}, correct={row['current_correct']}, achievements='{row['achieved_achievements']}'")
        else:
            print(f"🔍 DEBUG: user_id={user_id} - нет записи в БД")

  
async def save_quiz_result(user_id: int, score: int, lang: str):
    """Сохраняет результат прохождения квиза"""
    await _db_connection.execute(
        """INSERT OR REPLACE INTO quiz_state 
           (user_id, score, lang, completion_date) 
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
        (user_id, score, lang)
    )
    await _db_connection.commit()

async def get_last_result(user_id: int) -> dict:
    """Получает последний результат пользователя"""
    async with _db_connection.execute(
        """SELECT score, lang, completion_date 
           FROM quiz_state 
           WHERE user_id = ? AND score IS NOT NULL
           ORDER BY completion_date DESC 
           LIMIT 1""",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return {
                "score": row["score"],               
                "lang": row["lang"],
                "date": row["completion_date"]
            }
        return None
    
async def close_db():
    """Закрывает соединение при завершении работы бота"""
    if _db_connection:
        await _db_connection.close()
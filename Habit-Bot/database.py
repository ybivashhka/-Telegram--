import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def init_db():
    """Инициализация базы данных для хранения привычек."""
    try:
        conn = sqlite3.connect('habits.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS habits
                     (user_id INTEGER, habit TEXT, date TEXT, completed INTEGER)''')
        conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
    finally:
        conn.close()

def add_habit(user_id: int, habit: str):
    """Добавление новой привычки."""
    try:
        conn = sqlite3.connect('habits.db')
        c = conn.cursor()
        c.execute('INSERT INTO habits (user_id, habit, date, completed) VALUES (?, ?, ?, ?)',
                  (user_id, habit, datetime.now().strftime('%Y-%m-%d'), 0))
        conn.commit()
        logger.info(f"Habit '{habit}' added for user {user_id}.")
        return True
    except sqlite3.Error as e:
        logger.error(f"Failed to add habit: {e}")
        return False
    finally:
        conn.close()

def track_habit(user_id: int, habit: str):
    """Отметка выполнения привычки."""
    try:
        conn = sqlite3.connect('habits.db')
        c = conn.cursor()
        c.execute('UPDATE habits SET completed = 1 WHERE user_id = ? AND habit = ? AND date = ?',
                  (user_id, habit, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        logger.info(f"Habit '{habit}' tracked for user {user_id}.")
        return True
    except sqlite3.Error as e:
        logger.error(f"Failed to track habit: {e}")
        return False
    finally:
        conn.close()

def get_user_habits(user_id: int):
    """Получение списка привычек пользователя."""
    try:
        conn = sqlite3.connect('habits.db')
        c = conn.cursor()
        c.execute('SELECT DISTINCT habit FROM habits WHERE user_id = ?', (user_id,))
        habits = [row[0] for row in c.fetchall()]
        logger.info(f"Retrieved {len(habits)} habits for user {user_id}.")
        return habits
    except sqlite3.Error as e:
        logger.error(f"Failed to get habits: {e}")
        return []
    finally:
        conn.close()

def get_habit_progress(user_id: int, habit: str, days: int = 7):
    """Получение прогресса по привычке за указанный период."""
    try:
        conn = sqlite3.connect('habits.db')
        c = conn.cursor()
        c.execute('SELECT date, completed FROM habits WHERE user_id = ? AND habit = ? AND date >= ?',
                  (user_id, habit, (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')))
        data = c.fetchall()
        logger.info(f"Retrieved progress for habit '{habit}' for user {user_id}.")
        return data
    except sqlite3.Error as e:
        logger.error(f"Failed to get progress: {e}")
        return []
    finally:
        conn.close()

def get_all_habits_stats(user_id: int, days: int = 7):
    """Получение статистики по всем привычкам за указанный период."""
    try:
        conn = sqlite3.connect('habits.db')
        c = conn.cursor()
        c.execute('SELECT habit, completed FROM habits WHERE user_id = ? AND date >= ?',
                  (user_id, (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')))
        data = c.fetchall()
        logger.info(f"Retrieved stats for user {user_id}.")
        return data
    except sqlite3.Error as e:
        logger.error(f"Failed to get stats: {e}")
        return []
    finally:
        conn.close()
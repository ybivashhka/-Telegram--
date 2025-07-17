from aiogram import Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from database import add_habit, track_habit, get_user_habits, get_habit_progress, get_all_habits_stats
from visualizer import generate_stats_plot
from states import AddHabit
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

# Количество привычек на одной странице
HABITS_PER_PAGE = 5

def create_paginated_keyboard(habits, page, action):
    """Создание пагинированной клавиатуры для привычек."""
    start_idx = page * HABITS_PER_PAGE
    end_idx = start_idx + HABITS_PER_PAGE
    paginated_habits = habits[start_idx:end_idx]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=habit, callback_data=f'{action}_{habit}')]
        for habit in paginated_habits
    ])
    
    nav_buttons = []
    if start_idx > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f'page_{action}_{page-1}'))
    if end_idx < len(habits):
        nav_buttons.append(InlineKeyboardButton(text="Далее ➡", callback_data=f'page_{action}_{page+1}'))
    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)
    
    return keyboard

def setup_handlers(dp: Dispatcher):
    """Настройка всех обработчиков команд и callback-запросов."""
    
    @dp.message(CommandStart())
    async def start_command(message: types.Message):
        """Обработчик команды /start."""
        await message.reply('Привет! Я бот для трекинга привычек. Используй команды:\n'
                           '/add - Добавить привычку\n'
                           '/track - Отметить выполнение\n'
                           '/progress - Показать прогресс\n'
                           '/stats - Показать статистику\n'
                           '/delete - Удалить привычку\n'
                           '/cancel - Отменить действие')
        logger.info(f"User {message.from_user.id} started bot.")

    @dp.message(Command('add'))
    async def add_habit_command(message: types.Message, state: FSMContext):
        """Обработчик команды /add для начала ввода привычки."""
        await message.reply('Введи название привычки (или /cancel для отмены):')
        await state.set_state(AddHabit.waiting_for_habit)
        logger.info(f"User {message.from_user.id} started adding habit.")

    @dp.message(AddHabit.waiting_for_habit)
    async def process_habit_input(message: types.Message, state: FSMContext):
        """Обработчик ввода названия привычки."""
        if message.text.startswith('/cancel'):
            await state.clear()
            await message.reply('Добавление привычки отменено.')
            logger.info(f"User {message.from_user.id} cancelled adding habit.")
            return
        
        habit = message.text.strip()
        if not habit:
            await message.reply('Название привычки не может быть пустым. Попробуй снова или /cancel.')
            return
        
        if add_habit(message.from_user.id, habit):
            await message.reply(f'Привычка "{habit}" добавлена!')
            logger.info(f"Habit '{habit}' added for user {message.from_user.id}.")
        else:
            await message.reply('Ошибка при добавлении привычки. Попробуй снова.')
        
        await state.clear()

    @dp.message(Command('cancel'))
    async def cancel_command(message: types.Message, state: FSMContext):
        """Обработчик команды /cancel."""
        await state.clear()
        await message.reply('Действие отменено.')
        logger.info(f"User {message.from_user.id} cancelled action.")

    @dp.message(Command('track'))
    async def track_habit_command(message: types.Message):
        """Обработчик команды /track для выбора привычки."""
        habits = get_user_habits(message.from_user.id)
        if not habits:
            await message.reply('У тебя нет привычек. Добавь их с помощью /add!')
            return
        
        keyboard = create_paginated_keyboard(habits, page=0, action='track')
        await message.reply('Выбери привычку для отметки:', reply_markup=keyboard)
        logger.info(f"User {message.from_user.id} requested track habits.")

    @dp.callback_query(lambda c: c.data.startswith('track_'))
    async def process_track_callback(callback: types.CallbackQuery):
        """Обработчик callback-запроса для отметки выполнения."""
        habit = callback.data.replace('track_', '')
        if track_habit(callback.from_user.id, habit):
            await callback.message.reply(f'Привычка "{habit}" отмечена как выполненная!')
            logger.info(f"Habit '{habit}' tracked for user {callback.from_user.id}.")
        else:
            await callback.message.reply('Ошибка при отметке привычки. Попробуй снова.')
        await callback.answer()

    @dp.message(Command('progress'))
    async def show_progress_command(message: types.Message):
        """Обработчик команды /progress для выбора привычки."""
        habits = get_user_habits(message.from_user.id)
        if not habits:
            await message.reply('У тебя нет привычек. Добавь их с помощью /add!')
            return
        
        keyboard = create_paginated_keyboard(habits, page=0, action='progress')
        await message.reply('Выбери привычку для просмотра прогресса:', reply_markup=keyboard)
        logger.info(f"User {message.from_user.id} requested progress.")

    @dp.callback_query(lambda c: c.data.startswith('progress_'))
    async def process_progress_callback(callback: types.CallbackQuery):
        """Обработчик callback-запроса для показа прогресса."""
        habit = callback.data.replace('progress_', '')
        data = get_habit_progress(callback.from_user.id, habit)
        
        if not data:
            await callback.message.reply(f'Нет данных для "{habit}" за последнюю неделю.')
            return
        
        completed = sum(row[1] for row in data)
        progress = completed / len(data) * 100
        await callback.message.reply(f'Прогресс для "{habit}": {progress:.1f}% выполнено за неделю.')
        logger.info(f"Progress for habit '{habit}' shown for user {callback.from_user.id}.")
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith('page_'))
    async def process_page_callback(callback: types.CallbackQuery):
        """Обработчик пагинации для track и progress."""
        action, page = callback.data.split('_')[1], int(callback.data.split('_')[2])
        habits = get_user_habits(callback.from_user.id)
        
        keyboard = create_paginated_keyboard(habits, page, action)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        logger.info(f"User {callback.from_user.id} navigated to {action} page {page}.")
        await callback.answer()

    @dp.message(Command('stats'))
    async def show_stats_command(message: types.Message):
        """Обработчик команды /stats для выбора периода статистики."""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Неделя", callback_data='stats_7')],
            [InlineKeyboardButton(text="Месяц", callback_data='stats_30')]
        ])
        await message.reply('Выбери период для статистики:', reply_markup=keyboard)
        logger.info(f"User {message.from_user.id} requested stats.")

    @dp.callback_query(lambda c: c.data.startswith('stats_'))
    async def process_stats_callback(callback: types.CallbackQuery):
        """Обработчик callback-запроса для показа статистики."""
        days = int(callback.data.replace('stats_', ''))
        data = get_all_habits_stats(callback.from_user.id, days=days)
        
        if not data:
            await callback.message.reply(f'Нет данных за последние {days} дней.')
            logger.info(f"No stats data for user {callback.from_user.id} for {days} days.")
            await callback.answer()
            return
        
        plot_file = generate_stats_plot(data, callback.from_user.id)
        if not plot_file or not os.path.exists(plot_file):
            logger.error(f"Failed to generate or find plot file for user {callback.from_user.id}: {plot_file}")
            await callback.message.reply('Ошибка при создании графика. Убедись, что данные доступны, и попробуй снова.')
            await callback.answer()
            return
        
        try:
            photo = FSInputFile(path=plot_file, filename=f'stats_{callback.from_user.id}.png')
            await callback.message.reply_photo(photo=photo, caption=f'Статистика за {days} дней')
            logger.info(f"Sent stats plot to user {callback.from_user.id}: {plot_file}")
        except Exception as e:
            logger.error(f"Failed to send plot for user {callback.from_user.id}: {e}")
            await callback.message.reply(f'Ошибка при отправке графика: {str(e)}. Попробуй снова.')
        finally:
            try:
                if os.path.exists(plot_file):
                    os.remove(plot_file)
                    logger.info(f"Deleted plot file: {plot_file}")
                else:
                    logger.warning(f"Plot file {plot_file} does not exist for deletion")
            except OSError as e:
                logger.error(f"Failed to delete plot file {plot_file}: {e}")
        await callback.answer()

    @dp.message(Command('delete'))
    async def delete_habit_command(message: types.Message):
        """Обработчик команды /delete для выбора привычки."""
        habits = get_user_habits(message.from_user.id)
        if not habits:
            await message.reply('У тебя нет привычек для удаления.')
            return
        
        keyboard = create_paginated_keyboard(habits, page=0, action='delete')
        await message.reply('Выбери привычку для удаления:', reply_markup=keyboard)
        logger.info(f"User {message.from_user.id} requested delete habits.")

    @dp.callback_query(lambda c: c.data.startswith('delete_'))
    async def process_delete_callback(callback: types.CallbackQuery):
        """Обработчик callback-запроса для подтверждения удаления."""
        habit = callback.data.replace('delete_', '')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data=f'confirm_delete_{habit}')],
            [InlineKeyboardButton(text="Отмена", callback_data='cancel_delete')]
        ])
        await callback.message.reply(f'Точно удалить привычку "{habit}"?', reply_markup=keyboard)
        logger.info(f"User {callback.from_user.id} requested to confirm deletion of '{habit}'.")
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith('confirm_delete_'))
    async def confirm_delete_callback(callback: types.CallbackQuery):
        """Обработчик подтверждения удаления привычки."""
        habit = callback.data.replace('confirm_delete_', '')
        try:
            conn = sqlite3.connect('habits.db')
            c = conn.cursor()
            # Проверяем, существует ли привычка
            c.execute('SELECT COUNT(*) FROM habits WHERE user_id = ? AND habit = ?',
                      (callback.from_user.id, habit))
            if c.fetchone()[0] == 0:
                await callback.message.reply(f'Привычка "{habit}" не найдена.')
                logger.warning(f"Habit '{habit}' not found for user {callback.from_user.id}.")
                conn.close()
                await callback.answer()
                return
            
            # Удаляем привычку
            c.execute('DELETE FROM habits WHERE user_id = ? AND habit = ?',
                      (callback.from_user.id, habit))
            conn.commit()
            await callback.message.reply(f'Привычка "{habit}" удалена.')
            logger.info(f"Habit '{habit}' deleted for user {callback.from_user.id}.")
        except sqlite3.Error as e:
            logger.error(f"Failed to delete habit '{habit}' for user {callback.from_user.id}: {e}")
            await callback.message.reply(f'Ошибка при удалении привычки "{habit}": {str(e)}. Попробуй снова.')
        finally:
            conn.close()
        await callback.answer()

    @dp.callback_query(lambda c: c.data == 'cancel_delete')
    async def cancel_delete_callback(callback: types.CallbackQuery):
        """Обработчик отмены удаления."""
        await callback.message.reply('Удаление отменено.')
        logger.info(f"User {callback.from_user.id} cancelled deletion.")
        await callback.answer()
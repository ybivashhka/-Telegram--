import matplotlib.pyplot as plt
import os
import logging

logger = logging.getLogger(__name__)

def generate_stats_plot(data, user_id):
    """Генерация графика статистики привычек."""
    try:
        if not data:
            logger.error(f"No data provided for user {user_id}")
            return None
        
        habits = {}
        for habit, completed in data:
            if habit not in habits:
                habits[habit] = {'completed': 0, 'total': 0}
            habits[habit]['total'] += 1
            habits[habit]['completed'] += completed
        
        if not habits:
            logger.error(f"No valid habits data for user {user_id}")
            return None
        
        # Создание графика
        plt.figure(figsize=(8, 6))
        habit_names = list(habits.keys())
        progress = [habits[h]['completed'] / habits[h]['total'] * 100 for h in habit_names]
        
        plt.bar(habit_names, progress, color='skyblue')
        plt.xlabel('Привычки')
        plt.ylabel('Процент выполнения (%)')
        plt.title('Прогресс привычек за выбранный период')
        plt.xticks(rotation=45)
        
        plot_file = f'stats_{user_id}.png'
        plt.savefig(plot_file)
        plt.close()
        
        if not os.path.exists(plot_file):
            logger.error(f"Plot file {plot_file} was not created for user {user_id}")
            return None
        
        logger.info(f"Generated stats plot for user {user_id}: {plot_file}")
        return plot_file
    except Exception as e:
        logger.error(f"Failed to generate stats plot for user {user_id}: {e}")
        return None
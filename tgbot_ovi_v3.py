# Бот парсит статистику Ови, получает количество игр и голов, проверяет кликом и шедулером
# pip install pyTelegramBotAPI requests schedule BeautifulSoup
import telebot
import requests
import json
import schedule
import time
from datetime import datetime
from threading import Thread
from bs4 import BeautifulSoup

# Токен вашего бота
TOKEN = '8199513220:AAGl09XIIqzpfF1zlJQIzAinT7tjic38e7c'
bot = telebot.TeleBot(TOKEN)

# Переменная для хранения рекорда
Global_var_goals = 0

# Рекорд Овечкина
GRETZKY_RECORD = 1000

# Имя файла для хранения данных
USER_DATA_FILE = 'users.json'

# Загружаем данные о пользователях
try:
    with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
        users_data = json.load(file)
except FileNotFoundError:
    print("Файл с данными о пользователях не найден! Создаем новый.")
    users_data = {}


# Функция для сохранения данных в JSON
def save_users_data():
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(users_data, file, ensure_ascii=False, indent=4)


# Функция для отправки сообщения всем пользователям
def send_message_to_all_users(message_text):
    for user_id, user_info in users_data.items():
        try:
            # Отправляем сообщение
            bot.send_message(user_info['chat_id'], message_text)
        except Exception as e:
            print(
                f"Не удалось отправить сообщение пользователю {user_info['username']} (ID: {user_id}): {e}")


# Обработчик личных сообщений (если пользователь начинает диалог с ботом)
def handle_private_message(message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "No username"
    first_name = message.from_user.first_name if message.from_user.first_name else "No first name"
    last_name = message.from_user.last_name if message.from_user.last_name else "No last name"

    # Добавляем пользователя в данные, если его еще нет
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'chat_id': message.chat.id
        }
        save_users_data()
        print(f"Новый пользователь добавлен: {username} (ID: {user_id})")


# Функция для проверки, забил ли Овечкин
def check_ovechkin_goals():
    global Global_var_goals
    goals_result, games_played_result = get_ovechkin_goals()
    if goals_result is None:
        print("Ошибка при получении данных о голах Овечкина")
        return

    current_date_check = datetime.now().strftime('%d.%m.%Y')

    if goals_result > Global_var_goals:
        # Текст сообщения, которое вы хотите отправить
        message_text = (f"🏒🥅 Овечкин забил!\nНа {current_date_check} его текущий счет: "
                        f"{goals_result} голов.")
        # Отправляем сообщение всем пользователям
        send_message_to_all_users(message_text)
        print(f"Овечкин забил! Его текущий счет: {goals_result} голов на {current_date_check}.")
        Global_var_goals = goals_result
    else:
        print(f"Новых голов нет. Текущий счет: {goals_result} (было: {Global_var_goals})")


# Функция для получения текущего счета Овечкина
def get_ovechkin_goals():
    # Парсим юрл
    url = "https://www.espn.com/nhl/player/stats/_/id/3101/alex-ovechkin"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Ищем блок с общей статистикой Career
            stats_block = soup.find_all('span', class_='fw-bold clr-gray-01')
            if stats_block and len(stats_block) >= 3:
                # Ищем количество шайб и игр
                goals = stats_block[2].text.strip()
                games_played = stats_block[1].text.strip()
                return int(goals), int(games_played)
        return None, None
    except Exception as e:
        print(f"Ошибка при парсинге данных: {e}")
        return None, None


# Команда для проверки счета Овечкина
@bot.message_handler(commands=['check_goals'])
def check_goals(message):
    global Global_var_goals
    goals_result, games_played_result = get_ovechkin_goals()
    current_date = datetime.now().strftime('%d.%m.%Y')
    if goals_result is not None:
        remaining_goals = GRETZKY_RECORD - goals_result
        google_link = (f"https://www.google.com/search?q="
                       f"На+{current_date}+"
                       f"сколько+шайб+осталось+забить+Александру+Овечкину+до+рекорда+1000 Ovi")
        response_text = (f"\nОсталось {remaining_goals} шайб\n\n"
                         f"На {current_date} текущий счет Александра Овечкина: {goals_result} шайб(ы) в"
                         f" {games_played_result} матчах.\n"
                         f"До рекорда \"1000 Ovi\" осталось забить:"
                         f" {remaining_goals}"
                         f" шайб.\n"
                         f"Подробнее: [Google]({google_link})"
                         )
        bot.send_message(message.chat.id, response_text, parse_mode="Markdown")
        Global_var_goals = goals_result
    else:
        bot.send_message(message.chat.id, "Не удалось получить данные о голах Овечкина.")


# Кнопка для проверки счета
@bot.message_handler(commands=['start'])
def start(message):
    handle_private_message(message)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button = telebot.types.KeyboardButton('🏒 Проверить счет Овечкина')
    markup.add(button)
    bot.send_message(message.chat.id, "Нажмите кнопку, чтобы проверить счет Овечкина:",
                     reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '🏒 Проверить счет Овечкина')
def handle_button(message):
    check_goals(message)


# Планирование задач
def schedule_tasks():
    schedule.every().day.at("07:00").do(check_ovechkin_goals)
    schedule.every().day.at("12:00").do(check_ovechkin_goals)
    schedule.every().day.at("19:00").do(check_ovechkin_goals)

    while True:
        schedule.run_pending()
        time.sleep(60)


# Запуск бота и планировщика
if __name__ == "__main__":
    # Получаем текущее количество голов при старте
    goals, _ = get_ovechkin_goals()
    if goals is not None:
        Global_var_goals = goals
        print(f"Текущий счет Овечкина: {goals} голов")

    Thread(target=schedule_tasks, daemon=True).start()
    print("Бот запущен...")

    # Запуск бота
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Ошибка в работе бота: {e}")
            time.sleep(5)
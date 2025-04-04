import telebot
from telebot import types
from datetime import datetime
from flask import Flask
import os

# Создаём Flask-приложение
app = Flask(__name__)

# Подключаем бота с твоим токеном
bot = telebot.TeleBot('7940514562:AAEejbBsPnmqFxpQj_T2iAUaSOOpFEuedfw')
MY_CHAT_ID = 1440226179  # Твой ID для админ-меню и получения заявок

# Список для хранения всех заявок
all_applications = []

# Словарь для хранения данных пользователей
applications = {}

# Список ролей для кнопок
ROLES = ["Переводчик", "Редактор", "Тайпер", "Клинер", "Другое"]

# Описания ролей
ROLE_DESCRIPTIONS = {
    "Переводчик": "📖 Переводит текст манги с одного языка на другой.",
    "Редактор": "✍️ Проверяет и исправляет перевод, улучшает стиль.",
    "Тайпер": "🖌️ Вставляет текст в изображения манги.",
    "Клинер": "🧹 Удаляет текст с изображений и чистит сканы.",
    "Другое": "🔧 Другие задачи (укажи в комментарии, что именно)."
}

# Функция для создания текста заявки
def create_application_text(app_data, include_timestamp=False):
    text = (f"📨 Заявка:\n"
            f"👤 Username: {app_data['username']}\n"
            f"✍️ Имя: {app_data['name']}\n"
            f"🎭 Роль: {app_data['role']}\n"
            f"💬 Комментарий: {app_data['comment']}")
    if include_timestamp and 'timestamp' in app_data:
        text += f"\n🕒 Дата и время: {app_data['timestamp']}"
    return text

# Функция для создания кнопок редактирования
def create_edit_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✍️ Имя", callback_data="edit_name"),
               types.InlineKeyboardButton("🎭 Роль", callback_data="edit_role"),
               types.InlineKeyboardButton("💬 Комментарий", callback_data="edit_comment"),
               types.InlineKeyboardButton("✅ Отправить", callback_data="submit_application"))
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not message.from_user.username:
        bot.reply_to(message, "❌ Привет! У тебя нет username в Telegram. "
                              "Добавь его в настройках (@username) и начни заново с /start.")
        return
    
    markup = types.InlineKeyboardMarkup()
    start_button = types.InlineKeyboardButton("✨ Начать подачу заявки", callback_data="start_application")
    markup.add(start_button)
    
    bot.reply_to(message, "👋 Привет! Я бот для заявок в команду по переводу манги.\n"
                          "Готов присоединиться к нам? Нажми кнопку ниже!",
                          reply_markup=markup)
    applications[message.chat.id] = {'step': 'start', 'username': f"@{message.from_user.username}"}

# Обработчик команды /admin (только для тебя)
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.chat.id != MY_CHAT_ID:
        bot.reply_to(message, "❌ У тебя нет доступа к админ-меню!")
        return
    
    if not all_applications:
        bot.reply_to(message, "📂 Пока нет заявок.")
        return
    
    for idx, app in enumerate(all_applications, 1):
        app_text = create_application_text(app, include_timestamp=True)
        bot.send_message(message.chat.id, f"Заявка #{idx}\n{app_text}")

# Обработчик нажатий на инлайн-кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if chat_id not in applications:
        bot.answer_callback_query(call.id, "❌ Пожалуйста, начни с команды /start!")
        return

    if call.data == "start_application":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="📝 Отлично! Напиши своё имя:")
        applications[chat_id]['step'] = 'name'

    elif call.data in ROLES:
        applications[chat_id]['role'] = call.data
        role_description = ROLE_DESCRIPTIONS.get(call.data, "Описание отсутствует.")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"✅ Роль выбрана: {call.data}\n"
                                    f"{role_description}\n\n"
                                    "Напиши пару слов о себе или почему хочешь в команду:")
        applications[chat_id]['step'] = 'comment'

    elif call.data == "edit_name":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="📝 Введи новое имя:")
        applications[chat_id]['step'] = 'edit_name'

    elif call.data == "edit_role":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for role in ROLES:
            markup.add(types.InlineKeyboardButton(role, callback_data=role))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="🎭 Выбери новую роль:", reply_markup=markup)
        applications[chat_id]['step'] = 'edit_role'

    elif call.data == "edit_comment":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="💬 Введи новый комментарий:")
        applications[chat_id]['step'] = 'edit_comment'

    elif call.data == "submit_application":
        applications[chat_id]['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        application = create_application_text(applications[chat_id], include_timestamp=True)
        all_applications.append(applications[chat_id].copy())
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"🎉 Заявка отправлена!\n{application}")
        bot.send_message(MY_CHAT_ID, application)
        print(application)
        del applications[chat_id]

# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    
    if chat_id not in applications:
        bot.reply_to(message, "❌ Пожалуйста, начни с команды /start!")
        return

    step = applications[chat_id]['step']

    if step == 'name':
        applications[chat_id]['name'] = message.text
        markup = types.InlineKeyboardMarkup(row_width=2)
        for role in ROLES:
            markup.add(types.InlineKeyboardButton(role, callback_data=role))
        bot.reply_to(message, f"✅ Имя сохранено: {message.text}\n"
                              "Теперь выбери роль в команде:", reply_markup=markup)
        applications[chat_id]['step'] = 'role'

    elif step == 'comment':
        applications[chat_id]['comment'] = message.text
        application_text = create_application_text(applications[chat_id])
        markup = create_edit_buttons()
        bot.reply_to(message, f"{application_text}\n\n"
                              "Проверь данные. Если нужно что-то изменить, выбери ниже:",
                              reply_markup=markup)
        applications[chat_id]['step'] = 'preview'

    elif step == 'edit_name':
        applications[chat_id]['name'] = message.text
        application_text = create_application_text(applications[chat_id])
        markup = create_edit_buttons()
        bot.reply_to(message, f"✅ Имя обновлено: {message.text}\n\n"
                              f"{application_text}\n\n"
                              "Проверь данные. Если нужно что-то изменить, выбери ниже:",
                              reply_markup=markup)
        applications[chat_id]['step'] = 'preview'

    elif step == 'edit_comment':
        applications[chat_id]['comment'] = message.text
        application_text = create_application_text(applications[chat_id])
        markup = create_edit_buttons()
        bot.reply_to(message, f"✅ Комментарий обновлён: {message.text}\n\n"
                              f"{application_text}\n\n"
                              "Проверь данные. Если нужно что-то изменить, выбери ниже:",
                              reply_markup=markup)
        applications[chat_id]['step'] = 'preview'

    else:
        bot.reply_to(message, "❌ Пожалуйста, следуй инструкциям! "
                              "Если что-то пошло не так, начни заново с /start.")

# Flask маршрут для проверки, что сервер работает
@app.route('/')
def home():
    return "Bot is running!"

# Запуск бота в polling-режиме
bot.remove_webhook()
bot.polling()

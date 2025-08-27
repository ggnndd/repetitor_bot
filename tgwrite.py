import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext


ADMIN_TELEGRAM_ID = '' #удалил специально, учтите если будете запускать и проверять код, здесь нужно вписать tg id пользователя(админа),

# Путь к файлу для хранения ссылок
FILE_PATH = 'files.json'


# Загрузка ссылок из JSON
def load_files():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r') as f:
            return json.load(f)
    else:
        return {
            'ОГЭ': '',
            'ЕГЭ': '',
            'История искусств': ''
        }


# Сохранение ссылок в JSON-файл
def save_files(files):
    with open(FILE_PATH, 'w') as f:
        json.dump(files, f)


files = load_files()


# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Родитель", callback_data='role_parent')],
        [InlineKeyboardButton("Ученик", callback_data='role_student')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Добро пожаловать! Пожалуйста, выберите свою роль:', reply_markup=reply_markup)


# Обработчик выбора роли (так скажем)
def role_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    context.user_data['role'] = 'Родитель' if query.data == 'role_parent' else 'Ученик'

    keyboard = [
        [InlineKeyboardButton("ОГЭ", callback_data='course_oge')],
        [InlineKeyboardButton("ЕГЭ", callback_data='course_ege')],
        [InlineKeyboardButton("История искусств", callback_data='course_history')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text=f"Вы выбрали роль {context.user_data['role']}. Пожалуйста, выберите подготовку:",
                            reply_markup=reply_markup)


# Обработчик выбора курса
def course_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'course_oge':
        context.user_data['course'] = 'ОГЭ'
    elif query.data == 'course_ege':
        context.user_data['course'] = 'ЕГЭ'
    elif query.data == 'course_history':
        context.user_data['course'] = 'История искусств'

    context.user_data['leave_request'] = True
    query.edit_message_text(text="Пожалуйста, отправьте свои ФИО.")


# Обработчик текстовых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    if 'leave_request' in context.user_data:
        context.user_data['fio'] = update.message.text
        context.user_data.pop('leave_request')
        update.message.reply_text('Пожалуйста, отправьте ваш ник в Telegram.')

        context.user_data['awaiting_nick'] = True
    elif 'awaiting_nick' in context.user_data:
        context.user_data['nick'] = update.message.text
        context.user_data.pop('awaiting_nick')

        fio = context.user_data['fio']
        nick = context.user_data['nick']
        role = context.user_data['role']
        course = context.user_data['course']
        username = update.message.from_user.username
        user_id = update.message.from_user.id

        # Отправка данных администратору
        context.bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=(
                f'Новая заявка на пробное занятие:\n'
                f'Роль: {role}\n'
                f'Подготовка: {course}\n'
                f'ФИО: {fio}\n'
                f'Ник: {nick}\n'
                f'Отправлено с аккаунта: @{username} (ID: {user_id})'
            )
        )

        # Отправка ссылки на файл пользователю
        if course in files and files[course]:
            update.message.reply_text(
                f'Вам подарок! Скачайте файл по ссылке: {files[course]}')
        else:
            update.message.reply_text('Извините, файл для выбранного курса недоступен.')

        update.message.reply_text(
            'Спасибо за заявку! Ваши данные были отправлены администратору. С вами свяжутся в ближайшее время.')


# Обработчик команды изменения ссылок
def admin_set_file(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == int(ADMIN_TELEGRAM_ID):
        if len(context.args) != 2:
            update.message.reply_text('Использование: /setfile <course> <url>')
            return

        course, url = context.args
        if course in files:
            files[course] = url
            save_files(files)
            update.message.reply_text(f'Ссылка на файл для курса {course} была обновлена.')
        else:
            update.message.reply_text('Некорректный курс. Допустимые курсы: ОГЭ, ЕГЭ, История искусств.')
    else:
        update.message.reply_text('У вас нет прав для выполнения этой команды.')


def main() -> None:
    updater = Updater("") # тут вам нужно указать токен бота в тг, удалил, потому что это личная информация человека и этот бот до сих пор используется

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(role_choice, pattern='^role_'))
    updater.dispatcher.add_handler(CallbackQueryHandler(course_choice, pattern='^course_'))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.dispatcher.add_handler(CommandHandler('setfile', admin_set_file, pass_args=True))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

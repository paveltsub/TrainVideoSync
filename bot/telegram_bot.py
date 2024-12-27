import logging
from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

bot_token = "ТОКЕН_ЗДЕСЬ"

# кнопка
requst_video_button = "/get_video"

# кнопки для выбора видео
video_choices = ["Видео 1.avi", "Видео 2.avi", "Видео 3.avi", "Видео 4.avi"]

async def start_command(update, context):
    
    # /start
    keyboard = [
        [KeyboardButton(requst_video_button)],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        "Нажмите на кнопку ниже или введите /get_video для запроса видео.",
        reply_markup=reply_markup
    )
    # cбрасываем состояние
    context.user_data['awaiting_video_choice'] = False

async def show_video_list(update_or_message, context):
    
    # список видео (второй шаг).
    keyboard = [
        [KeyboardButton(name) for name in video_choices[:2]],
        [KeyboardButton(name) for name in video_choices[2:]]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if hasattr(update_or_message, "reply_text"):
        await update_or_message.reply_text(
            "Выберите видео:",
            reply_markup=reply_markup
        )
    else:
        await update_or_message.message.reply_text(
            "Выберите видео:",
            reply_markup=reply_markup
        )
    
    context.user_data['awaiting_video_choice'] = True

async def get_video_command(update, context):

    # команда /get_video: переходим к выбору видео
    await show_video_list(update.message, context)

async def handle_text_messages(update, context):

    chat_id = update.effective_chat.id
    user_text = update.message.text.strip()

    if not context.user_data.get('awaiting_video_choice', False):
        if user_text.lower() in [requst_video_button.lower(), "/get_video"]:
            await show_video_list(update, context)
        else:
            await update.message.reply_text(
                "Неизвестная команда.\n"
                "Нажмите на кнопку или введите /get_video, чтобы выбрать видео."
            )
    else:
        # file_id да всех видео
        mapping = {
            "Видео 1.avi": "BQACAgIAAxkBAANQZ230-3Vxx8O9eFocbzLJXzTysVYAAv1lAAJsWXBLEUBNYo25fQM2BA",
            "Видео 2.avi": "BQACAgIAAxkBAANdZ238cDi-xEzZvuZ5duEK0j7NT7EAAv5lAAJsWXBL6ch3-fjpQd82BA",
            "Видео 3.avi": "BQACAgIAAxkBAANfZ238dfytcsoeguMTh7zI3GSoHp0AAv9lAAJsWXBLHaDHcFxWhag2BA",
            "Видео 4.avi": "BQACAgIAAxkBAANhZ238esRe70CYcRG7dyAsiRrJEl4AA2YAAmxZcEv6ncC20KNxuDYE",
        }
        
        if user_text in mapping:
            file_id = mapping[user_text]
            # отправляем пользователю видео по file_id
            await update.message.reply_text(f"Отправляю файл {user_text}...")
            
            # Длительные операции (большие файлы) можно увеличить таймаут
            await context.bot.send_video(
                chat_id=chat_id,
                video=file_id,
                read_timeout=300,
                write_timeout=300
            )
            
            context.user_data['awaiting_video_choice'] = False
            
            keyboard = [
                [KeyboardButton(requst_video_button)],
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "Можете снова запросить видео, нажав кнопку ниже или команду /get_video.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Неизвестная команда.\n"
                "Выберите одно из предложенных видео или /start для возврата в начало."
            )

def main():
    application = ApplicationBuilder().token(bot_token).build()

    # хендлеры команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("get_video", get_video_command))

    # хендлер сообщений
    application.add_handler(MessageHandler(filters.TEXT, handle_text_messages))

    application.run_polling()

if __name__ == "__main__":
    main()
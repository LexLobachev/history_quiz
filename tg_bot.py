import functools
import logging
import random
import redis

from decouple import config
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from quiz_parser import load_quiz_questions


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Здравствуйте!', reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


def new_question(update: Update, context: CallbackContext, questions, redis_connection) -> None:
    if update.message.text == 'Новый вопрос':
        random_key = random.choice(list(questions.keys()))
        question, answer = questions[random_key]
        redis_connection.set(update.message.from_user.id, answer)
        update.message.reply_text(question)
    else:
        update.message.reply_text(update.message.text)


def main() -> None:
    updater = Updater(config("TG_BOT_TOKEN"))
    redis_host = config("REDIS_HOST")
    redis_port = config("REDIS_PORT")
    redis_password = config("REDIS_PASSWORD")

    redis_connection = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)

    questions = load_quiz_questions()

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    give_new_question = functools.partial(new_question, questions=questions, redis_connection=redis_connection)

    dispatcher.add_handler(MessageHandler(Filters.text, give_new_question))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

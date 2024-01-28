import functools
import logging
import random

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


def new_question(update: Update, context: CallbackContext, questions) -> None:
    if update.message.text == 'Новый вопрос':
        random_key = random.choice(list(questions.keys()))
        question = questions[random_key][0]
        update.message.reply_text(question)
    else:
        update.message.reply_text(update.message.text)


def main() -> None:
    updater = Updater(config("TG_BOT_TOKEN"))

    questions = load_quiz_questions()

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    give_new_question = functools.partial(new_question, questions=questions)

    dispatcher.add_handler(MessageHandler(Filters.text, give_new_question))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

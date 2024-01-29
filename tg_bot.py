import functools
import logging
import random
import redis

from decouple import config
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from quiz_parser import load_quiz_questions


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

NEW_QUESTION, ANSWER = range(2)


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Здравствуйте!', reply_markup=reply_markup)

    return NEW_QUESTION


def handle_new_question_request(update: Update, context: CallbackContext, questions, redis_connection):
    random_key = random.choice(list(questions.keys()))
    question, answer = questions[random_key]
    redis_connection.set(update.message.from_user.id, answer)
    update.message.reply_text(question)

    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext, redis_connection):
    redis_answer = redis_connection.get(update.message.from_user.id)
    right_answer = redis_answer.decode("utf-8").lower()
    user_answer = update.message.text.lower()

    if user_answer == right_answer:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»')
        return NEW_QUESTION
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return ANSWER


def handle_give_up(update: Update, context: CallbackContext, redis_connection):
    redis_answer = redis_connection.get(update.message.from_user.id)
    right_answer = redis_answer.decode("utf-8")
    update.message.reply_text(f'Вот правильный ответ: {right_answer}')

    return NEW_QUESTION


def new_question(update: Update, context: CallbackContext, questions, redis_connection) -> None:
    if update.message.text == 'Новый вопрос':
        random_key = random.choice(list(questions.keys()))
        question, answer = questions[random_key]
        redis_connection.set(update.message.from_user.id, answer)
        update.message.reply_text(question)
    else:
        redis_answer = redis_connection.get(update.message.from_user.id)
        right_answer = redis_answer.decode("utf-8").lower()
        user_answer = update.message.text.lower()

        if user_answer == right_answer:
            update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»')
        else:
            update.message.reply_text('Неправильно… Попробуешь ещё раз?')

        update.message.reply_text(update.message.text)


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        'До новых встреч!',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main():
    updater = Updater(config("TG_BOT_TOKEN"))
    redis_host = config("REDIS_HOST")
    redis_port = config("REDIS_PORT")
    redis_password = config("REDIS_PASSWORD")

    redis_connection = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)

    questions = load_quiz_questions()

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={

            NEW_QUESTION: [
                MessageHandler(Filters.regex(r'^Новый вопрос'),
                               functools.partial(handle_new_question_request,
                                                 questions=questions,
                                                 redis_connection=redis_connection
                                                 )
                               )
            ],

            ANSWER: [
                MessageHandler(Filters.regex(r'^Сдаться'),
                               functools.partial(handle_give_up, redis_connection=redis_connection)
                               ),
                MessageHandler(Filters.text,
                               functools.partial(handle_solution_attempt, redis_connection=redis_connection))
            ],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )


    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

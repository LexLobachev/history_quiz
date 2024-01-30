import logging
import random
from decouple import config

import vk_api
import redis
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from quiz_parser import load_quiz_questions


logger = logging.getLogger("vk_logger")


def handle_new_question_request(vk, event, redis_connection, keyboard, questions):
    random_key = random.choice(list(questions.keys()))
    question, answer = questions[random_key]
    redis_connection.set(event.peer_id, answer)
    vk.messages.send(
        user_id=event.user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )


def handle_solution_attempt(vk, event, redis_connection, keyboard):
    redis_answer = redis_connection.get(event.peer_id)
    right_answer = redis_answer.decode("utf-8").lower()
    user_answer = event.text.lower()

    if user_answer == right_answer:
        vk.messages.send(
            user_id=event.user_id,
            message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id()
        )
    else:
        vk.messages.send(
            user_id=event.user_id,
            message='Неправильно… Попробуешь ещё раз?',
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id()
        )


def handle_give_up(vk, event, redis_connection, keyboard):
    redis_answer = redis_connection.get(event.peer_id)
    right_answer = redis_answer.decode("utf-8")
    vk.messages.send(
        user_id=event.user_id,
        message=f'Вот правильный ответ: {right_answer}',
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )


def handle_give_score(vk, event, keyboard):
    vk.messages.send(
        user_id=event.user_id,
        message='Пока что функционал по подсчету ваших баллов за правильные ответы не интегрирован',
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )


def main():
    vk_session = vk_api.VkApi(token=config("VK_BOT_TOKEN"))
    redis_host = config("REDIS_HOST")
    redis_port = config("REDIS_PORT")
    redis_password = config("REDIS_PASSWORD")

    redis_connection = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)

    questions = load_quiz_questions()

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    logger.setLevel(logging.INFO)
    logger.info("ВК бот Викторины запущен")

    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text == 'start':
                    vk.messages.send(
                        user_id=event.user_id,
                        message='Здравствуйте! Нажмите на кнопку "Новый вопрос", чтобы получить случайный вопрос',
                        random_id=get_random_id(),
                        keyboard=keyboard.get_keyboard(),
                    )

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text == 'Новый вопрос':
                    handle_new_question_request(vk, event, redis_connection, keyboard, questions)

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text == 'Сдаться':
                    handle_give_up(vk, event, redis_connection, keyboard)

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text == 'Мой счет':
                    handle_give_score(vk, event, keyboard)

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    handle_solution_attempt(vk, event, redis_connection, keyboard)
        except Exception as message:
            logger.debug(message)


if __name__ == '__main__':
    main()

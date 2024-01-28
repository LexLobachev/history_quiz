
def load_quiz_questions():
    quiz = {}
    with open("quiz-questions/1vs1200.txt", "r", encoding="KOI8-R") as my_file:
        lines = my_file.read().split('\n\n')
        question_id = 1
        for line in lines:
            question_number = f'Вопрос {question_id}:'
            if 'Вопрос' in line:
                question = line.lstrip().replace('\n', ' ').split(': ', 1)[1]
                quiz.setdefault(question_number, []).append(question)
            elif 'Ответ' in line:
                answer = line.lstrip().replace('\n', ' ')
                quiz.setdefault(question_number, []).append(answer)
                question_id += 1
    return quiz


if __name__ == '__main__':
    load_quiz_questions()

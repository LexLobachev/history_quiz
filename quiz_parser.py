
def load_quiz_questions(parser_path):
    quiz = {}
    with open(parser_path, "r", encoding="KOI8-R") as file:
        lines = file.read().split('\n\n')
    question_id = 1
    for line in lines:
        question_number = f'Вопрос {question_id}:'
        if 'Вопрос' in line:
            question = line.lstrip().replace('\n', ' ').split(': ', 1)[1]
            quiz.setdefault(question_number, []).append(question)
        elif 'Ответ' in line:
            answer = line.lstrip().replace('\n', ' ').replace('.', '').replace('Ответ: ', '')
            quiz.setdefault(question_number, []).append(answer)
            question_id += 1
    return quiz


if __name__ == '__main__':
    load_quiz_questions(parser_path="quiz-questions/3f15.txt")

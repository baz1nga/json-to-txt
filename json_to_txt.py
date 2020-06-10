import os
import json
from datetime import datetime
from typing import Optional

import requests
from requests.exceptions import ConnectionError

DIR_NAME = 'tasks'
TASKS_DIR = os.path.join(os.getcwd(), DIR_NAME)
USERS_URL_LINK = 'https://json.medrating.org/users'
TODOS_URL_LINK = 'https://json.medrating.org/todos'
CURR_DATETIME = datetime.now().strftime('%d.%m.%Y %H:%M')
MAX_LENGHT = 50


def create_dir(dir_name) -> None:
    """Создание директории tasks"""
    if not os.path.isdir(dir_name):
        try:
            os.mkdir(dir_name)
        except PermissionError as error:
            print(f'Нет прав на создание директории:({error})')
            return None
    return None


def get_json_list(url: str) -> Optional[list]:
    """Получение данных со страницы c джсонами"""
    try:
        json_list = json.loads(requests.get(url).text)
    except ConnectionError as error:
        print(f'Невозможно получить данные со страницы:({error})')
        return None
    return json_list


def create_user_files(users: list, tasks: list) -> list:
    """Заполнение списка пользователей и их задач данными из двух списков."""
    completed_tasks = ''
    uncompleted_tasks = ''
    user_files = []

    for user in users:
        try:
            user_company = user.get('company').get('name')
        # Ошибка возникает, когда user.get('company') возвращает None
        except AttributeError:
            user_company = None

        content = f'{user.get("name")}<{user.get("email")}>{CURR_DATETIME}\n'
        content += f'{user_company}\n\n'

        for task in tasks:
            if task.get('userId') == user['id']:
                if len(task['title']) > MAX_LENGHT:
                    task_title = f'{task.get("title")[:MAX_LENGHT]}...'
                else:
                    task_title = task.get('title')
                if task['completed']:
                    completed_tasks += f'{task_title}\n'
                else:
                    uncompleted_tasks += f'{task_title}\n'

        content += f'Завершённые задачи:\n{completed_tasks}\n'
        content += f'Оставшиеся задачи:\n{uncompleted_tasks}\n'
        user_files.append(
            {'username': user.get('username'), 'task': content},
        )
        # Сбрасываем пулл задач для следующего пользователя.
        completed_tasks = ''
        uncompleted_tasks = ''
    return user_files


def create_user_report(files: list) -> None:
    """Запись файлов из списка в папку в виде .txt файлов"""
    for file in files:
        username = file['username']
        task = file['task']
        if username:
            file_path = os.path.join(TASKS_DIR, f'{username}.txt')
            if os.path.isfile(file_path):
                rewrite_report(file_path, username)
            try:
                with open(file_path, 'wb') as f:
                    f.write(task.encode('utf-8'))
            except IOError as error:
                print(f'Произошла ошибка Ввода/Вывода({error})')
                return None
    return None


def rewrite_report(file_path: str, username: str) -> None:
    """Бекап существующего файла под именем username_Y-m-dTH:M"""
    file_creation_time = os.path.getctime(file_path)
    # Приведение даты и времени создания файла к удобочитаемому виду.
    datetime_file = datetime.fromtimestamp(
        file_creation_time,
    ).strftime('%Y-%m-%dT%H:%M')  # Как вариант можно добавить :%S
    # Чтобы бекапы старых файлов можно было создавать с интервалом не в минуту
    # А с интервалом в кажую секунду.
    new_filename = f'{username}_{datetime_file}.txt'
    new_file_path = os.path.join(TASKS_DIR, new_filename)
    try:
        os.rename(file_path, new_file_path)
    except IOError as error:
        print(f'Произошла ошибка Ввода/Вывода({error})')
        return None
    return None


if __name__ == '__main__':
    create_dir(dir_name=DIR_NAME)
    users_list = get_json_list(url=USERS_URL_LINK)
    todos_list = get_json_list(url=TODOS_URL_LINK)
    pool_files = create_user_files(users_list, todos_list)
    create_user_report(pool_files)

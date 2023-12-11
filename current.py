from todoist_api_python.api import TodoistAPI
import json
from datetime import date
import datetime
import traceback
import logger
import sys

CLIENT_ID = '01fd238f1dca45c0b6a2ffdb3ff9d601'
CLIENT_SECRET = '51376de7dfe946418eff3c149f11cc54'
TEST_TOKEN = '48107fa1de46acc615b78411cea73524a10bb75b'

api = TodoistAPI(TEST_TOKEN)


def update_api(new_token):
    global TEST_TOKEN
    global api
    TEST_TOKEN = new_token
    api = TodoistAPI(TEST_TOKEN)


def get_project_id(project_name):
    projects = api.get_projects()
    myprojects = []
    for project in projects:
        if (project.name == project_name):
            myprojects.append(project.id)
    if len(myprojects) <= 0:
        # Not Found
        return None
    if len(myprojects) > 1:
        # too many objects
        return None
    return myprojects[0]


def delete_project(name):
    id = get_project_id(name)
    s = api.delete_project(project_id=id)


def add_project(name, parent_name=None, view_style='list', color="charcoal"):
    res = get_projects_names()
    if len(res) >= 7:
        return 'Переполнение. Купите тариф Про.'
    parent_id = get_project_id(parent_name)
    project = api.add_project(name=name, parent_id=parent_id, view_style=view_style, color=color)
    return project.id


def get_projects_names(url=False) -> list:
    projects = api.get_projects()
    if url:
        projects_names = [[project.name, project.url] for project in projects]
    else:
        projects_names = [project.name for project in projects]
    # print(projects_names)
    return projects_names


def rename_project(old_name, new_name):
    project_id = get_project_id(old_name)
    project = api.update_project(project_id=project_id, name=new_name)
    return project.url


def get_tasks(project_name=None):
    project_id = get_project_id(project_name)
    tasks = api.get_tasks(project_id=project_id)
    return tasks


def tasks_today(project_name=None):
    project_id = get_project_id(project_name)
    tasks = api.get_tasks(project_id=project_id)
    current_date = date.today()
    today_tasks = []
    for task in tasks:
        res = task.due
        if (res != None):
            if (task.due.date == str(current_date)):
                today_tasks.append(task)
    return today_tasks


def get_task_id(content, project_name):
    project_id = get_project_id(project_name)
    tasks = api.get_tasks(project_id=project_id)
    res = []
    for task in tasks:
        if task.content == content:
            res.append(task.id)
    if len(res) == 1:
        return res[0]
    else:
        return None


def close_task(content, project_name):
    task_id = get_task_id(content, project_name)
    is_success = api.close_task(task_id=task_id)


def add_task(content, project_name, due_date=None, description=None, priority=1):
    project_id = get_project_id(project_name)
    task = api.add_task(content=content, project_id=project_id, due_date=due_date, description=description,
                        priority=1)
    return task


def get_task_description(content, project_name):
    project_id = get_project_id(project_name)
    tasks = api.get_tasks(project_id=project_id)
    res = []
    for task in tasks:
        if task.content == content:
            res.append(task.description)
    if len(res) == 1:
        return res[0]
    else:
        return None


import telebot
from telebot import types

api_token = '6899437684:AAHuhona7h1r4kPmQTGe-SRULunPkWEqbg0'
bot = telebot.TeleBot(api_token, exception_handler=logger.ExcHandler())

old_name_dict = dict()  # chat id to old name
project_dict = dict()  # chat id to project
task_dict = dict()  # chat id to task
desc_dict = dict()


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/help"))
    bot.send_message(message.chat.id, f"Hello, {message.from_user.full_name}!",
                     reply_markup=markup)
    mesg = bot.send_message(message.chat.id,
                            f"Пожалуйста, авторизируйтесь. "
                            f"Для этого перейдите на https://app.todoist.com/app/settings/integrations/developer, "
                            f"скопируйте Токен API и пришлите в чат.",
                            reply_markup=markup)
    bot.register_next_step_handler(mesg, auth)


def auth(message):
    global TEST_TOKEN
    update_api(message.text)
    bot.send_message(message.chat.id, 'Авторизация прошла успешно')
    help(message)


@bot.message_handler(commands=["help"])
def help(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Авторизироваться", callback_data='get_project_id'))
    markup.add(types.InlineKeyboardButton("Посмотреть id проекта", callback_data='get_project_id'))
    markup.add(types.InlineKeyboardButton("Удалить проект", callback_data='delete_project'))
    markup.add(types.InlineKeyboardButton("Добавить проект", callback_data='add_project'))
    markup.add(types.InlineKeyboardButton("Изменить имя проекта", callback_data='rename_project'))
    markup.add(types.InlineKeyboardButton("Получить задания из проекта", callback_data='get_tasks'))
    markup.add(types.InlineKeyboardButton("Получить задания на сегодня из проекта", callback_data='get_tasks_today'))
    markup.add(types.InlineKeyboardButton("Закрыть задание", callback_data='close_task'))
    markup.add(types.InlineKeyboardButton("Создать задание", callback_data='add_task'))
    markup.add(types.InlineKeyboardButton("Посмотреть описание задания", callback_data='get_description'))
    if message.text == '\\help':
        bot.reply_to(message, "__*Help information:*__", reply_markup=markup, parse_mode='MarkdownV2')
    else:
        bot.send_message(message.chat.id, "__*Help information:*__", reply_markup=markup, parse_mode='MarkdownV2')


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'get_project_id':
        bot.send_message(callback.message.chat.id, '__*\> Посмотреть id проекта:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, get_proj_id)
    elif callback.data == 'delete_project':
        bot.send_message(callback.message.chat.id, '__*\> Удалить проект:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, del_proj_id)
    elif callback.data == 'add_project':
        bot.send_message(callback.message.chat.id, '__*\> Добавить проект:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, add_proj)
    elif callback.data == 'rename_project':
        bot.send_message(callback.message.chat.id, '__*\> Изменить имя проекта:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите старое название проекта')
        bot.register_next_step_handler(mesg, rename_proj)
    elif callback.data == 'get_tasks':
        bot.send_message(callback.message.chat.id, '__*\> Получить задания из проекта:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, get_tasks_bot)
    elif callback.data == 'get_tasks_today':
        bot.send_message(callback.message.chat.id, '__*\> Получить задания на сегодня из проекта:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, get_tasks_today_bot)
    elif callback.data == 'close_task':
        bot.send_message(callback.message.chat.id, '__*\> Закрыть задание:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, close_task_proj)
    elif callback.data == 'add_task':
        bot.send_message(callback.message.chat.id, '__*\> Создать задание:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, add_task_proj)
    elif callback.data == 'get_description':
        bot.send_message(callback.message.chat.id, '__*\> Посмотреть описание задания:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, get_desc_proj)


def get_proj_id(message):
    bot.send_message(message.chat.id, f'id "{message.text}" проекта: {get_project_id(message.text)}')


def del_proj_id(message):
    delete_project(message.text)
    bot.send_message(message.chat.id, f'Проект "{message.text}" удален')


def add_proj(message):
    add_project(message.text)
    bot.send_message(message.chat.id, f'Проект "{message.text}" добавлен')


def rename_proj(message):
    old_name_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите новое название проекта')
    bot.register_next_step_handler(mesg, add_proj_set_new)


def add_proj_set_new(message):
    rename_project(old_name_dict[message.chat.id], message.text)
    bot.send_message(message.chat.id, f'Проект "{old_name_dict[message.chat.id]}" переименован в "{message.text}"')
    old_name_dict.pop(message.chat.id)


def get_tasks_bot(message):
    bot.send_message(message.chat.id,
                     f'Задачи из проекта "{message.text}": {[el.content for el in get_tasks(message.text)]}')


def get_tasks_today_bot(message):
    bot.send_message(message.chat.id,
                     f'Задачи из проекта "{message.text}" на сегодня: {str([el.content for el in tasks_today(message.text)])}')


def close_task_proj(message):
    project_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите название задачи')
    bot.register_next_step_handler(mesg, close_task_cont)


def close_task_cont(message):
    close_task(message.text, project_dict[message.chat.id])
    bot.send_message(message.chat.id, f'Задача "{message.text}" из проекта "{project_dict[message.chat.id]}" закрыта')


def add_task_proj(message):
    project_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите название задачи')
    bot.register_next_step_handler(mesg, add_task_cont)


def add_task_cont(message):
    task_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите описание задачи')
    bot.register_next_step_handler(mesg, add_task_desc)


def add_task_desc(message):
    try:
        add_task(content=task_dict[message.chat.id], project_name=project_dict[message.chat.id],
                 description=message.text)
        bot.send_message(message.chat.id,
                         f'Задача "{task_dict[message.chat.id]}" добавлена в проект "{project_dict[message.chat.id]}"')
        task_dict.pop(message.chat.id)
        project_dict.pop(message.chat.id)
        current_func = traceback.extract_stack()[-1][2]
        logger.logger.debug(
            logger.make_logging_log_text(func_name=current_func,
                                         username=message.from_user.username,
                                         action=f"Task '{task_dict[message.chat.id]}' has been successfully added "
                                                f"to project '{project_dict[message.chat.id]}'"))
    except Warning as warn:
        current_func = traceback.extract_stack()[-1][2]
        logger.logger.warning(
            logger.make_logging_log_text(func_name=current_func, system_message=warn,
                                         username=message.from_user.username, message_text=message.text,
                                         action=f"Task '{task_dict[message.chat.id]}' has been successfully added "
                                                f"to project '{project_dict[message.chat.id]}'"))
    except Exception as err:
        current_func = traceback.extract_stack()[-1][2]
        logger.logger.error(
            logger.make_logging_err_text(func_name=current_func, error=err, username=message.from_user.username,
                                         message_text=message.text,
                                         action=f"Attempt to add task '{task_dict[message.chat.id]}'"
                                                f"to project '{project_dict[message.chat.id]}'"))


def get_desc_proj(message):
    try:
        desc_dict[message.chat.id] = message.text
        mesg = bot.send_message(message.chat.id, 'Введите название задачи')
        bot.register_next_step_handler(mesg, get_desc_task)
        current_func = traceback.extract_stack()[-1][2]
        logger.logger.debug(
            logger.make_logging_log_text(func_name=current_func,
                                         username=message.from_user.username,
                                         action='Input of project\'s name for future getting description of a task.'))
    except Warning as warn:
        current_func = traceback.extract_stack()[-1][2]
        logger.logger.warning(
            logger.make_logging_log_text(func_name=current_func, system_message=warn,
                                         username=message.from_user.username, message_text=message.text,
                                         action='Input of project\'s name for future getting description of a task.'))
    except Exception as err:
        current_func = traceback.extract_stack()[-1][2]
        logger.logger.error(
            logger.make_logging_err_text(func_name=current_func, error=err, username=message.from_user.username,
                                         message_text=message.text,
                                         action='Input of project\'s name for future getting description of a task.'))


def get_desc_task(message):
    desc = get_task_description(project_name=desc_dict[message.chat.id], content=message.text)
    if desc:
        bot.send_message(message.chat.id, f'Описание задачи "{message.text}": '
                                          f'"{desc}"')
    else:
        bot.send_message(message.chat.id,
                         f"Извините, задача '{message.text}' в проекте '{desc_dict[message.chat.id]}' не найдена.")
        logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                        action='User tried ti get description for a non-existing task.',
                                                        username=message.from_user.username))
    desc_dict.pop(message.chat.id)


bot.infinity_polling()

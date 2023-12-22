from datetime import date, datetime
import traceback
import telebot
from telebot import types
import pandas as pd
from todoist_api_python.api import TodoistAPI
import logger

CLIENT_ID = '01fd238f1dca45c0b6a2ffdb3ff9d601'
CLIENT_SECRET = '51376de7dfe946418eff3c149f11cc54'
TEST_TOKEN = '48107fa1de46acc615b78411cea73524a10bb75b'

# api = TodoistAPI(TEST_TOKEN)

api_token = '6899437684:AAHuhona7h1r4kPmQTGe-SRULunPkWEqbg0'
bot = telebot.TeleBot(api_token, exception_handler=logger.ExcHandler())
users_database = pd.read_csv('users.csv')

old_name_dict = dict()  # chat id to old name
project_dict = dict()  # chat id to project
task_dict = dict()  # chat id to task
desc_dict = dict()
dd_dict = dict()
select_proj_dict = dict()  # for func modify
select_task_dict = dict()  # for func modify
INF_TASK_SYMB = "-"
API_DATE_FORMAT = "%Y-%m-%d"


def get_api(chat_id: int) -> TodoistAPI:
    user_token = users_database[users_database['chat_id'] == chat_id]['token'].values[0]
    api = TodoistAPI(user_token)
    return api


def get_project_id(api, project_name):
    projects = api.get_projects()
    my_projects = []
    for project in projects:
        if project.name == project_name:
            my_projects.append(project.id)
    if len(my_projects) <= 0:
        # Not Found
        return None
    if len(my_projects) > 1:
        # too many objects
        return None
    return my_projects[0]


def delete_project(api, name):
    id = get_project_id(api, name)
    try:
        s = api.delete_project(project_id=id)
    except Exception as error:
        return error


def add_project(api, name, parent_name=None, view_style='list', color="charcoal"):
    try:
        res = get_projects_names(api)
        if len(res) >= 7:
            return 'Переполнение. Купите тариф Про.'
        parent_id = get_project_id(api, parent_name)
        project = api.add_project(name=name, parent_id=parent_id, view_style=view_style, color=color)
        return project.id
    except Exception as error:
        return error


def get_projects_names(api, url=False) -> list:
    try:
        projects = api.get_projects()

        if url:
            projects_names = [[project.name, project.url] for project in projects if project.name != 'Inbox']
        else:
            projects_names = [project.name for project in projects if project.name != 'Inbox']
        return projects_names
    except Exception as error:
        return error


def rename_project(api, old_name, new_name):
    try:
        project_id = get_project_id(api, old_name)
        project = api.update_project(project_id=project_id, name=new_name)
        return project.url
    except Exception as error:
        return error


def get_tasks(api, project_name=None):
    project_id = get_project_id(api, project_name)
    tasks = api.get_tasks(project_id=project_id)
    return tasks


def tasks_today(api, project_name=None):
    project_id = get_project_id(api, project_name)
    tasks = api.get_tasks(project_id=project_id)
    current_date = date.today()
    today_tasks = []
    for task in tasks:
        res = task.due
        if res:
            if task.due.date == str(current_date):
                today_tasks.append(task)
    return today_tasks


def get_task_id(api, content, project_name):
    project_id = get_project_id(api, project_name)
    tasks = api.get_tasks(project_id=project_id)
    res = []
    for task in tasks:
        if task.content == content:
            res.append(task.id)
    if len(res) == 1:
        return res[0]
    else:
        return None


def close_task(api, content, project_name):
    task_id = get_task_id(api, content, project_name)
    try:
        is_success = api.close_task(task_id=task_id)
    except Exception as error:
        return error


def add_task(api, content, project_name, due_date=None, description=None, priority=1):
    try:
        project_id = get_project_id(api, project_name)
        task = api.add_task(content=content, project_id=project_id, due_date=due_date, description=description,
                            priority=1)
        return task
    except Exception as error:
        return error


def get_task_description(api, content, project_name):
    project_id = get_project_id(api, project_name)
    tasks = api.get_tasks(project_id=project_id)
    res = []
    for task in tasks:
        if task.content == content:
            res.append(task.description)
    if len(res) == 1:
        return res[0]
    else:
        return None


help_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
help_markup.add(types.KeyboardButton("/help"))


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Hello, {message.from_user.full_name}!",
                     reply_markup=help_markup)
    mesg = bot.send_message(message.chat.id,
                            f"Пожалуйста, авторизируйтесь. "
                            f"Для этого перейдите на https://app.todoist.com/app/settings/integrations/developer, "
                            f"скопируйте Токен API и пришлите в чат.",
                            reply_markup=help_markup)
    bot.register_next_step_handler(mesg, auth)


def auth(message):
    global users_database
    chat_id = message.chat.id
    new_token = message.text

    line = users_database[users_database['chat_id'] == chat_id]
    if line.count()['chat_id'] == 0:
        users_database = pd.concat([users_database,
                                    pd.DataFrame([[chat_id, new_token]], columns=list(users_database.columns))])
    else:
        line_id = users_database[users_database['chat_id'] == chat_id].index[0]
        users_database.iloc[line_id, 1] = new_token
    users_database.to_csv('users.csv', header=True, index=False, sep=',')
    bot.send_message(message.chat.id, 'Авторизация прошла успешно')
    help(message)


def update_task(api, old_content, project_name, due_date=None, description=None, priority=1, new_content=None):
    try:
        project_id = get_project_id(api, project_name)
        task_id = get_task_id(api, old_content, project_name)
        if new_content:
            api.update_task(task_id=task_id, content=old_content, project_id=project_id, due_date=due_date,
                            description=description, priority=priority)
        else:
            api.update_task(task_id=task_id, content=new_content, project_id=project_id, due_date=due_date,
                            description=description, priority=priority)
    except Exception as error:
        return error


@bot.message_handler(commands=["help"])
def help(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Авторизироваться", callback_data='auth'))
    markup.add(types.InlineKeyboardButton("Посмотреть все проекты", callback_data='get_all_projects'))
    markup.add(types.InlineKeyboardButton("Удалить проект", callback_data='delete_project'))
    markup.add(types.InlineKeyboardButton("Добавить проект", callback_data='add_project'))
    markup.add(types.InlineKeyboardButton("Изменить имя проекта", callback_data='rename_project'))
    markup.add(types.InlineKeyboardButton("Получить задания из проекта", callback_data='get_tasks'))
    markup.add(types.InlineKeyboardButton("Получить задания на сегодня из проекта",
                                          callback_data='get_tasks_today'))
    markup.add(types.InlineKeyboardButton("Закрыть задание", callback_data='close_task'))
    markup.add(types.InlineKeyboardButton("Создать задание", callback_data='add_task'))
    markup.add(types.InlineKeyboardButton("Посмотреть описание задания", callback_data='get_description'))
    markup.add(types.InlineKeyboardButton("Изменить задание", callback_data='modify_task'))
    if message.text == '\\help':
        bot.reply_to(message, "__*Help information:*__", reply_markup=markup, parse_mode='MarkdownV2')
    else:
        bot.send_message(message.chat.id, "__*Help information:*__", reply_markup=markup, parse_mode='MarkdownV2')


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'auth':
        bot.send_message(callback.message.chat.id, '__*\> Авторизация:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id,
                                f"Перейдите на https://app.todoist.com/app/settings/integrations/developer, "
                                f"скопируйте Токен API и пришлите в чат.")
        bot.register_next_step_handler(mesg, auth)
    elif callback.data == 'delete_project':
        bot.send_message(callback.message.chat.id, '__*\> Удалить проект:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Close project: ")
    elif callback.data == 'add_project':
        bot.send_message(callback.message.chat.id, '__*\> Добавить проект:*__', 'MarkdownV2')
        mesg = bot.send_message(callback.message.chat.id, 'Введите название проекта')
        bot.register_next_step_handler(mesg, add_proj)
    elif callback.data == 'rename_project':
        bot.send_message(callback.message.chat.id, '__*\> Изменить имя проекта:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Change name: ")
    elif callback.data == 'get_tasks':
        bot.send_message(callback.message.chat.id, '__*\> Получить задания из проекта:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Get tasks from: ")
    elif callback.data == 'get_tasks_today':
        bot.send_message(callback.message.chat.id, '__*\> Получить задания на сегодня из проекта:*__',
                         'MarkdownV2')
        write_projects(callback.message.chat.id, "Get tasks for today from: ")
    elif callback.data == 'close_task':
        bot.send_message(callback.message.chat.id, '__*\> Закрыть задание:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Close task from: ")
    elif callback.data == 'add_task':
        bot.send_message(callback.message.chat.id, '__*\> Создать задание:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Add task to: ")
    elif callback.data == 'get_description':
        bot.send_message(callback.message.chat.id, '__*\> Посмотреть описание задания:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Get description from: ")
    elif callback.data == 'get_all_projects':
        bot.send_message(callback.message.chat.id, '__*\> Посмотреть все проекты:*__', 'MarkdownV2')
        output = ''
        api = get_api(callback.message.chat.id)
        for el in get_projects_names(api):
            output += el + '\n'
        bot.send_message(callback.message.chat.id, f'Ваши проекты: \n {str(output)}')
    elif callback.data == 'modify_task':
        bot.send_message(callback.message.chat.id, '__*\> Изменить задание:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Project: ")


def write_projects(chat_id, prefix):
    api = get_api(chat_id)
    projects = get_projects_names(api)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    if len(projects) == 0:
        bot.send_message(chat_id, "У вас нет проектов")
    else:
        for project in projects:
            markup.add(types.KeyboardButton(prefix + str(project)))
        bot.send_message(chat_id, "Ваши проекты", reply_markup=markup)


def write_tasks(message, get_prefix, set_prefix):
    api = get_api(message.chat.id)
    tasks = get_tasks(api, message.text[len(get_prefix):])
    select_proj_dict[message.chat.id] = message.text[len(get_prefix):]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for task in tasks:
        markup.add(types.KeyboardButton(set_prefix + str(task.content)))
    if not tasks:
        bot.reply_to(message, "В данном проекте нет заданий")
    bot.send_message(message.chat.id, "Выберите задание из списка:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith("Close project: "))
def del_proj_id(message):
    api = get_api(message.chat.id)
    delete_project(api, message.text[len("Close project: "):])
    bot.send_message(message.chat.id, f'Проект "{message.text[len("Close project: "):]}" удален')


def add_proj(message):
    api = get_api(message.chat.id)
    add_project(api, message.text)
    bot.send_message(message.chat.id, f'Проект "{message.text}" добавлен')


@bot.message_handler(func=lambda message: message.text.startswith("Change name: "))
def rename_proj(message):
    old_name_dict[message.chat.id] = message.text[len("Change name: "):]
    mesg = bot.send_message(message.chat.id, 'Введите новое название проекта')
    bot.register_next_step_handler(mesg, add_proj_set_new)


def add_proj_set_new(message):
    api = get_api(message.chat.id)
    rename_project(api, old_name_dict[message.chat.id], message.text)
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    bot.send_message(message.chat.id, f'Проект "{old_name_dict[message.chat.id]}" переименован в "{message.text}"',
                     reply_markup=markup)
    old_name_dict.pop(message.chat.id)


@bot.message_handler(func=lambda message: message.text.startswith("Get tasks from: "))
def get_tasks_bot(message: telebot.types.Message):
    api = get_api(message.chat.id)
    tasks_with_dd = []
    tasks_without_dd = []
    for task in get_tasks(api, message.text[16:]):
        if task.due is not None:
            tasks_with_dd.append(task)
            continue
        tasks_without_dd.append(task)
    tasks_with_dd.sort(key=lambda x: [datetime.strptime(x.due.date, API_DATE_FORMAT), -x.priority])
    tasks_without_dd.sort(key=lambda x: -x.priority)

    output_with_dd = ""
    iteration = 1
    for task in tasks_with_dd:
        output_with_dd += f"({iteration}) " + task.content + (f", deadline: {task.due.date}, "
                                                              f"priority = {task.priority}\n")
        iteration += 1

    output_without_dd = "\nВот задания, к которым дедлайн не указан:\n"
    for task in tasks_without_dd:
        output_without_dd += (f"({iteration}) " + task.content +
                              f', deadline: not mentioned, priority = {task.priority}\n')
        iteration += 1
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    bot.send_message(message.chat.id,
                     f'Задачи из проекта "{message.text}":\n' +
                     "Приоритет: число от 1 до 4 (1 -- слабый приоритет, 4 -- самый сильный приоритет)\n" +
                     output_with_dd + output_without_dd, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith("Get tasks for today from: "))
def get_tasks_today_bot(message: telebot.types.Message):
    api = get_api(message.chat.id)
    bot.send_message(message.chat.id,
                     f'Задачи из проекта "{message.text[26:]}" на сегодня: '
                     f'{str([el.content for el in tasks_today(api, message.text)])}')


@bot.message_handler(func=lambda message: message.text.startswith("Close task from: "))
def close_task_proj(message: telebot.types.Message):
    project_dict[message.chat.id] = message.text
    write_tasks(message, "Close task from: ", "Close: ")


@bot.message_handler(func=lambda message: message.text.startswith("Close: "))
def close_task_task(message: telebot.types.Message):
    api = get_api(message.chat.id)
    close_task(api, message.text[len("Close: "):], project_dict[message.chat.id])
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    bot.send_message(message.chat.id, f'Задача "{message.text[len("Close: "):]}" из проекта '
                                      f'"{project_dict[message.chat.id][len("Close task from: "):]}" закрыта',
                     reply_markup=markup)
    project_dict.pop(message.chat.id)


@bot.message_handler(func=lambda message: message.text.startswith("Add task to: "))
def add_task_proj(message):
    project_dict[message.chat.id] = message.text[len("Add task to: "):]
    mesg = bot.send_message(message.chat.id, 'Введите название задачи')
    bot.register_next_step_handler(mesg, add_task_cont)


def add_task_cont(message):
    task_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите описание задачи')
    bot.register_next_step_handler(mesg, add_task_date)


def add_task_date(message):
    desc_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите дедлайн в формате YYYY-MM-DD\n'
                                             'Если задание бессрочное, введите символ "-" (минус)')
    bot.register_next_step_handler(mesg, add_task_deadline)


def add_task_deadline(message):
    dd_dict[message.chat.id] = message.text if message.text != INF_TASK_SYMB else None
    mesg = bot.send_message(message.chat.id, 'Введите приоритет (целое число от 1 до 4)\n')
    # try-except
    bot.register_next_step_handler(mesg, add_task_wrapper)


def add_task_wrapper(message):
    api = get_api(message.chat.id)
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    try:
        current_func = traceback.extract_stack()[-1][2]
        try:
            priority = int(message.text)
        except ValueError:
            logger.logger.warning(
                logger.make_logging_log_text(func_name=current_func,
                                             username=message.from_user.username,
                                             system_message='Something went wrong with priority of the task.',
                                             action=f"Attempt to add task '{task_dict[message.chat.id]}'"
                                                    f"to project '{project_dict[message.chat.id]}'"))

            priority = 1
        add_task(api=api, content=task_dict[message.chat.id], project_name=project_dict[message.chat.id],
                 description=desc_dict[message.chat.id],
                 due_date=dd_dict[message.chat.id], priority=priority)
        bot.send_message(message.chat.id,
                         f'Задача "{task_dict[message.chat.id]}" добавлена в проект "{project_dict[message.chat.id]}"',
                         reply_markup=markup)
        logger.logger.debug(
            logger.make_logging_log_text(func_name=current_func,
                                         username=message.from_user.username,
                                         action=f"Task '{task_dict[message.chat.id]}' has been successfully added "
                                                f"to project '{project_dict[message.chat.id]}'"))
        task_dict.pop(message.chat.id)
        project_dict.pop(message.chat.id)
        desc_dict.pop(message.chat.id)
        dd_dict.pop(message.chat.id)
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


@bot.message_handler(func=lambda message: message.text.startswith("Get description from: "))
def get_desc_proj(message):
    try:
        desc_dict[message.chat.id] = message.text[len("Get description from: "):]
        write_tasks(message, "Get description from: ", "Task description: ")
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


@bot.message_handler(func=lambda message: message.text.startswith("Task description: "))
def get_desc_task(message):
    api = get_api(message.chat.id)
    desc = get_task_description(api=api, project_name=desc_dict[message.chat.id],
                                content=message.text[len("Task description: "):])
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    if desc:
        bot.send_message(message.chat.id, f'Описание задачи "{message.text[len("Task description: "):]}": '
                                          f'"{desc}"', reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
                         f"Извините, задача '{message.text}' в проекте '{desc_dict[message.chat.id]}' не найдена.",
                         reply_markup=markup)
        logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                        action='User tried to get description for a non-existing task.',
                                                        username=message.from_user.username))
    desc_dict.pop(message.chat.id)


@bot.message_handler(func=lambda message: message.text.startswith("Project: "))
def modify_task(message: telebot.types.Message):
    tasks = get_tasks(message.text[9:])
    select_proj_dict[message.chat.id] = message.text[9:]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for task in tasks:
        markup.add(types.KeyboardButton("Task: " + str(task.content)))
    if not tasks:
        bot.reply_to(message, "В данном проекте нет заданий")
    bot.send_message(message.chat.id, "Выберите задание из списка:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith("Task: "))
def task_handler(message: telebot.types.Message):
    select_task_dict[message.chat.id] = message.text[6:]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Content")
    markup.add("Description")
    markup.add("Deadline")
    markup.add("Priority")
    bot.send_message(message.chat.id, "Выберите тип изменения", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith("Content"))
def content_handler(message: telebot.types.Message):
    mesg = bot.send_message(message.chat.id, "Введите новое название задачи")
    bot.register_next_step_handler(mesg, modify_content)


def modify_content(message):
    api = get_api(message.chat.id)
    update_task(api, old_content=select_task_dict[message.chat.id], project_name=select_proj_dict[message.chat.id],
                new_content=message.text)
    select_task_dict.pop(message.chat.id)
    select_proj_dict.pop(message.chat.id)
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    bot.send_message(message.chat.id, "Задание успешно переименовано", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith("Description"))
def description_handler(message: telebot.types.Message):
    mesg = bot.send_message(message.chat.id, "Введите новое название задачи")
    bot.register_next_step_handler(mesg, modify_description)


def modify_description(message):
    api = get_api(message.chat.id)
    update_task(api=api, old_content=select_task_dict[message.chat.id], project_name=select_proj_dict[message.chat.id],
                description=message.text)
    select_task_dict.pop(message.chat.id)
    select_proj_dict.pop(message.chat.id)
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    bot.send_message(message.chat.id, "Описание задания успешно изменено", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith("Deadline"))
def deadline_handler(message: telebot.types.Message):
    mesg = bot.send_message(message.chat.id, 'Введите дедлайн в формате YYYY-MM-DD\n'
                                             'Если задание бессрочное, введите символ "-" (минус)')
    bot.register_next_step_handler(mesg, modify_deadline)


def modify_deadline(message):
    api = get_api(message.chat.id)
    if message.text == '-':
        update_task(api=api, old_content=select_task_dict[message.chat.id],
                    project_name=select_proj_dict[message.chat.id],
                    due_date=None)
    else:
        update_task(api=api, old_content=select_task_dict[message.chat.id],
                    project_name=select_proj_dict[message.chat.id],
                    due_date=message.text)
    select_task_dict.pop(message.chat.id)
    select_proj_dict.pop(message.chat.id)
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    bot.send_message(message.chat.id, "Дедлайн задания успешно изменен", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith("Priority"))
def priority_handler(message: telebot.types.Message):
    mesg = bot.send_message(message.chat.id, 'Введите новый приоритет задания (целое число от 1 до 4)')
    bot.register_next_step_handler(mesg, modify_priority)


def modify_priority(message):
    api = get_api(message.chat.id)
    update_task(api=api, old_content=select_task_dict[message.chat.id], project_name=select_proj_dict[message.chat.id],
                priority=message.text)
    select_task_dict.pop(message.chat.id)
    select_proj_dict.pop(message.chat.id)
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    bot.send_message(message.chat.id, "Приоритет задания успешно изменен", reply_markup=markup)


bot.infinity_polling()

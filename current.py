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

api_token = '6573328063:AAGYz8MHyQoLR7d7rO7Yd3eZE_rgeRrEG_0'
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
    try:
        user_token = users_database[users_database['chat_id'] == chat_id]['token'].values
        while len(user_token) < 1:
            logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                            chat_id=chat_id,
                                                            action=f'Non-authorised user tried to do smth.'))
            bot.next_step_backend = None
            bot.send_message(chat_id, "Упс, кажется, вы не авторизированы.")
            start()
            user_token = users_database[users_database['chat_id'] == chat_id]['token'].values
        api = TodoistAPI(user_token[0])
        return api
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         chat_id=chat_id, action=f'Getting token API for user'))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err, chat_id=chat_id,
                                         action=f'Getting token API for user'))


def get_project_id(api: TodoistAPI, project_name: str) -> str:
    try:
        projects = api.get_projects()
        my_projects = []
        for project in projects:
            if project.name == project_name:
                my_projects.append(project.id)
        if len(my_projects) <= 0:
            logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                            action=f"Attempt to get id for project '{project_name}'. "
                                                                   f"Failed: no projects with such name found."))
            return '-'
        if len(my_projects) > 1:
            logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                            action=f"Attempt to get id for project '{project_name}'. "
                                                                   f"Failed: too many projects ({len(my_projects)}) "
                                                                   f"with such name."))
            return '-'
        logger.logger.debug(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                         action=f"Got id for project '{project_name}': {my_projects[0]}."))
        return my_projects[0]
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         action=f"Attempt to get id for project '{project_name}'."))
        return '-'
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         action=f"Attempt to get id for project '{project_name}'."))
        return '-'


def delete_project(api: TodoistAPI, name: str) -> bool:
    try:
        id = get_project_id(api, name)
        if id == '-':
            raise RuntimeError(f'No project with name {name} found.')
        api.delete_project(project_id=id)
        logger.logger.debug(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                         action=f"Project '{name}' deleted successfully."))
        return True
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         action=f"Attempt to delete project '{name}'."))
        return False
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         action=f"Attempt to delete project '{name}'."))
        return False


def add_project(api: TodoistAPI, name: str, chat_id: int, parent_name: str | None = None, view_style='list',
                color="charcoal") -> bool:
    try:
        res = get_projects_names(api)
        if len(res) >= 7:
            logger.logger.info(
                logger.make_logging_log_text(func_name='add_project', chat_id=chat_id,
                                             action=f"Attempt to add project '{name}', but need Pro "
                                                    f"to add more projects"))
            bot.send_message(chat_id, 'Слишком много проектов. Купите тариф Про.')
            return False
        parent_id = get_project_id(api, parent_name)
        if parent_id == '-':
            raise RuntimeError(f'No project with name {parent_name} found.')
        api.add_project(name=name, parent_id=parent_id, view_style=view_style, color=color)
        logger.logger.debug(
            logger.make_logging_log_text(func_name='add_project', chat_id=chat_id,
                                         action=f"Successfully added project '{name}'"))
        return True

    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='add_project', system_message=warn,
                                         action=f"Attempt to add project '{name}'."))
        return False
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='add_project', error=err,
                                         action=f"Attempt to add project '{name}'."))
        return False


def get_projects_names(api: TodoistAPI, url: bool = False) -> list:
    try:
        projects = api.get_projects()
        if url:
            projects_names = [[project.name, project.url] for project in projects if project.name != 'Inbox']
        else:
            projects_names = [project.name for project in projects if project.name != 'Inbox']

        logger.logger.debug(
            logger.make_logging_log_text(func_name='get_projects_names',
                                         action=f"Got names of projects."))
        return projects_names
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='get_projects_names', system_message=warn,
                                         action=f"Attempt to get names of projects."))
        return []
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='get_projects_names', error=err,
                                         action=f"Attempt to get names of projects."))
        return []


def rename_project(api: TodoistAPI, old_name: str, new_name: str) -> bool:
    try:
        project_id = get_project_id(api, old_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {old_name} found.')
        is_success = api.update_project(project_id=project_id, name=new_name)
        if is_success:
            logger.logger.info(
                logger.make_logging_log_text(func_name='rename_project',
                                             action=f"Failed to rename project '{old_name}' to '{new_name}'."))
        else:
            logger.logger.debug(
                logger.make_logging_log_text(func_name='rename_project',
                                             action=f"Attempt rename project '{old_name}' to '{new_name}'."))
        return is_success
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='rename_project', system_message=warn,
                                         action=f"Attempt rename project '{old_name}' to '{new_name}'."))
        return False
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='rename_project', error=err,
                                         action=f"Attempt rename project '{old_name}' to '{new_name}'."))
        return False


def get_tasks(api: TodoistAPI, project_name: str) -> list:
    try:
        project_id = get_project_id(api, project_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {project_name} found.')
        tasks = api.get_tasks(project_id=project_id)
        logger.logger.debug(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                         action=f"Got all tasks from project '{project_name}'."))
        return tasks
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='get_tasks', system_message=warn,
                                         action=f"Attempt to get tasks from project {project_name}."))
        return []
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='get_tasks', error=err,
                                         action=f"Attempt to get tasks from project {project_name}."))
        return []


def tasks_today(api: TodoistAPI, project_name: str) -> list:
    try:
        project_id = get_project_id(api, project_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {project_name} found.')
        tasks = api.get_tasks(project_id=project_id)
        current_date = date.today()
        today_tasks = []
        for task in tasks:
            res = task.due
            if res:
                if task.due.date == str(current_date):
                    today_tasks.append(task)
        logger.logger.debug(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                         action=f"Got all tasks for today from project '{project_name}'."))
        return today_tasks
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='tasks_today', system_message=warn,
                                         action=f"Attempt to get tasks for today from project {project_name}."))
        return []
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='tasks_today', error=err,
                                         action=f"Attempt to get tasks for today from project {project_name}."))
        return []


def get_task_id(api: TodoistAPI, content: str, project_name: str) -> str:
    try:
        project_id = get_project_id(api, project_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {project_name} found.')
        tasks = api.get_tasks(project_id=project_id)
        res = []
        for task in tasks:
            if task.content == content:
                res.append(task.id)
        if len(res) == 1:
            return res[0]
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             action=f"Attempt to get task id for task from {project_name} with content "
                                                    f"'{content}', but too many tasks found({len(res)})."))
            return ''
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='get_task_id', system_message=warn,
                                         action=f"Attempt to get task id for {project_name}."))
        return ''
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='get_task_id', error=err,
                                         action=f"Attempt to get tasks for today from project {project_name}."))
        return ''


def close_task(api: TodoistAPI, content: str, project_name: str) -> bool:
    try:
        task_id = get_task_id(api, content, project_name)
        if task_id == '':
            logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                            action=f"Couldn't get task with id {task_id} "
                                                                   f"from project {project_name} to close."))
            return False
        is_success = api.close_task(task_id=task_id)
        if is_success:
            logger.logger.debug(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                             action=f"Successfully closed task with id {task_id} "
                                                                    f"from project {project_name}."))
        else:
            logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                            action=f"Couldn't close task with id {task_id} "
                                                                   f"from project {project_name}."))
        return is_success
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         action=f"Attempt to get task id for {project_name}."))
        return False
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         action=f"Attempt to get tasks for today from project {project_name}."))
        return False


def add_task(api: TodoistAPI, content: str, project_name: str, due_date=None, description: str | None = None,
             priority: int = 1) -> bool:
    try:
        project_id = get_project_id(api, project_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {project_name} found.')
        api.add_task(content=content, project_id=project_id, due_date=due_date, description=description,
                     priority=priority)
        logger.logger.debug(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                         action=f"Successfully added task '{content}' "
                                                                f"to project '{project_name}'."))
        return True
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         action=f"Attempt to add task '{content}' to project '{project_name}'."))
        return False
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         action=f"Attempt to add task '{content}' to project '{project_name}'."))
        return False


def get_task_description(api: TodoistAPI, content: str, project_name: str) -> str | None:
    try:
        project_id = get_project_id(api, project_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {project_name} found.')

        tasks = api.get_tasks(project_id=project_id)
        res = []
        for task in tasks:
            if task.content == content:
                res.append(task.description)
        if len(res) == 1:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             action=f"Successfully got task description for task '{content}' "
                                                    f"from project '{project_name}'."))
            return res[0]
        elif len(res) == 0:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             action=f"Failed to get task description for task '{content}' "
                                                    f"from project '{project_name}': no task found."))
            return None
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             action=f"Failed to get task description for task '{content}' "
                                                    f"from project '{project_name}': too many tasks found ({len(res)})."))
            return None
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         action=f"Attempt to add task '{content}' to project '{project_name}'."))
        return None
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         action=f"Attempt to add task '{content}' to project '{project_name}'."))
        return None


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message | None = None):
    help_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    help_markup.add(types.KeyboardButton("/help"))
    bot.send_message(message.chat.id, f"Hello, {message.from_user.full_name}!",
                     reply_markup=help_markup)
    mesg = bot.send_message(message.chat.id,
                            f"Пожалуйста, авторизируйтесь. "
                            f"Для этого перейдите на https://app.todoist.com/app/settings/integrations/developer, "
                            f"скопируйте Токен API и пришлите в чат.",
                            reply_markup=help_markup)
    bot.register_next_step_handler(mesg, auth)


def auth(message: telebot.types.Message):
    global users_database
    print(type(message))
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


def update_task(api: TodoistAPI, old_content: str, project_name: str, due_date=None, description: str | None = None,
                priority: int = 1, new_content: str | None = None) -> bool:
    try:
        project_id = get_project_id(api, project_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {project_name} found.')
        task_id = get_task_id(api, old_content, project_name)
        if task_id == '':
            logger.logger.info(logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                                            action=f"Couldn't get task with id {task_id} "
                                                                   f"from project {project_name} to update."))
            return False
        if new_content:
            api.update_task(task_id=task_id, content=old_content, project_id=project_id, due_date=due_date,
                            description=description, priority=priority)
        else:
            api.update_task(task_id=task_id, content=new_content, project_id=project_id, due_date=due_date,
                            description=description, priority=priority)
        logger.logger.debug(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                         action=f"Successfully updated task update task '{old_content}' "
                                                f"from project '{project_name}'."))
        return True
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         action=f"Attempt to update task '{old_content}' "
                                                f"from project '{project_name}'."))
        return False
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         action=f"Attempt to update task '{old_content}' "
                                                f"from project '{project_name}'."))
        return False


@bot.message_handler(commands=["help"])
def help(message: telebot.types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Авторизироваться", callback_data='auth'))
    markup.add(types.InlineKeyboardButton("Посмотреть все проекты", callback_data='get_all_projects'))
    markup.add(types.InlineKeyboardButton("Удалить проект", callback_data='delete_project'))
    markup.add(types.InlineKeyboardButton("Добавить проект", callback_data='add_project'))
    markup.add(types.InlineKeyboardButton("Изменить имя проекта", callback_data='rename_project'))
    markup.add(types.InlineKeyboardButton("Получить задания из проекта", callback_data='get_tasks'))
    markup.add(types.InlineKeyboardButton("Получить задания на сегодня из проекта", callback_data='get_tasks_today'))
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
        try:
            api = get_api(callback.message.chat.id)
            for el in get_projects_names(api):
                output += el + '\n'
            bot.send_message(callback.message.chat.id, f'Ваши проекты: \n {str(output)}')
        except Exception as err:
            logger.logger.error(
                logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                             chat_id=callback.message.chat.id,
                                             action=f"Attempt to get all projects"))
    elif callback.data == 'modify_task':
        bot.send_message(callback.message.chat.id, '__*\> Изменить задание:*__', 'MarkdownV2')
        write_projects(callback.message.chat.id, "Project: ")


def write_projects(chat_id, prefix):
    try:
        api = get_api(chat_id)
        projects = get_projects_names(api)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        if len(projects) == 0:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], chat_id=chat_id,
                                             action=f"Attempt to make buttons of projects, but no projects found. "
                                                    f"Prefix: {prefix}."))
            bot.send_message(chat_id, "У вас нет проектов")
        else:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], chat_id=chat_id,
                                             action=f"Made buttons of projects, prefix: {prefix}."))
            for project in projects:
                markup.add(types.KeyboardButton(prefix + str(project)))
            bot.send_message(chat_id, "Ваши проекты", reply_markup=markup)

    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         chat_id=chat_id,
                                         action=f"Attempt to make buttons of projects, prefix: {prefix}"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err, chat_id=chat_id,
                                         action=f"Attempt to make buttons of projects, prefix: {prefix}"))


def write_tasks(message: telebot.types.Message, get_prefix, set_prefix):
    try:
        api = get_api(message.chat.id)
        tasks = get_tasks(api, message.text[len(get_prefix):])
        if len(tasks) == 0:
            bot.reply_to(message, "В данном проекте нет заданий")
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Attempt to make buttons of tasks, but no tasks found. "
                                                    f"get_prefix={get_prefix}, set_prefix={set_prefix}."))
            return

        select_proj_dict[message.chat.id] = message.text[len(get_prefix):]
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for task in tasks:
            markup.add(types.KeyboardButton(set_prefix + str(task.content)))
        logger.logger.debug(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to make buttons of tasks, ({len(tasks)}) found. "
                                                f"get_prefix={get_prefix}, set_prefix = {set_prefix}."))
        bot.send_message(message.chat.id, "Выберите задание из списка:", reply_markup=markup)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to make buttons of tasks. "
                                                f"get_prefix={get_prefix}, set_prefix={set_prefix}."))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to make buttons of tasks. "
                                                f"get_prefix={get_prefix}, set_prefix={set_prefix}."))


@bot.message_handler(func=lambda message: message.text.startswith("Close project: "))
def del_proj_id(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        project_name = message.text[len("Close project: "):]
        is_successful = delete_project(api, project_name)
        if is_successful:
            bot.send_message(message.chat.id, f'Проект "{project_name}" удален')
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, message_text=message.text,
                                             action=f"Successfully deleted project '{project_name}'"))
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, message_text=message.text,
                                             action=f"Failed to delete project '{project_name}'"))
            bot.send_message(message.chat.id, f'Упс, что-то пошло не так')


    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, message_text=message.text,
                                         action=f"Attempt to delete project"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, message_text=message.text,
                                         action=f"Attempt to delete project"))


def add_proj(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        is_successful = add_project(api, message.text, message.chat.id)
        if is_successful:
            bot.send_message(message.chat.id, f'Проект "{message.text}" добавлен')
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username,
                                             action=f"Successfully added project '{message.text}'"))
        else:
            bot.send_message(message.chat.id, 'Упс, что-то пошло не так')
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], chat_id=message.chat.id,
                                             username=message.chat.username, message_text=message.text,
                                             action=f"Failed to add project '{message.text}'"))
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to add project"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to add project"))


@bot.message_handler(func=lambda message: message.text.startswith("Change name: "))
def rename_proj(message: telebot.types.Message):
    old_name_dict[message.chat.id] = message.text[len("Change name: "):]
    mesg = bot.send_message(message.chat.id, 'Введите новое название проекта')
    bot.register_next_step_handler(mesg, add_proj_set_new)


def add_proj_set_new(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        is_successful = rename_project(api, old_name_dict[message.chat.id], message.text)
        if not is_successful:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], chat_id=message.chat.id,
                                             username=message.chat.username, message_text=message.text,
                                             action=f"Failed to rename project '{old_name_dict[message.chat.id]}'"))
            bot.send_message(message.chat.id, f'Упс, не удалось переименовать проект '
                                              f'"{old_name_dict[message.chat.id]}" в "{message.text}"')
            return
        markup = types.ReplyKeyboardMarkup()
        markup.add("/help")
        bot.send_message(message.chat.id, f'Проект "{old_name_dict[message.chat.id]}" переименован в "{message.text}"',
                         reply_markup=markup)
        old_name_dict.pop(message.chat.id)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to rename project"))
    except ValueError as err:
        bot.send_message(message.chat.id, f'Упс, похоже, проект "{old_name_dict[message.chat.id]}" не существует')
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id,
                                         action=f"Failed to rename project '{old_name_dict[message.chat.id]}', "))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err, chat_id=message.chat.id,
                                         username=message.chat.username, message_text=message.text,
                                         action=f"Failed to rename project '{old_name_dict[message.chat.id]}'"))


@bot.message_handler(func=lambda message: message.text.startswith("Get tasks from: "))
def get_tasks_bot(message: telebot.types.Message):
    try:
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
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to get tasks from project."))
    except Exception as err:
        bot.send_message(message.chat.id, 'Упс, что-то пошло не так.')
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to get tasks from project."))


@bot.message_handler(func=lambda message: message.text.startswith("Get tasks for today from: "))
def get_tasks_today_bot(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        bot.send_message(message.chat.id,
                         f'Задачи из проекта "{message.text[26:]}" на сегодня: '
                         f'{str([el.content for el in tasks_today(api, message.text)])}')
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to take tasks for today"))
    except Exception as err:
        bot.send_message(message.chat.id, 'Упс, что-то пошло не так.')
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to take tasks for today"))


@bot.message_handler(func=lambda message: message.text.startswith("Close task from: "))
def close_task_proj(message: telebot.types.Message):
    project_dict[message.chat.id] = message.text
    write_tasks(message, "Close task from: ", "Close: ")


@bot.message_handler(func=lambda message: message.text.startswith("Close: "))
def close_task_task(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        markup = types.ReplyKeyboardMarkup()
        markup.add("/help")
        is_success = close_task(api, message.text[len("Close: "):], project_dict[message.chat.id])
        if is_success:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Successfully closed task"))
            bot.send_message(message.chat.id, f'Задача "{message.text[len("Close: "):]}" из проекта '
                                              f'"{project_dict[message.chat.id][len("Close task from: "):]}" закрыта',
                             reply_markup=markup)
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Failed to close task"))
            bot.send_message(message.chat.id, f'Не удалось закрыть задачу "{message.text[len("Close: "):]}" из проекта '
                                              f'"{project_dict[message.chat.id][len("Close task from: "):]}"',
                             reply_markup=markup)
        project_dict.pop(message.chat.id)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to close task."))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, message_text=message.text,
                                         chat_id=message.chat.id, action=f"Attempt to close task."))


@bot.message_handler(func=lambda message: message.text.startswith("Add task to: "))
def add_task_proj(message: telebot.types.Message):
    project_dict[message.chat.id] = message.text[len("Add task to: "):]
    mesg = bot.send_message(message.chat.id, 'Введите название задачи')
    bot.register_next_step_handler(mesg, add_task_cont)


def add_task_cont(message: telebot.types.Message):
    task_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите описание задачи')
    bot.register_next_step_handler(mesg, add_task_date)


def add_task_date(message: telebot.types.Message):
    desc_dict[message.chat.id] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите дедлайн в формате YYYY-MM-DD\n'
                                             'Если задание бессрочное, введите символ "-" (минус)')
    bot.register_next_step_handler(mesg, add_task_deadline)


def add_task_deadline(message: telebot.types.Message):
    dd_dict[message.chat.id] = message.text if message.text != INF_TASK_SYMB else None
    mesg = bot.send_message(message.chat.id, 'Введите приоритет (целое число от 1 до 4)\n')
    bot.register_next_step_handler(mesg, add_task_wrapper)


def add_task_wrapper(message: telebot.types.Message):
    api = get_api(message.chat.id)
    markup = types.ReplyKeyboardMarkup()
    markup.add("/help")
    try:
        try:
            priority = int(message.text)
        except ValueError:
            logger.logger.warning(
                logger.make_logging_log_text(func_name='add_task_wrapper',
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
            logger.make_logging_log_text(func_name='add_task_wrapper',
                                         username=message.from_user.username,
                                         action=f"Task '{task_dict[message.chat.id]}' has been successfully added "
                                                f"to project '{project_dict[message.chat.id]}'"))
        task_dict.pop(message.chat.id)
        project_dict.pop(message.chat.id)
        desc_dict.pop(message.chat.id)
        dd_dict.pop(message.chat.id)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='add_task_wrapper', system_message=warn,
                                         username=message.from_user.username, message_text=message.text,
                                         action=f"Task '{task_dict[message.chat.id]}' has been successfully added "
                                                f"to project '{project_dict[message.chat.id]}'"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='add_task_wrapper', error=err, username=message.from_user.username,
                                         message_text=message.text,
                                         action=f"Attempt to add task '{task_dict[message.chat.id]}'"
                                                f"to project '{project_dict[message.chat.id]}'"))


@bot.message_handler(func=lambda message: message.text.startswith("Get description from: "))
def get_desc_proj(message: telebot.types.Message):
    try:
        desc_dict[message.chat.id] = message.text[len("Get description from: "):]
        write_tasks(message, "Get description from: ", "Task description: ")
        logger.logger.debug(
            logger.make_logging_log_text(func_name='get_desc_proj',
                                         username=message.from_user.username,
                                         action='Input of project\'s name for future getting description of a task.'))
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name='get_desc_proj', system_message=warn,
                                         username=message.from_user.username, message_text=message.text,
                                         action='Input of project\'s name for future getting description of a task.'))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='get_desc_proj', error=err, username=message.from_user.username,
                                         message_text=message.text,
                                         action='Input of project\'s name for future getting description of a task.'))


@bot.message_handler(func=lambda message: message.text.startswith("Task description: "))
def get_desc_task(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        desc = get_task_description(api=api, project_name=desc_dict[message.chat.id],
                                    content=message.text[len("Task description: "):])
        markup = types.ReplyKeyboardMarkup()
        markup.add("/help")
        if desc:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], username=message.chat.username,
                                             chat_id=message.chat.id,
                                             action=f"Got description for task {message.text} from project "
                                                    f"{desc_dict[message.chat.id]}."))
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
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to get description for task {message.text} "
                                                f"from project {desc_dict[message.chat.id]}."))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to get description for task {message.text} "
                                                f"from project {desc_dict[message.chat.id]}."))


@bot.message_handler(func=lambda message: message.text.startswith("Project: "))
def modify_task(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        tasks = get_tasks(api, message.text[9:])
        select_proj_dict[message.chat.id] = message.text[9:]
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        if len(tasks) == 0:
            bot.reply_to(message, "В данном проекте нет заданий")
        else:
            for task in tasks:
                markup.add(types.KeyboardButton("Task: " + str(task.content)))
            bot.send_message(message.chat.id, "Выберите задание из списка:", reply_markup=markup)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to make buttons for tasks from project {message.text[9:]}."))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to get description for task {message.text} "
                                                f"from project {desc_dict[message.chat.id]}."))


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


def modify_content(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        is_success = update_task(api=api, old_content=select_task_dict[message.chat.id],
                                 project_name=select_proj_dict[message.chat.id],
                                 new_content=message.text)
        select_task_dict.pop(message.chat.id)
        select_proj_dict.pop(message.chat.id)
        markup = types.ReplyKeyboardMarkup()
        markup.add("/help")
        if is_success:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Successfully renamed task"))
            bot.send_message(message.chat.id, "Задание успешно переименовано", reply_markup=markup)
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Failed to rename task"))
            bot.send_message(message.chat.id, "Упс, что-то пошло не так", reply_markup=markup)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt rename task"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt rename task"))


@bot.message_handler(func=lambda message: message.text.startswith("Description"))
def description_handler(message: telebot.types.Message):
    mesg = bot.send_message(message.chat.id, "Введите новое название задачи")
    bot.register_next_step_handler(mesg, modify_description)


def modify_description(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        is_success = update_task(api=api, old_content=select_task_dict[message.chat.id],
                                 project_name=select_proj_dict[message.chat.id],
                                 description=message.text)
        select_task_dict.pop(message.chat.id)
        select_proj_dict.pop(message.chat.id)
        markup = types.ReplyKeyboardMarkup()
        markup.add("/help")
        if is_success:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Successfully changed description of task"))
            bot.send_message(message.chat.id, "Описание задания успешно изменено", reply_markup=markup)
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Failed to change description of task"))
            bot.send_message(message.chat.id, "Упс, что-то пошло не так", reply_markup=markup)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to change description of task"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to change description of task"))


@bot.message_handler(func=lambda message: message.text.startswith("Deadline"))
def deadline_handler(message: telebot.types.Message):
    mesg = bot.send_message(message.chat.id, 'Введите дедлайн в формате YYYY-MM-DD\n'
                                             'Если задание бессрочное, введите символ "-" (минус)')
    bot.register_next_step_handler(mesg, modify_deadline)


def modify_deadline(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        if message.text == '-':
            is_success = update_task(api=api, old_content=select_task_dict[message.chat.id],
                                     project_name=select_proj_dict[message.chat.id])
        else:
            is_success = update_task(api=api, old_content=select_task_dict[message.chat.id],
                                     project_name=select_proj_dict[message.chat.id],
                                     due_date=message.text)
        select_task_dict.pop(message.chat.id)
        select_proj_dict.pop(message.chat.id)
        markup = types.ReplyKeyboardMarkup()
        markup.add("/help")
        if is_success:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Successfully changed deadline of task"))
            bot.send_message(message.chat.id, "Дедлайн задания успешно изменен", reply_markup=markup)
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Failed to change deadline of task"))
            bot.send_message(message.chat.id, "Упс, что-то пошло не так", reply_markup=markup)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to change deadline of task"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to change deadline of task"))


@bot.message_handler(func=lambda message: message.text.startswith("Priority"))
def priority_handler(message: telebot.types.Message):
    mesg = bot.send_message(message.chat.id, 'Введите новый приоритет задания (целое число от 1 до 4)')
    bot.register_next_step_handler(mesg, modify_priority)


def modify_priority(message: telebot.types.Message):
    try:
        api = get_api(message.chat.id)
        is_success = update_task(api=api, old_content=select_task_dict[message.chat.id],
                                 project_name=select_proj_dict[message.chat.id], priority=int(message.text))
        select_task_dict.pop(message.chat.id)
        select_proj_dict.pop(message.chat.id)
        markup = types.ReplyKeyboardMarkup()
        markup.add("/help")
        if is_success:
            logger.logger.debug(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Successfully changed priority of task"))
            bot.send_message(message.chat.id, "Приоритет задания успешно изменен", reply_markup=markup)
        else:
            logger.logger.info(
                logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2],
                                             username=message.chat.username, chat_id=message.chat.id,
                                             action=f"Failed to change priority of task"))
            bot.send_message(message.chat.id, "Упс, что-то пошло не так", reply_markup=markup)
    except Warning as warn:
        logger.logger.warning(
            logger.make_logging_log_text(func_name=traceback.extract_stack()[-1][2], system_message=warn,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to change priority of task"))
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name=traceback.extract_stack()[-1][2], error=err,
                                         username=message.chat.username, chat_id=message.chat.id,
                                         action=f"Attempt to change priority of task"))


bot.infinity_polling()

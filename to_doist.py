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

def get_projects_names(api: TodoistAPI, url: bool = False) -> list|None:
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
        return None
    except Exception as err:
        logger.logger.error(
            logger.make_logging_err_text(func_name='get_projects_names', error=err,
                                         action=f"Attempt to get names of projects."))
        return None


def rename_project(api: TodoistAPI, old_name: str, new_name: str) -> bool:
    try:
        project_id = get_project_id(api, old_name)
        if project_id == '-':
            raise RuntimeError(f'No project with name {old_name} found.')
        is_success = api.update_project(project_id=project_id, name=new_name)
        if is_success:
            logger.logger.info(
                logger.make_logging_log_text(func_name='rename_project',
                                             action=f"Renamed project '{old_name}' to '{new_name}'."))
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

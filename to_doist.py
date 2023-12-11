from todoist_api_python.api import TodoistAPI
import json
from datetime import date
import datetime

TEST_TOKEN = '38847922db0efe60a38e91fe73ec190f19f2ecfb'

api = TodoistAPI(TEST_TOKEN)

def get_project_id(project_name):
    projects = api.get_projects()
    myprojects = []
    for project in projects:
        if (project.name == project_name):
            myprojects.append(project.id)
    if len(myprojects) <= 0:
        #Not Found
        return None
    if len(myprojects) > 1:
        #too many objects
        return None
    return myprojects[0]

def delete_project(name):
    id = get_project_id(name)
    try:
        s = api.delete_project(project_id=id)
    except Exception as error:
        return error

delete_project('Test 2')
# получение существующих проектов
# можно вернуть с ссылкой на проект
def get_projects_names(url=False)->list:
    try:
        projects = api.get_projects()
        if (url):
            projects_names = [[project.name, project.url] for project in projects]
        else:
            projects_names = [project.name for project in projects]
        #print(projects_names)
        return projects_names
    except Exception as error:
        return error


#добавить проект
#можно сделать дочерний проект и выбрать view_style
# view_style - два варианта - list или on_board
#можно сделать дочерний проект и выбрать view_style
# view_style - два варианта - list или on_board
def add_project(name, parent_name=None, view_style='list', color= "charcoal"):
    try:
        res = get_projects_names()
        if len(res) >= 7:
            return 'Переполнение. Купите тариф Про.'
        parent_id = get_project_id(parent_name)
        project = api.add_project(name=name, parent_id=parent_id, view_style=view_style, color=color)
        return project.id
    except Exception as error:
        return(error)



def rename_project(old_name, new_name):
    try:
        project_id = get_project_id(old_name)
        project = api.update_project(project_id=project_id, name=new_name)
        return project.url
    except Exception as error:
        return error

def style_project(name, color="charcoal", favourite=False, view_style='list'):
    try:
        project_id = get_project_id(name)
        project = api.update_project(project_id=project_id, name=name, color=color, favourite=favourite, view_style=view_style)
        return project.url
    except Exception as error:
        return error

def get_tasks(project_name=None):
    project_id = get_project_id(project_name)
    tasks = api.get_tasks(project_id=project_id)
    return tasks

def tasks_today(project_name=None):
    project_id = get_project_id(project_name)
    tasks = api.get_tasks(project_id=project_id)
    current_date = date.today()
    today_tasks = []
    print(current_date)
    for task in tasks:
        res = task.due
        if (res != None):
            if (task.due.date == str(current_date)):
                today_tasks.append(task)
    return today_tasks
tasks_today()

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
    try:
        is_success = api.close_task(task_id=task_id)
    except Exception as error:
        return error
#print(close_task('num2', 'Test 1'))

#priority 1 to 4(urgent)
#due - when
# description: "",
#     due: {
#         date: "2016-09-01",
#         is_recurring: false,
#         datetime: "2016-09-01T12:00:00.000000Z",
#         string: "tomorrow at 12",
#         timezone: "Europe/Moscow"
#     },

def add_task(content, project_name, due_date=None, desсription=None, priority=1):
    try:
        project_id = get_project_id(project_name)
        task = api.add_task(content=content, project_id=project_id, due_date=due_date, desсription=desсription, priority=priority)
        return task
    except Exception as error:
        return error

def update_task(old_content, project_name, due_date=None, desription=None, priority=1, new_content=None):
    try:
        project_id = get_project_id(project_name)
        print(1)
        task_id = get_task_id(old_content, project_name)
        print(task_id)
        if (new_content != None):
            task = api.update_task(task_id=task_id, content=new_content, project_id=project_id, due_date=due_date, desription=desription, priority=1)
        else:
            task = api.update_task(task_id=task_id, content=old_content, project_id=project_id, due_date=due_date, desription=desription, priority=1)
        print(task)
    except Exception as error:
        return error

#add_task('num88', 'Test 1',  '2023-10-11', 'be free', 3)

#задания - сдавать сегодня

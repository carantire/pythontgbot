import sys
import logging
import traceback

import telebot


class WarningFilter(logging.Filter):
    def filter(self, record):
        return record.levelno <= logging.WARNING


class ErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.ERROR


def make_logging_err_text(error, func_name, action=None, username=None, message_text=None) -> str:
    logging_text = (f"Error occured in function {func_name}. Error class: {error.__class__.__name__}.\n"
                    f"Error message:\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n")
    if action:
        logging_text += f"User's action: {action} "
    if username:
        logging_text += f'Username: {username}. '
    if message_text:
        logging_text += f'User\'s message: {message_text}.'

    return logging_text


def make_logging_log_text(func_name, system_message=None, action=None, username=None, message_text=None) -> str:
    logging_text = f"Function {func_name}."
    if system_message:
        logging_text += f'System info: {system_message}.'
    logging_text += '\n'
    if action:
        logging_text += f"User's action: {action} "
    if username:
        logging_text += f'Username: {username}. '
    if message_text:
        logging_text += f'User\'s message: {message_text}.'

    return logging_text


logger = logging.getLogger("logger_todoist_bot")
logger.setLevel(logging.DEBUG)

handler_log = logging.FileHandler(f"logging_telebot.log", mode='w')
handler_log.addFilter(WarningFilter())
handler_log.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)s %(levelname)s. %(message)s\n"
                                               "_________________________________________________\n"))
logger.addHandler(handler_log)

handler_err = logging.StreamHandler(sys.stderr)
handler_err.addFilter(ErrorFilter())
handler_err.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)s %(levelname)s. %(message)s\n"
                                               "_________________________________________________\n"))
logger.addHandler(handler_err)


class ExcHandler:
    def handle(self, e):
        if isinstance(e, Warning):
            ...
        elif isinstance(e, Exception):
            ...


class ExceptionWithUserInfo(Exception):
    def __init__(self, error, func_name, action=None, username=None, message_text=None):
        self.error = error
        self.func_name = func_name
        self.action = action
        self.username = username
        self.message_text = message_text


class WarningWithUserInfo(Warning):
    def __init__(self, system_message, func_name, action=None, username=None, message_text=None):
        self.system_message = system_message
        self.func_name = func_name
        self.action = action
        self.username = username
        self.message_text = message_text

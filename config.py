# encoding: utf-8
from os import getcwd
SECRET_KEY = 'a unique and long key'
TITLE = 'Test Wiki, Please Ignore'
HISTORY_SHOW_MAX = 30
PIC_BASE = '/static/content/'
CONTENT_DIR = f'{getcwd()}/content'
USER_DIR = f'{getcwd()}/user'
NUMBER_OF_HISTORY = 5
PRIVATE = True
LOG_LEVEL = 'DEBUG' #Should be set to INFO in prod
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'error': {
            'format': '%(asctime)s  [%(levelname)s]: %(name)s-%(process)d | %(module)s(%(lineno)s)- %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'Riki_rotating_file_handler': {
            'level': 'DEBUG',
            'formatter': 'error',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{getcwd()}\\logs\\Riki.log',
            'mode': 'a',
            'maxBytes': 1048576,
            'backupCount': 10
        }, 'DB_rotating_file_handler': {
            'level': 'DEBUG',
            'formatter': 'error',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{getcwd()}\\logs\\Riki_DB.log',
            'mode': 'a',
            'maxBytes': 1048576,
            'backupCount': 10
        }, 'external_rotating_file_handler': {
            'level': 'DEBUG',
            'formatter': 'error',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{getcwd()}\\logs\\external.log',
            'mode': 'a',
            'maxBytes': 1048576,
            'backupCount': 10
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['external_rotating_file_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
        'wiki': {
            'handlers': ['Riki_rotating_file_handler'],
            'level': LOG_LEVEL,
            'propagate': False
        },
        'database': {
            'handlers': ['DB_rotating_file_handler'],
            'level': LOG_LEVEL,
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['Riki_rotating_file_handler'],
            'level': LOG_LEVEL,
            'propagate': False
        },
    }
}


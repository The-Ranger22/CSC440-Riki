#!/Users/smcho/virtualenv/riki/bin/python

# -*- coding: utf-8 -*-
import logging
import logging.config
import os

from config import LOGGING_CONFIG
from wikiDB import setup, db_file_path

from flask_sqlalchemy import SQLAlchemy

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger('wiki')

from wiki import create_app

directory = os.getcwd()
log.debug(f'CWD: {directory}')
app = create_app(directory)
db_file = os.getcwd() + "/" + 'wiki' + '.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + db_file
db = SQLAlchemy(app)
db.init_app(app)

if __name__ == '__main__':
    #Check to see if the database exists, if not create the DB file
    if not os.path.exists(db_file):
        setup()

    # Launch Wiki Web application
    app.run(host='0.0.0.0', debug=True)
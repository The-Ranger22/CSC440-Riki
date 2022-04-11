#!/Users/smcho/virtualenv/riki/bin/python

# -*- coding: utf-8 -*-
import os
from wikiDB import setup, db_file_path

from flask_sqlalchemy import SQLAlchemy

from wiki import create_app

directory = os.getcwd()
app = create_app(directory)
db_file = os.getcwd() + "/" + 'wiki' + '.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + db_file
db = SQLAlchemy(app)
db.init_app(app)

if __name__ == '__main__':
    # Check to see if the database exists, if not create the DB file
    if not os.path.exists(db_file_path()):
        setup()

    # Launch Wiki Web application
    app.run(host='0.0.0.0', debug=True)

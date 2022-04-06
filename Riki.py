#!/Users/smcho/virtualenv/riki/bin/python

# -*- coding: utf-8 -*-
import os
from wikiDB import setup, db_file_path

from wiki import create_app

directory = os.getcwd()
app = create_app(directory)

if __name__ == '__main__':
    # Check to see if the database exists, if not create the DB file
    if not os.path.exists(db_file_path()):
        setup()

    # Launch Wiki Web application
    app.run(host='0.0.0.0', debug=True)
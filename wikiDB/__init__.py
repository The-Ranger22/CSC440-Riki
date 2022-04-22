import logging
from sqlite3 import connect, Connection
from os import getcwd
from os.path import exists

import config
from datetime import datetime

log = logging.getLogger('database')
db_name = 'wiki'
file_ext = ".db"

def db_file_path():
    return getcwd() + "/" + db_name + file_ext

def setup():
    loc = __path__[0]
    log.info("beginning db setup.")
    with open(f"{loc}/SQL/create_db.sql", "r") as file:
        query = file.read()
    with connect(db_name + file_ext) as conn:
        if not isinstance(conn, Connection):
            log.critical("Unable to setup DB. ")
            raise TypeError
        log.info("Creating DB...")
        conn.executescript(query)

        ### Inserting the home page

        conn.execute(
            "INSERT INTO PAGE(URI, TITLE, CONTENT, DATE_CREATED, LAST_EDITED) VALUES (?, ?, ?, ?, ?)",
            (
                'home',
                'Home',
                bytes('title: Home\ntags: \n\n**TEST WIKI, PLEASE IGNORE**', config.TEXT_ENCODING),
                datetime.now(),
                datetime.now()
            )
        )




    log.info("Db created.")


if __name__ == "__main__":
    if not exists(db_file_path()):
        setup()




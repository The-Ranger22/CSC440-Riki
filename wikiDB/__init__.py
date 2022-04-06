from sqlite3 import connect, Connection
from os import getcwd
from os.path import exists


db_name = 'wiki'
file_ext = ".db"

def db_file_path():
    return getcwd() + "/" + db_name + file_ext

def setup():
    loc = __path__[0]
    print("Beginning setup process...")
    with open(f"{loc}/SQL/create_db.sql", "r") as file:
        query = file.read()
    with connect(db_name + file_ext) as conn:
        if not isinstance(conn, Connection):
            raise TypeError
        print("Creating DB...")
        conn.executescript(query)


if __name__ == "__main__":
    if not exists(db_file_path()):
        setup()




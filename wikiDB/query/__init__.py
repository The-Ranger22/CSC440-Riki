
# region Imports
import wikiDB
from sqlite3 import connect
from sqlite3 import DatabaseError
import user
# endregion

def _query(query_func):
    def query_wrap(args=None):
        result = -1
        try:
            conn = connect(wikiDB.db_file)
            cursor = conn.cursor()
            if args is None:
                cursor.execute(query_func())
            else:
                cursor.execute(query_func(*args))
            result = cursor.fetchall()
            conn.commit()
            conn.close()
        except Exception:
            raise DatabaseError
        return result
    return query_wrap

class Tables:
    USER = "USER"
    PAGE = "PAGE"
    CATEGORY = "CATEGORY"
    TAG = "TAG"


def query_db(method):
    def query_wrapper(*args):
        return f"[{method(*args)}]"
    return query_wrapper

class User:
    _clauses = []

    @staticmethod
    def insert(username, password, email, active, auth):
        return user.insert(username, password, email, active, auth)

    @staticmethod
    def update(uid=None, username=None, password=None, email=None, active=None, auth=None):
        pass

    @staticmethod
    def delete(uid=None, username=None, password=None, email=None, active=None, auth=None):
        pass

    @classmethod
    def select(cls, uid=None, username=None, password=None, email=None, active=None, auth=None):

        cls._clauses.append("<SELECT CLAUSE>")
        return cls

    @classmethod
    def where(cls, uid=None, username=None, password=None, email=None, active=None, auth=None):
        cls._clauses.append("<WHERE CLAUSE>")
        return cls

    @classmethod
    def group_by(cls, uid=None, username=None, password=None, email=None, active=None, auth=None):
        cls._clauses.append("<GROUP BY CLAUSE>")
        return cls

    @classmethod
    @query_db
    def exec(cls):
        query = "".join(cls._clauses)
        cls._clauses.clear()
        return query


class Page:
    pass

class Category:
    pass

class Tag:
    pass


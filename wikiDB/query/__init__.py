
# region Imports
import logging

import wikiDB
from sqlite3 import connect
from sqlite3 import DatabaseError
from abc import ABC, abstractmethod
# endregion
log = logging.getLogger('database')

def _query(method):
    """
    A decorator responsible for connecting to a SQLite database and return the query result (if any).
    @param method: the query method to be decorated
    @return: the query wrapper responsible for connecting to the database
    """
    def query_wrap(ref):
        """

        @param ref:
        @return:
        """
        result = -1
        try:
            conn = connect(wikiDB.db_file_path())
            cursor = conn.cursor()

            query_format, arguments = method(ref)

            log.debug(f'Attempting query: {query_format}')
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(query_format, arguments)  # TODO: Start enforcing the relational constrains of foreign keys
            result = cursor.fetchall()
            conn.commit()
            conn.close()

            return result
        except Exception:
            raise DatabaseError
    return query_wrap

def _kwargs_sq_processor(kwargs):
    if not isinstance(kwargs, dict):
        raise TypeError

    for k in kwargs.keys():
        if isinstance(kwargs[k], str):
            kwargs[k] = f'\'{kwargs[k]}\''
        else:
            kwargs[k] = f'{kwargs[k]}'

    return kwargs

class AbstractTable(ABC):
    class Query:
        """

        """

        @property
        def query_types(self):
            return ["INSERT", "SELECT", "UPDATE", "DELETE"]

        def __init__(self, table, query_type, *args, **kwargs):
            # ensuring type correctness
            if not isinstance(query_type, str):
                raise TypeError
            if not isinstance(table, str):
                raise TypeError

            query_type = query_type.upper()
            # kwargs = _kwargs_sq_processor(kwargs)  # Applying single quotes to all values of type str


            if query_type not in self.query_types:
                log.error()
                raise ValueError("argument <query_type> must be an element of ['INSERT','SELECT','UPDATE','DELETE']")

            self._clauses = []
            self._args = []
            query_cmd = ""
            if query_type == "INSERT":
                if len(kwargs) == 0:
                    log.debug("'No fields for the INSERT statement were provided'")
                    raise ValueError
                seperator = ", "
                # query_cmd = f"INSERT INTO {table} ({seperator.join(kwargs.keys())}) VALUES ({seperator.join(kwargs.values())})"
                query_cmd = f"INSERT INTO {table} ({seperator.join(kwargs.keys())}) VALUES ({seperator.join(['?' for x in range(len(kwargs.values()))])})"
                self._args = list(kwargs.values())
            elif query_type == "SELECT":
                if len(args) == 0:
                    query_cmd = f"SELECT * FROM {table}"
                else:
                    query_cmd = f"SELECT {', '.join(args)} FROM {table}"
            elif query_type == "UPDATE":
                query_cmd = f"UPDATE {table} SET {', '.join([f'{key}={value}' for key, value in kwargs.items()])}"
            elif query_type == "DELETE":
                query_cmd = f"DELETE FROM {table}"

            self._clauses.append(query_cmd)

        def where(self, **kwargs):
            if len(kwargs) == 0:
                log.debug("'No conditions for the WHERE statement were provided'")
                raise ValueError("No conditions for the WHERE statement were provided")
            separator = " AND "
            kwargs = _kwargs_sq_processor(kwargs)
            self._clauses.append(f"WHERE {separator.join([f'{key}={value}' for key, value in kwargs.items()])}")
            return self

        def group_by(self, *cols):
            separator = ", "
            self._clauses.append(f"GROUP BY {separator.join(cols)}")
            return self

        @_query
        def exec(self):
            log.debug(self._clauses)
            log.debug(self._args)
            return (f"{' '.join(self._clauses)};", self._args)

    @classmethod
    @abstractmethod
    def name(cls):
        pass

    @classmethod
    @abstractmethod
    def fields(cls):
        pass

    @classmethod
    @abstractmethod
    def select(cls, *args):
        pass

    @classmethod
    @abstractmethod
    def insert(cls, *args):
        pass

    @classmethod
    @abstractmethod
    def update(cls, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def delete(cls):
        pass

# region User Table
class UserTable(AbstractTable):

    @classmethod
    def name(cls):
        return "USER"

    @classmethod
    def fields(cls):
        return ["ID", "USERNAME", "PASSWORD", "EMAIL", "AUTHENTICATED", "ACTIVE"]

    @classmethod
    def select(cls, ID=False, username=False, password=False, email=False, authenticated=False, active=False):
        args = []
        if ID:
            args.append("ID")
        if username:
            args.append("USERNAME")
        if password:
            args.append("PASSWORD")
        if email:
            args.append("EMAIL")
        if authenticated:
            args.append("AUTHENTICATED")
        if active:
            args.append("ACTIVE")
        return cls.Query(cls.name(), "SELECT", *args)

    @classmethod
    def insert(cls, username, password, email, authenticated=False, active=False):

        if username is None or password is None or email is None:
            raise ValueError
        return cls.Query(cls.name(), "INSERT",
                         username=username,
                         password=password,
                         email=email,
                         authenticated=authenticated,
                         active=active
                         )

    @classmethod
    def update(cls, **kwargs):
        return cls.Query(cls.name(), "UPDATE", **kwargs)

    @classmethod
    def delete(cls):
        return cls.Query(cls.name(), "DELETE")
# endregion

# region Page Table
class PageTable(AbstractTable):

    @classmethod
    def name(cls):
        return "PAGE"

    @classmethod
    def fields(cls):
        return ["ID", "URI", "TITLE", "CONTENT", "DATE_CREATED", "LAST_EDITED"]

    @classmethod
    def select(cls, ID=False, URI=False, title=False, content=False, date_created=False, last_edited=False):
        args = []
        if ID:
            args.append("ID")
        if URI:
            args.append("URI")
        if title:
            args.append("TITLE")
        if content:
            args.append("CONTENT")
        if date_created:
            args.append("DATE_CREATED")
        if last_edited:
            args.append("LAST_EDITED")
        return cls.Query(cls.name(), "SELECT", *args)

    @classmethod
    def insert(cls, URI, title, content, date_created, last_edited):
        return cls.Query(cls.name(), "INSERT",
                         URI=URI,
                         title=title,
                         content=content,
                         date_created=date_created,
                         last_edited=last_edited)

    @classmethod
    def update(cls, **kwargs):
        return cls.Query(cls.name(), "UPDATE", **kwargs)

    @classmethod
    def delete(cls):
        return cls.Query(cls.name(), "DELETE")
# endregion

# region Tag Table
class TagTable(AbstractTable):

    @classmethod
    def name(cls):
        return "TAG"

    @classmethod
    def fields(cls):
        return ["NAME", "CATEGORY_ID"]

    @classmethod
    def select(cls, ID=False, name=False, category_id=False):
        args = []
        if ID:
            args.append("ID")
        if name:
            args.append("NAME")
        if category_id:
            args.append("CATEGORY_ID")
        return cls.Query(cls.name(), "SELECT", *args)

    @classmethod
    def insert(cls, name, category_id):
        return cls.Query(cls.name(), "INSERT", name=name, category_id=category_id)

    @classmethod
    def update(cls, name=None, category_id=None):
        if name is None:
            raise TypeError("parameter <name> cannot be None!")
        if category_id is None:
            raise TypeError("parameter <category_id> cannot be None!")
        if not isinstance(name, str):
            raise TypeError("parameter <name> must be a string!")
        if not isinstance(category_id, int):
            raise TypeError("parameter <category_id> must be an int!")
        if name == "":
            raise ValueError("A string of a length greater than 0 must be provided")
        if category_id < 0:
            raise ValueError("A non-negative integer must be provided to <category_id>!")

        return cls.Query(cls.name(), "UPDATE", name, category_id)

    @classmethod
    def delete(cls):
        return cls.Query(cls.name(), "DELETE")
# endregion

# region Category Table
class CategoryTable(AbstractTable):

    @classmethod
    def name(cls):
        return "CATEGORY"

    @classmethod
    def fields(cls):
        return []

    @classmethod
    def select(cls, ID=False, name=False):
        args = []
        if ID:
            args.append("ID")
        if name:
            args.append("NAME")
        return cls.Query(cls.name(), "SELECT", *args)

    @classmethod
    def insert(cls, name):
        return cls.Query(cls.name(), "INSERT", name=name)

    @classmethod
    def update(cls, name=None):
        if name is None:
            raise TypeError("parameter <name> cannot be None!")
        if not isinstance(name, str):
            raise TypeError("parameter <name> must be a string!")
        if name == "":
            raise ValueError("A string of a length greater than 0 must be provided")
        return cls.Query(cls.name(), "UPDATE", name)

    @classmethod
    def delete(cls):
        return cls.Query(cls.name(), "DELETE")
# endregion


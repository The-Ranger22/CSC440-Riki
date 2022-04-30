"""
    User classes & helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import json
import binascii
import hashlib
from functools import wraps

from flask import current_app
from flask_login import current_user

from wikiDB.tables import UserTable


class UserManager(object):
    """A very simple user Manager, that saves it's data as json."""

    def __init__(self):
        pass


    @staticmethod
    def _form_userdata_from_query(password, auth):
        return {
                    'active': True,
                    'authentication_method': 'cleartext',
                    'password': password,
                    'authenticated': auth,
                    'roles': []
                }

    def read(self):
        # with open(self.file) as f:
        #     data = json.loads(f.read())

        raw_query_data = UserTable.select().exec()
        data = {}

        # Convert tables data to the expected dictionary format
        for uid, username, password, email, authenticated, active in raw_query_data:
            data[username] = {
                'active': active,
                'authentication_method': 'cleartext',
                'password': password,
                'authenticated': authenticated,
                'roles': []
            }

        return data

    def write(self, data):
        pass
        # with open(self.file, 'w') as f:
        #     f.write(json.dumps(data, indent=2))

    def add_user(self, name, password,
                 active=True, roles=[], authentication_method=None):

        if len(UserTable.select().where(username=name)) > 0:
            return False
        if authentication_method is None:
            authentication_method = get_default_authentication_method()

        # new_user = {
        #     'active': active,
        #     'roles': roles,
        #     'authentication_method': authentication_method,
        #     'authenticated': False
        # }
        # Currently we have only two authentication_methods: cleartext and
        # hash. If we get more authentication_methods, we will need to go to a
        # strategy object pattern that operates on User.data.
        # if authentication_method == 'hash':
        #     new_user['hash'] = make_salted_hash(password)
        # elif authentication_method == 'cleartext':
        #     new_user['password'] = password
        # else:
        #     raise NotImplementedError(authentication_method)
        # self.write(users)

        UserTable.insert(name, password, "mail@mail.com", True, True)
        return User(self, name, self._form_userdata_from_query(password, True))

    def get_user(self, name):

        # users = self.read()

        userdata = (UserTable.select().where("", username=name).exec())
        if len(userdata) == 0:
            return False
        userdata = userdata[0]


        return User(self, name, self._form_userdata_from_query(userdata[2], userdata[4]))

    def delete_user(self, name):
        raise NotImplementedError()
        # users = self.read()
        # if not users.pop(name, False):
        #     return False
        # self.write(users)
        # return True

    def update(self, name, userdata):
        data = self.read()
        data[name] = userdata
        self.write(data)


class User(object):
    def __init__(self, manager, name, data):
        self.manager = manager
        self.name = name
        self.data = data

    def get(self, option):
        return self.data.get(option)

    def set(self, option, value):
        self.data[option] = value
        self.save()

    def save(self):
        self.manager.update(self.name, self.data)

    def is_authenticated(self):
        return self.data.get('authenticated')

    def is_active(self):
        return self.data.get('active')

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.name

    def check_password(self, password):
        """Return True, return False, or raise NotImplementedError if the
        authentication_method is missing or unknown."""
        authentication_method = self.data.get('authentication_method', None)
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        # See comment in UserManager.add_user about authentication_method.
        if authentication_method == 'hash':
            result = check_hashed_password(password, self.get('hash'))
        elif authentication_method == 'cleartext':
            result = (self.get('password') == password)
        else:
            raise NotImplementedError(authentication_method)
        return result


def get_default_authentication_method():
    return current_app.config.get('DEFAULT_AUTHENTICATION_METHOD', 'cleartext')


def make_salted_hash(password, salt=None):
    if not salt:
        salt = os.urandom(64)
    d = hashlib.sha512()
    d.update(salt[:32])
    d.update(password)
    d.update(salt[32:])
    return binascii.hexlify(salt) + d.hexdigest()


def check_hashed_password(password, salted_hash):
    salt = binascii.unhexlify(salted_hash[:128])
    return make_salted_hash(password, salt) == salted_hash


def protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_app.config.get('PRIVATE') and not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        return f(*args, **kwargs)

    return wrapper

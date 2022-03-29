from wikiDB.query import _query



@_query
def _insert(username, password, email, active, auth):
    return f'''
    INSERT INTO USER (USERNAME, PASSWORD, EMAIL, AUTHENTICATED, ACTIVE) 
    VALUES ('{username}', '{password}', '{email}', '{auth}', '{active}')
    '''

def insert(username, password, email, auth, active):
    _insert((username, password, email, auth, active))

@_query
def _select(uid=None, password=None, email=None, auth=None, active=None, where=None):
    return f'''
    SELECT * FROM USER;
    '''

@_query
def _update():
    pass

@_query
def _delete():
    pass

"""
    Forms
    ~~~~~
"""
import logging

from flask_wtf import Form
from wtforms import BooleanField
from wtforms import TextField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms import SelectField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError

from wiki.core import clean_url
from wiki.web import current_wiki
from wiki.web import current_users
log = logging.getLogger('wiki')

class URLForm(Form):
    url = TextField('', [InputRequired()])

    def validate_url(form, field):
        if current_wiki.exists(field.data):
            error_msg = f'The URL \'{field.data}\' exists already.'
            log.debug(error_msg)
            raise ValidationError(error_msg)

    def clean_url(self, url):
        return clean_url(url)


class SearchForm(Form):
    term = TextField('', [InputRequired()])
    ignore_case = BooleanField(
        description='Ignore Case',
        # FIXME: default is not correctly populated
        default=True)
    option = SelectField("Sort By", choices=[("default", "Relevance"), ("CDO", "Creation Date: Oldest"),
                                             ("CDN", "Creation Date: Newest"), ("EDO", "Last Edited Date: Oldest"),
                                             ("EDN", "Last Edited Date: Newest")], render_kw={'style': 'width: 15ch'},)



class EditorForm(Form):
    title = TextField('', [InputRequired()])
    body = TextAreaField('', [InputRequired()])
    tags = TextField('')


class LoginForm(Form):
    name = TextField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])

    def validate_name(form, field):
        user = current_users.get_user(field.data.strip())

        if not user:
            log.debug(f'Cannot find username: \'{field.data}\'')
            raise ValidationError('This username does not exist.')
        else:
            log.debug(f'Validated user: \'{user.get_id()}\'')


    def validate_password(form, field):
        user = current_users.get_user(form.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            log.debug(f'Username and password do not match. User: \'{user.get_id()}\'')
            raise ValidationError('Username and password do not match.')
        else:
            log.info(f'User \'{user.get_id()}\' has logged on.')

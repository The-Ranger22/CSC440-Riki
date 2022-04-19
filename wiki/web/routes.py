"""
    Routes
    ~~~~~~
"""
import logging

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from wiki.core import Processor
from wiki.web.forms import EditorForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect
from wikiDB.DatabaseModel import Page
import re

log = logging.getLogger('wiki')
bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        log.info(f'Successfully saved page \'{page.title}\'')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    log.info(f'Page \'{page.title}\' was successfully deleted')
    return redirect(url_for('wiki.home'))


# Replaced by categories page
@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/categories/')
@protect
def categories():
    tags = current_wiki.get_tags()
    pages = current_wiki.index()
    return render_template('categories.html', pages=pages, tags=tags)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    """
    Defines a route to display the search page or the search
    page with its results based on the search terms given by the user.
    @return: Render template for search page
    """
    form = SearchForm()
    if form.validate_on_submit():
        searchText = form.term.data
        log.debug(f'Raw search text: \'{searchText}\'')
        caseInsensitive = form.ignore_case.data
        option = form.option.data

        results = query_for_regex(option, searchText, caseInsensitive)
        if not caseInsensitive:
            if not results:
                term = format_term(searchText)
                words = term[1:-1].split('%')
                idList = []
                searchTerm = term.encode()
                log.debug(f'Processed search text: \'{searchTerm}\'')
                results = Page.query.filter(Page.content.like(searchTerm) | Page.title.like(searchTerm)).all()
                for result in results:
                    if all((word.encode() in result.content for word in words) or (word.encode() in result.title
                           for word in words)):
                        idList.append(result.id)
                if option == "default":
                    results = Page.query.filter(Page.id.in_(idList)).all()
                elif option == "CDO":
                    results = Page.query.filter(Page.id.in_(idList)).order_by(Page.date_created).all()
                elif option == "CDN":
                    results = Page.query.filter(Page.id.in_(idList)).order_by(Page.date_created.desc()).all()
                elif option == "EDO":
                    results = Page.query.filter(Page.id.in_(idList)).order_by(Page.last_edited).all()
                elif option == "EDN":
                    results = Page.query.filter(Page.id.in_(idList)).order_by(Page.last_edited.desc()).all()
        else:
            if not results:
                term = format_term(searchText)
                searchTerm = term.encode()
                log.debug(f'Processed search text: \'{searchTerm}\'')
                results = query_for_search(option, searchTerm)

        return render_template('search.html', form=form, results=results, search=form.term.data,
                               case=form.ignore_case.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data.strip())
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


@bp.route('/user/')
def user_index():
    pass


@bp.route('/user/create/')
def user_create():
    pass


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


def query_for_search(option, search_term):
    """
    PYDOC
    Returns articles that match the term or terms that was given by the user.
    @param option: sort by option for articles
    @param search_term: term or terms given by the user to search
    @return: a list of all the articles that matches the term or terms given
    """
    log.info(f'Searching for pages with criteria: \'{search_term}\', option: \'{option}\'')

    results = None
    if option == "default":
        results = Page.query.filter(Page.content.like(search_term) | Page.title.like(search_term)).all()
    elif option == "CDO":
        results = Page.query.filter(Page.content.like(search_term) | Page.title.like(search_term)) \
            .order_by(Page.date_created).all()
    elif option == "CDN":
        results = Page.query.filter(Page.content.like(search_term) | Page.title.like(search_term)) \
            .order_by(Page.date_created.desc()).all()
    elif option == "EDO":
        results = Page.query.filter(Page.content.like(search_term) | Page.title.like(search_term)) \
            .order_by(Page.last_edited).all()
    elif option == "EDN":
        results = Page.query.filter(Page.content.like(search_term) | Page.title.like(search_term)) \
            .order_by(Page.last_edited.desc()).all()
    return results


def query_for_regex(option, search_term, case_insensitive):
    """
    Returns articles that match the regex that was given by the user.
    @param option: sort by option for articles
    @param search_term: regex given by the user to search
    @param case_insensitive: a boolean that determines if the search is case-sensitive or not
    @return: a list of all the articles that matches the regex given
    """
    log.info(f'Searching for pages with criteria: \'{search_term}\', option: \'{option}\'')

    regexIdList = []
    queryResults = Page.query.all()
    results = None
    if not case_insensitive:
        for result in queryResults:
            content = str(result.content)
            title = str(result.title)
            if re.search(search_term, content) or re.search(search_term, title):
                regexIdList.append(result.id)
    else:
        for result in queryResults:
            content = str(result.content)
            title = str(result.title)
            if re.search(search_term, content, re.IGNORECASE) or re.search(search_term, title, re.IGNORECASE):
                regexIdList.append(result.id)
    if option == "default":
        results = Page.query.filter(Page.id.in_(regexIdList)).all()
    elif option == "CDO":
        results = Page.query.filter(Page.id.in_(regexIdList)).order_by(Page.date_created).all()
    elif option == "CDN":
        results = Page.query.filter(Page.id.in_(regexIdList)).order_by(Page.date_created.desc()).all()
    elif option == "EDO":
        results = Page.query.filter(Page.id.in_(regexIdList)).order_by(Page.last_edited).all()
    elif option == "EDN":
        results = Page.query.filter(Page.id.in_(regexIdList)).order_by(Page.last_edited.desc()).all()
    return results


def format_term(searchText):
    """
    Returns formatted search term(s)
    @param searchText: user's raw search text
    @return: formatted search term(s)
    """
    term = "%"
    if searchText[0] == "\"" and searchText[len(searchText) - 1] == "\"":
        searchText = searchText[1:-1]
        term = "%{}%".format(searchText)
    else:
        terms = searchText.split()
        for t in terms:
            term = term + t + '%'
    return term

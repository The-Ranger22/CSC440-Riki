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
import doctest

doctest.testmod()
log = logging.getLogger('wiki')
bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get_from_DB('home')
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
    page = current_wiki.get_from_DB(url)
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
        page.load(form)
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
    if(url=='home'):
        flash('Can\'t move the home page!')
        return display('home')
    page = current_wiki.get_from_DB(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        log.info(f'Moving page \'{url}\' to \'{newurl}\'')
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_from_DB(url)
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
    page = current_wiki.index()
    pages = []
    for item in page:
        pageTags = (item.tags).split(',')
        if item.tags == '':
            pages.append([[item.title,item.url],"Uncategorized"])
        else:
            pages.append([[item.title,item.url],[pageTags]])
    #   BACKUP IN CASE DATABASE SWITCH MESSES WITH FUNCTIONS ABOVE
    #   POSSIBLY PASS [[[PAGE.NAME,PAGE.URL],CATEGORY],[PAGE,CATEGORY]] LIST CREATED BEFORE PASSING TO HTML
    #   IF QUERIES CAN'T BE DONE IN HTML
    #   tags = TagTable.select(name=True).exec()
    #   pages = PageTable.select(title=True).exec()
    #   relations = [tagid,pageid]
    #   for (tag in tags){
    #       print(tag.name)
    #       for (relationship in relationships){
    #           if tag.id = relationship[0]{
    #               page = PageTable.tables(PageID = relationship[1])
    #               <a href=(page.url)>page.name</a>
    #           }
    #       }
    #   }
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
                results = iterate_id_list(option, idList)
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
        log.info(f'User \'{form.name.data}\' has logged on')
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    log.info(f'User has logged out')
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
    Returns pages that match the term or terms that was given by the user.
    @param option: sort by option for pages
    @param search_term: term or terms given by the user to search
    @return: a list of all the pages that matches the term or terms given
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
    special_characters = "\"!@#\\$%^&*()-+?_=,<>/\""
    if not case_insensitive:
        for result in queryResults:
            content = result.content.decode()
            title = result.title
            if not content[0].isalnum() and not content[0] in special_characters:
                content = content[1:-1]
            if re.search(search_term, content) or re.search(search_term, title):
                regexIdList.append(result.id)
    else:
        for result in queryResults:
            content = result.content.decode()
            title = result.title
            if not content[0].isalnum() and not content[0] in special_characters:
                content = content[1:-1]
            if re.search(search_term, content, re.IGNORECASE) or re.search(search_term, title, re.IGNORECASE):
                regexIdList.append(result.id)

    results = iterate_id_list(option, regexIdList)
    return results


def format_term(searchText):
    """
    Returns formatted search term(s)
    @param searchText: user's raw search text
    @return: formatted search term(s)
    """
    term = "%"
    pattern = '"(.*?)"'  # terms in double quote
    if re.search(pattern, searchText):
        terms = re.findall(pattern, searchText)
        for t in terms:
            term = term + t + '%'
    else:
        terms = searchText.split()
        for t in terms:
            term = term + t + '%'
    return term


def iterate_id_list(option, id_list):
    """
    Returns the query results using the given id list and sort by option
    @param option: sorting of the Pages
    @param id_list: list of Pages' ids that need to be gotten
    @return: query results
    """
    if option == "default":
        results = Page.query.filter(Page.id.in_(id_list)).all()
    elif option == "CDO":
        results = Page.query.filter(Page.id.in_(id_list)).order_by(Page.date_created).all()
    elif option == "CDN":
        results = Page.query.filter(Page.id.in_(id_list)).order_by(Page.date_created.desc()).all()
    elif option == "EDO":
        results = Page.query.filter(Page.id.in_(id_list)).order_by(Page.last_edited).all()
    elif option == "EDN":
        results = Page.query.filter(Page.id.in_(id_list)).order_by(Page.last_edited.desc()).all()
    return results

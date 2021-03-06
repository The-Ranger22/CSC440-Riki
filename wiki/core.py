"""
    Wiki core
    ~~~~~~~~~

    Responsible for presenting information to the user

"""
import json
import logging
from collections import OrderedDict
from io import open
import os
import re

from flask import abort
from flask import url_for
import markdown
import datetime

import config
from wikiDB.tables import PageTable
log_wiki = logging.getLogger('wiki')
log_db = logging.getLogger('database')

def clean_url(url):
    """
        Cleans the url and corrects various errors. Removes multiple
        spaces and all leading and trailing spaces. Changes spaces
        to underscores and makes all characters lowercase. Also
        takes care of Windows style folders use.

        :param str url: the url to clean


        :returns: the cleaned url
        :rtype: str
    """
    log_wiki.debug(f'Dirty url: \'{url}\'')
    url = re.sub('[ ]{2,}', ' ', url).strip()
    url = url.lower().replace(' ', '_')
    url = url.replace('\\\\', '/').replace('\\', '/')
    log_wiki.debug(f'Clean url: \'{url}\'')
    return url


def wikilink(text, url_formatter=None):
    """
        Processes Wikilink syntax "[[Link]]" within the html body.
        This is intended to be run after content has been processed
        by markdown and is already HTML.

        :param str text: the html to highlight wiki links in.
        :param function url_formatter: which URL formatter to use,
            will by default use the flask url formatter

        Syntax:
            This accepts Wikilink syntax in the form of [[WikiLink]] or
            [[url/location|LinkName]]. Everything is referenced from the
            base location "/", therefore sub-pages need to use the
            [[page/subpage|Subpage]].

        :returns: the processed html
        :rtype: str
    """
    log_wiki.debug(f'Preformatted wiki-link: \'{text}\'')
    if url_formatter is None:
        url_formatter = url_for
    link_regex = re.compile(
        r"((?<!\<code\>)\[\[([^<].+?) \s*([|] \s* (.+?) \s*)?]])",
        re.X | re.U
    )
    for i in link_regex.findall(text):
        title = [i[-1] if i[-1] else i[1]][0]
        url = clean_url(i[1])
        html_url = "<a href='{0}'>{1}</a>".format(
            url_formatter('wiki.display', url=url),
            title
        )
        text = re.sub(link_regex, html_url, text, count=1)

    log_wiki.debug(f'Formatted wiki-link: \'{text}\'')
    return text


class Processor(object):
    """
        The processor handles the processing of file content into
        metadata and markdown and takes care of the rendering.

        It also offers some helper methods that can be used for various
        cases.
    """

    preprocessors = []
    postprocessors = [wikilink]

    def __init__(self, text):
        """
            Initialization of the processor.

            :param str text: the text to process
        """


        self.md = markdown.Markdown([
            'codehilite',
            'fenced_code',
            'meta',
            'tables'
        ])
        self.input = text
        self.markdown = None
        self.meta_raw = None

        self.pre = None
        self.html = None
        self.final = None
        self.meta = None

    def process_pre(self):
        """
            Content preprocessor.
        """
        current = self.input
        for processor in self.preprocessors:
            current = processor(current)
        self.pre = current

    def process_markdown(self):
        """
            Convert to HTML.
        """
        self.html = self.md.convert(self.pre)


    def split_raw(self):
        """
            Split text into raw meta and content.
        """
        self.meta_raw, self.markdown = self.pre.split('\n\n', 1)

    def process_meta(self):
        """
            Get metadata.

            .. warning:: Can only be called after :meth:`html` was
                called.
        """
        # the markdown meta plugin does not retain the order of the
        # entries, so we have to loop over the meta values a second
        # time to put them into a dictionary in the correct order
        self.meta = OrderedDict()
        for line in self.meta_raw.split('\n'):
            key = line.split(':', 1)[0]
            # markdown metadata always returns a list of lines, we will
            # reverse that here
            self.meta[key.lower()] = \
                '\n'.join(self.md.Meta[key.lower()])

    def process_post(self):
        """
            Content postprocessor.
        """
        current = self.html
        for processor in self.postprocessors:
            current = processor(current)
        self.final = current

    def process(self):
        """
            Runs the full suite of processing on the given text, all
            pre and post processing, markdown rendering and meta data
            handling.
        """
        self.process_pre()
        self.process_markdown()
        self.split_raw()
        self.process_meta()
        self.process_post()

        return self.final, self.markdown, self.meta


class Page(object):

    def __init__(self, id, url, title, content, date_created, last_edited, new=False):
        self.id = id
        self.url = url
        self.notTheOtherTitle = title
        self.content = content if not isinstance(content, bytes) else content.decode("UTF-8")
        self.date_created = date_created
        self.last_edited = last_edited
        self._meta = OrderedDict()
        if not new:
            self.render()

    def __repr__(self):
        return "<Page: {}@{}>".format(self.url, self.path)

    def load(self, form):

        self['title'] = form.title.data
        self['body'] = form.body.data
        self['tags'] = form.tags.data


        self.content = f"title: {self['title']}\ntags: {self['tags']}\n\n{self['body']}"




    def render(self):
        processor = Processor(self.content)
        self._html, self.body, self._meta = processor.process()

    def save(self, update=True):
        """
        First checks if a page already exists in the DB, and if so, updates that page.
        Otherwise creates a new page entry with this object.
        @param update: True if the page should be rendered upon completion of the save.
        @return:
        """
        now = datetime.datetime.now()
        lines = []
        for key, value in list(self._meta.items()):
            line = '%s: %s\n' % (key, value)
            lines.append(line)
            log_wiki.debug(f'line: \'{line}\'')


        #PageTable.insert(self.url, self.title, bytes(self.content, "UTF-8"), now, now).exec()

        if len(PageTable.select(URI=True).where(separator="OR", URI=self.url).exec()) != 0:
            PageTable\
                .update(title=self.title, content=bytes(self.content, config.TEXT_ENCODING), last_edited=now)\
                .where(separator="OR", URI=self.url)\
                .exec()
        else:
            PageTable.insert(self.url, self.title, bytes(self.content, config.TEXT_ENCODING), now, now).exec()

        if update:
            self.render()

    @property
    def meta(self):
        return self._meta

    def __getitem__(self, name):
        return self._meta[name]

    def __setitem__(self, name, value):
        self._meta[name] = value

    @property
    def html(self):
        return self._html

    def __html__(self):
        return self.html

    @property
    def title(self):
        try:
            return self['title']
        except KeyError:
            return self.url

    @title.setter
    def title(self, value):
        self['title'] = value

    @property
    def tags(self):
        try:
            return self['tags']
        except KeyError:
            return ""

    @tags.setter
    def tags(self, value):
        self['tags'] = value


class Wiki(object):
    def __init__(self, root):
        self.root = root

    def get_from_DB(self, url):
        """
        Gets a page from the database based on url
        @param url: The url of the page
        @return: A Page object
        """
        result_list = PageTable.select().where("OR", URI=url).exec()
        if len(result_list) == 0:
            log_db.error(f'Unable to find page with url/title: \'{url}\'')
            abort(404)
        elif len(result_list) > 1:
            log_db.error(f'Result set > 1 when querying PAGE with url: \'{url}\'')
            abort(500, 'Internal Server Error')
        else:
            result = result_list[0]
            id = result[0]
            uri = result[1]
            title = result[2]
            content = result[3]
            date_created = result[4]
            last_edited = result[5]
            return Page(id, uri, title, content, date_created, last_edited)

    def path(self, url):
        return os.path.join(self.root, url + '.md')

    def exists(self, url):
        """
        Checks whether or not a page exists by url
        @param url: The url of the page in question
        @return: True if the page exists in the DB
        """
        result_list = PageTable.select().where('OR',URI=url,title=url).exec()
        return len(result_list) > 0


    def get(self, url):
        path = self.path(url)
        log_wiki.debug(f"Attempting to get page at {url}")
        #path = os.path.join(self.root, url + '.md')
        if self.exists(url):
            returned_tup = PageTable.select().where(separator='', URI=url).exec()[0]
            return Page(
                returned_tup[0],  # id
                returned_tup[1],  # URI
                returned_tup[2],  # TITLE
                returned_tup[3],  # CONTENT
                returned_tup[4],  # DATE CREATED
                returned_tup[5]   # LAST EDITED
            )
        return None

    def get_bare(self, url):
        """
        Returns a 'blank' page object.
        @param url: The url of the blank page object to be constructed.
        @return: A page object
        """
        if self.exists(url):
            return False
        id = len(PageTable.select().exec()) + 1
        log_wiki.info(f'created page with ID= \'{id}\'')
        page = Page(id, url, "", "", "", "", new=True)
        return page

    def move(self, url, newurl):
        """
        Updates the uri of the page in the database to newurl, provided newurl does not exist.
        @param url: The url of the page to be moved
        @param newurl: the destination url
        @return:
        """
        if (PageTable.select().where("", URI=newurl).exec()):
            msg = f'Cannot move page to url \'{newurl}\' as it already exists'
            log_wiki.error(msg)
            raise ValueError(msg)
        else:
            log_wiki.info(f'Moved page from url: \'{url}\' to url: \'{newurl}\'')
            PageTable.update(URI=newurl).where("", URI=url).exec()


    def delete(self, url):
        """
        Deletes a page from the database. Currently, no way to delete a non-existing page.
        But future may have a delete by name function
        @param url: The url to be deleted
        """
        log_wiki.info(f'Deleting page with url: \'{url}\'')
        if(PageTable.select().where("", URI=url).exec):
            PageTable.delete().where("", URI=url).exec()
            log_wiki.info('Page deleted.')
            return True
        log_wiki.info("Page did not exist.")
        return False


    def index(self):
        """
            Builds up a list of all the available pages.

            :returns: a list of all the wiki pages
            :rtype: list
        """

        pages = []
        result_list = PageTable.select().exec()
        log_wiki.debug(f'Num pages on index call: {len(result_list)}')
        for id, uri, title, content, date_created, last_edited in result_list:
            pages.append(Page(id, uri, title, content, date_created, last_edited))
        return sorted(pages, key=lambda x: x.title.lower())


    def index_by(self, key):
        """
            Get an index based on the given key.

            Will use the metadata value of the given key to group
            the existing pages.

            :param str key: the attribute to group the index on.

            :returns: Will return a dictionary where each entry holds
                a list of pages that share the given attribute.
            :rtype: dict
        """
        pages = {}
        for page in self.index():
            value = getattr(page, key)
            pre = pages.get(value, [])
            pages[value] = pre.append(page)
        return pages

    def get_by_title(self, title):
        pages = self.index(attr='title')
        return pages.get(title)

    def get_tags(self):
        pages = self.index()
        tags = {}
        for page in pages:
            pagetags = page.tags.split(',')
            for tag in pagetags:
                tag = tag.strip()
                if tag == '':
                    continue
                elif tags.get(tag):
                    tags[tag].append(page)
                else:
                    tags[tag] = [page]
        return tags

    def index_by_tag(self, tag):
        pages = self.index()
        tagged = []
        for page in pages:
            if tag in page.tags:
                tagged.append(page)
        return sorted(tagged, key=lambda x: x.title.lower())

    def search(self, term, ignore_case=True, attrs=['title', 'tags', 'body']):
        pages = self.index()
        regex = re.compile(term, re.IGNORECASE if ignore_case else 0)
        matched = []
        for page in pages:
            for attr in attrs:
                if regex.search(getattr(page, attr)):
                    matched.append(page)
                    break
        return matched

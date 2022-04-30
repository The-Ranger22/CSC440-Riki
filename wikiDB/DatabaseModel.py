from wikiDB.Abstract import AbstractBaseModel
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(AbstractBaseModel):
    """
    Database model for User table in the database
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    authenticated = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


class Page(AbstractBaseModel):
    """
    Database model for Page table in the database
    """
    id = db.Column(db.Integer, primary_key=True)
    uri = db.Column(db.Text, unique=True, nullable=False)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.BLOB, nullable=False)
    date_created = db.Column(db.Date, nullable=False)
    last_edited = db.Column(db.Date, nullable=False)

    def __init__(cls, uri, title, content, date_created, last_edited):
        cls.id = id
        cls.uri = uri
        cls.title = title
        cls.content = content
        cls.date_created = date_created
        cls.last_edited = last_edited

    def __repr__(self):
        return '<Page %r>' % self.title


class Category(AbstractBaseModel):
    """
    Database model for Category table in the database
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<Category %r>' % self.name


class Tags(AbstractBaseModel):
    """
    Database model for Tags table in the database
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), primary_key=True)

    def __repr__(self):
        return '<Tags %r>' % self.name


class PageTags(AbstractBaseModel):
    """
    Database model for Page_Tags table in the database
    """
    article_id = db.Column(db.Integer, db.ForeignKey('page.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)

    def __repr__(self):
        return '<PageTags %r>' % self.article_id

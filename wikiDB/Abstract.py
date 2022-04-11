from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AbstractBaseModel(db.Model):
    __abstract__ = True

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm
from sqlalchemy.ext.declarative import DeclarativeMeta


db: SQLAlchemy = SQLAlchemy()


class _FBase(db.Model):
    query: orm.Query


class AbstractBaseModel(_FBase, DeclarativeMeta):
    ...
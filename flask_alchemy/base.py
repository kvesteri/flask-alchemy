from inflection import underscore
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr


class Base(object):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return underscore(cls.__name__)

    id = sa.Column(sa.BigInteger, autoincrement=True, primary_key=True)

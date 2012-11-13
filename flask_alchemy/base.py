import sqlalchemy as sa


class Base(object):
    __abstract__ = True

    id = sa.Column(sa.BigInteger, autoincrement=True, primary_key=True)

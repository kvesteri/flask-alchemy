import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.alchemy import BaseQuery, Searchable, SearchQueryMixin


db = SQLAlchemy()


class PageQuery(BaseQuery, SearchQueryMixin):
    pass


class Page(db.Model, Searchable):
    query_class = PageQuery
    __searchable_columns__ = ['name', 'content']
    __tablename__ = 'page'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.Unicode(255))

    content = db.Column(db.UnicodeText)


class TestCase(object):
    def create_app(self):
        app = Flask('test')
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
            'TEST_DATABASE_URL',
            'postgres://localhost/flask_alchemy_test'
        )
        self.app = app
        self._app_context = self.app.app_context()
        self._app_context.push()

        db.init_app(app)
        return app

    def setup_method(self, method):
        #BaseTestCase.setup_method(self, method)
        self.app = self.create_app()
        db.create_all()

    def teardown_method(self, method):
        db.drop_all()

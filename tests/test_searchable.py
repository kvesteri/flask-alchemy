from tests import Page, TestCase, db
from flask.ext.alchemy import BaseQuery, Searchable, SearchQueryMixin


class TextItemQuery(BaseQuery, SearchQueryMixin):
    pass


class TextItem(db.Model, Searchable):
    __searchable_columns__ = ['name', 'content']
    __search_options__ = {
        'tablename': 'textitem',
        'search_vector_name': 'search_vector',
        'search_trigger_name': '{table}_search_update',
        'search_index_name': '{table}_search_index',
        'catalog': 'pg_catalog.english'
    }
    __tablename__ = 'textitem'
    query_class = TextItemQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.Unicode(255))

    content = db.Column(db.UnicodeText)


class Article(TextItem):
    __tablename__ = 'article'
    id = db.Column(db.Integer, db.ForeignKey(TextItem.id), primary_key=True)

    created_at = db.Column(db.DateTime)


class TestSearchableMixin(TestCase):
    def test_creates_search_index(self):
        rows = db.session.execute(
            """SELECT column_name
            FROM information_schema.columns WHERE table_name = 'page'"""
        ).fetchall()
        assert 'search_vector' in map(lambda a: a[0], rows)


class TestSearchQueryMixin(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        db.session.add(Page(name=u'index', content=u'some content'))
        db.session.add(Page(name=u'admin', content=u'admin content'))
        db.session.add(Page(name=u'home', content=u'this is the home page'))
        db.session.commit()

    def test_search_supports_term_splitting(self):
        assert Page.query.search('content').count() == 2

    def test_term_splitting_supports_multiple_spaces(self):
        assert Page.query.search('content  some').first().name == u'index'
        assert Page.query.search('content   some').first().name == u'index'
        assert Page.query.search('  ').count() == 3

    def test_search_removes_illegal_characters(self):
        assert Page.query.search(':@#').count()


class TestSearchableInheritance(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        db.session.add(Article(name=u'index', content=u'some content'))
        db.session.add(Article(name=u'admin', content=u'admin content'))
        db.session.add(Article(name=u'home', content=u'this is the home page'))
        db.session.commit()

    def test_supports_inheritance(self):
        assert Article.query.search('content').count() == 2

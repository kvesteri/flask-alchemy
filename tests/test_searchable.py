from tests import Page, TestCase, db


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
        assert Page.query.search(':@#')

from tests import TestCase, db


class TestSearchableMixin(TestCase):
    def test_creates_search_index(self):
        rows = db.session.execute(
            """SELECT column_name
            FROM information_schema.columns WHERE table_name = 'page'"""
        ).fetchall()
        assert 'search_vector' in map(lambda a: a[0], rows)

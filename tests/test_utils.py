from flask.ext.alchemy import escape_like


class TestEscapeLike(object):
    def test_escapes_wildcards(self):
        assert escape_like('_*%') == '*_***%'

from flask.ext.sqlalchemy import BaseQuery as _BaseQuery
from .search import SearchQueryMixin, Searchable
from .utils import sort_query, visible_page_numbers


__all__ = (
    SearchQueryMixin,
    Searchable,
    sort_query,
    visible_page_numbers
)


class BaseQuery(_BaseQuery):
    def paginate(self, page, per_page=20, error_out=True):
        pagination = _BaseQuery.paginate(self, page, per_page, error_out)
        return PaginationDecorator(pagination)

    def scalar_list(self):
        return [row[0] for row in self.all()]


class PaginationDecorator(object):
    def __init__(self, decorated):
        self.decorated = decorated

    def __getattr__(self, name):
        return getattr(self.decorated, name)

    def all(self):
        return self.items

    def pagination_json(self):
        return {
            'page': self.page,
            'pages': self.pages,
            'per_page': self.per_page,
            'total': self.total
        }

    def as_json_dict(self, *args, **kwargs):
        return {
            'pagination': self.pagination_json(),
            'data': [item.as_json_dict(**kwargs) for item in self.items]
        }


def escape_like(string, escape_char='*'):
    """
    Escapes the string paremeter used in SQL LIKE expressions

    :param string: a string to escape
    :param escape_char: escape character
    """
    return (
        string
        .replace(escape_char, escape_char * 2)
        .replace('%', escape_char + '%')
        .replace('_', escape_char + '_')
    )

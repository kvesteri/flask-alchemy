from flask.ext.sqlalchemy import BaseQuery as _BaseQuery
from .search import SearchQueryMixin, Searchable, safe_search_terms
from .utils import sort_query, escape_like


__all__ = (
    SearchQueryMixin,
    Searchable,
    safe_search_terms,
    sort_query,
    escape_like,
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

    def as_json(self, *args, **kwargs):
        return {
            'pagination': self.pagination_json(),
            'data': [item.as_json_dict(**kwargs) for item in self.items]
        }

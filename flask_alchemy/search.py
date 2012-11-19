import re

from sqlalchemy import event
from sqlalchemy.schema import DDL
from sqlalchemy.orm.mapper import Mapper


class SearchQueryMixin(object):
    def search_filter(self, term, tablename=None):
        if not tablename:
            tablename = self._entities[0].entity_zero.local_table.name
        return '%s.search_vector @@ to_tsquery(:term)' % tablename

    def search(self, term, tablename=None):
        """
        Search text items with full text search.

        :param term: the search term
        """

        if term:
            # remove all multiple whitespaces
            term = re.sub('\s+', ' ', term)
            # split the term into words
            words = map(lambda a: a + ':*', term.split(' '))
            return (
                self.filter(self.search_filter(term, tablename))
                .params(term=' & '.join(words))
            )
        else:
            return self


def attach_search_indexes(mapper, class_):
    if issubclass(class_, Searchable):
        class_.define_search_vector()


# attach to all mappers
event.listen(Mapper, 'instrument_class', attach_search_indexes)


class Searchable(object):
    __searchable_columns__ = []

    @classmethod
    def define_search_vector(cls):
        # We don't want sqlalchemy to know about this column so we add it
        # externally.
        table = cls.__table__
        tablename = cls.__tablename__
        event.listen(
            table,
            'after_create',
            DDL("ALTER TABLE %s ADD COLUMN search_vector tsvector" % tablename)
        )

        # This indexes the tsvector column
        event.listen(
            table,
            'after_create',
            DDL("""
            CREATE INDEX %s_search_index ON %s
            USING gin(search_vector)""" % (tablename, tablename))
        )

        # This sets up the trigger that keeps the tsvector column up to date.
        event.listen(
            table,
            'after_create',
            DDL("""CREATE TRIGGER %s_search_update
            BEFORE UPDATE OR INSERT ON %s
            FOR EACH ROW EXECUTE PROCEDURE
            tsvector_update_trigger(
                'search_vector',
                'pg_catalog.english',
                %s
            )""" % (
            tablename,
            tablename,
            ', '.join(map(lambda a: '%s' % a, cls.__searchable_columns__))
        )))

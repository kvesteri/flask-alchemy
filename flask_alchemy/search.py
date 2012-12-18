import re

from sqlalchemy import event
from sqlalchemy.schema import DDL
from sqlalchemy.orm.mapper import Mapper


def safe_search_terms(query):
    # Remove all illegal characters from the search query.
    query = re.sub(r'[\W\s]+', ' ', query).strip()
    if not query:
        return []

    # Split the search query into terms.
    terms = query.split(' ')

    # Search for words starting with the given search terms.
    return map(lambda a: a + ':*', terms)


class SearchQueryMixin(object):
    def search_filter(self, term, tablename=None):
        if not tablename:
            mapper = self._entities[0].entity_zero
            entity = mapper.class_
            if entity.__search_options__['tablename']:
                tablename = entity.__search_options__['tablename']
            else:
                tablename = entity._inspect_searchable_tablename()
        return '%s.search_vector @@ to_tsquery(:term)' % tablename

    def search(self, search_query, tablename=None):
        """
        Search text items with full text search.

        :param term: the search term
        """
        if not search_query:
            return self

        terms = safe_search_terms(search_query)
        if not terms:
            return self

        return (
            self.filter(self.search_filter(search_query, tablename))
            .params(term=' & '.join(terms))
        )


def attach_search_indexes(mapper, class_):
    if issubclass(class_, Searchable):
        class_.define_search_vector()


# attach to all mappers
event.listen(Mapper, 'instrument_class', attach_search_indexes)


class Searchable(object):
    __searchable_columns__ = []
    __search_options__ = {
        'tablename': None,
        'search_vector_name': 'search_vector',
        'search_trigger_name': '{table}_search_update',
        'search_index_name': '{table}_search_index',
        'catalog': 'pg_catalog.english'
    }

    @classmethod
    def _inspect_searchable_tablename(cls):
        """
        Recursive method that returns the name of the searchable table. This is
        method is needed for the inspection of tablenames in certain
        inheritance scenarios such as joined table inheritance where only
        parent is defined is searchable.
        """
        if Searchable in cls.__bases__:
            return cls.__tablename__

        for class_ in cls.__bases__:
            return class_._inspect_searchable_tablename()

    @classmethod
    def _search_vector_ddl(cls):
        """
        Returns the ddl for the search vector.
        """
        tablename = cls.__tablename__
        options = cls.__search_options__
        search_vector_name = options['search_vector_name']

        return DDL(
            """
            ALTER TABLE {table}
            ADD COLUMN {search_vector_name} tsvector
            """
            .format(
                table=tablename,
                search_vector_name=search_vector_name
            )
        )

    @classmethod
    def _search_index_ddl(cls):
        """
        Returns the ddl for creating the actual search index.
        """
        tablename = cls.__tablename__
        options = cls.__search_options__
        search_vector_name = options['search_vector_name']
        search_index_name = options['search_index_name'].format(
            table=tablename
        )
        return DDL(
            """
            CREATE INDEX {search_index_name} ON {table}
            USING gin({search_vector_name})
            """
            .format(
                table=tablename,
                search_index_name=search_index_name,
                search_vector_name=search_vector_name
            )
        )

    @classmethod
    def _search_trigger_ddl(cls):
        """
        Returns the ddl for creating an automatically updated search trigger.
        """
        tablename = cls.__tablename__
        options = cls.__search_options__
        search_vector_name = options['search_vector_name']
        search_trigger_name = options['search_trigger_name'].format(
            table=tablename
        )

        return DDL(
            """
            CREATE TRIGGER {search_trigger_name}
            BEFORE UPDATE OR INSERT ON {table}
            FOR EACH ROW EXECUTE PROCEDURE
            tsvector_update_trigger({arguments})
            """
            .format(
                search_trigger_name=search_trigger_name,
                table=tablename,
                arguments=', '.join([
                    search_vector_name,
                    "'%s'" % cls.__search_options__['catalog']] +
                    cls.__searchable_columns__
                )
            )
        )

    @classmethod
    def define_search_vector(cls):
        # In order to support joined table inheritance we need to ensure that
        # this class directly inherits Searchable
        if Searchable not in cls.__bases__:
            return

        if not cls.__searchable_columns__:
            raise Exception(
                "No searchable columns defined for model %s" % cls.__name__
            )

        # We don't want sqlalchemy to know about this column so we add it
        # externally.
        table = cls.__table__
        event.listen(
            table,
            'after_create',
            cls._search_vector_ddl()
        )

        # This indexes the tsvector column
        event.listen(
            table,
            'after_create',
            cls._search_index_ddl()
        )

        # This sets up the trigger that keeps the tsvector column up to date.
        event.listen(
            table,
            'after_create',
            cls._search_trigger_ddl()
        )

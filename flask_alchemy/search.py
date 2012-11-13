from sqlalchemy import event
from sqlalchemy.schema import DDL


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
            terms = map(lambda a: a + ':*', term.split(' '))
            return (
                self.filter(self.search_filter(term, tablename))
                .params(term=' & '.join(terms))
            )
        else:
            return self


class Searchable(object):
    def after_configured(self):
        # We don't want sqlalchemy to know about this column so we add it
        # externally.
        table = self.__class__.__table__
        event.listen(
            table,
            'after_create',
            DDL("ALTER TABLE product ADD COLUMN search_vector tsvector")
        )

        # This indexes the tsvector column
        event.listen(
            table,
            'after_create',
            DDL("""
            CREATE INDEX product_search_index ON product
            USING gin(search_vector)""")
        )

        # This sets up the trigger that keeps the tsvector column up to date.
        event.listen(
            table,
            'after_create',
            DDL("""CREATE TRIGGER product_search_update
            BEFORE UPDATE OR INSERT ON product
            FOR EACH ROW EXECUTE PROCEDURE
                tsvector_update_trigger('search_vector',
                                        'pg_catalog.english',
                                        'name',
                                        'description',
                                        'extra_information')"""))

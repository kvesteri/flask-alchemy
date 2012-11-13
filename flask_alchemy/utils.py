from flask import request
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.sql.expression import desc, asc


def sort_query(query, sort):
    """
    Applies an sql ORDER BY for given query

    :param query: query to be modified
    :param sort: string that defines the label or column to sort the query by
    """
    entities = [entity.entity_zero.class_ for entity in query._entities]
    for mapper in query._join_entities:
        if isinstance(mapper, Mapper):
            entities.append(mapper.class_)
        else:
            entities.append(mapper)

    # get all label names for queries such as:
    # db.session.query(Category, db.func.count(Article.id).label('articles'))
    labels = []
    for entity in query._entities:
        if isinstance(entity, _ColumnEntity) and entity._label_name:
            labels.append(entity._label_name)

    sort = request.args.get('sort', sort)
    if not sort:
        return query

    if sort[0] == '-':
        func = desc
        sort = sort[1:]
    else:
        func = asc

    component = None
    parts = sort.split('-')
    if len(parts) > 1:
        component = parts[0]
        sort = parts[1]
    if sort in labels:
        query = query.order_by(func(sort))
    else:
        for entity in entities:
            if component and entity.__table__.name != component:
                continue
            if sort in entity.__table__.columns:
                try:
                    attr = getattr(entity, sort)
                    query = query.order_by(func(attr))
                except AttributeError:
                    pass
                break
    return query


def visible_page_numbers(page, pages, inner_window=3, outer_window=0):
    """
    Takes the current page number and total number of pages, and computes
    an array containing the visible page numbers.  At least three pages on
    either side of the current page as well as the first and last pages
    will be included. For example::

        [1] 2 3 4 5 6 7 ... 42
        1 2 3 4 5 [6] 7 ... 42
        1 ... 4 5 6 [7] 8 9 ... 42
        1 ... 36 37 38 39 [40] 41 42

    :param page: current page number
    :param pages: total number of pages
    """
    window_from = page - inner_window
    window_to = page + inner_window

    if window_to > pages:
        window_from -= window_to - pages
        window_to = pages

    if window_from < 1:
        window_to += 1 - window_from
        window_from = 1
        if window_to > pages:
            window_to = pages

    visible = []

    left_gap_start = min(2 + outer_window, window_from)
    left_gap_end = window_from - 1

    for page in xrange(1, left_gap_start):
        visible.append(page)

    if left_gap_end - left_gap_start > 0:
        visible.append('...')
    elif left_gap_start == left_gap_end:
        visible.append(left_gap_start)

    right_gap_start = min(window_to + 1, pages - outer_window)
    right_gap_end = pages - outer_window - 1

    for page in xrange(left_gap_end + 1, right_gap_start):
        visible.append(page)

    if right_gap_end - right_gap_start > 0:
        visible.append('...')
    elif right_gap_start == right_gap_end:
        visible.append(right_gap_start)

    for page in xrange(right_gap_end + 1, pages + 1):
        visible.append(page)

    return visible

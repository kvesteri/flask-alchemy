import sqlalchemy as sa


class Base(object):
    __abstract__ = True

    id = sa.Column(sa.BigInteger, autoincrement=True, primary_key=True)

    @property
    def delete_modal_name(self):
        return 'modal-confirm-delete-%s-%d' % (self.__tablename__, self.id)

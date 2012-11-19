from datetime import datetime
import os

from flask import url_for, current_app
from flask.ext.storage import StorageException
from flask.ext.login import current_user
from wtforms_alchemy import ModelForm
from wtforms.fields import FileField
from wtforms.validators import Optional

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session, relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy


class AttachmentMixin(object):
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    type = sa.Column(sa.Unicode(255), nullable=False, index=True)
    key = sa.Column(sa.UnicodeText, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)

    uploader_id = sa.Column(None, sa.ForeignKey('user.id'), nullable=False)

    uploader = sa.relationship('User')

    created_at = sa.Column(
        sa.DateTime, nullable=False, default=datetime.utcnow
    )

    @property
    def delete_modal_name(self):
        return 'attachment-%d' % self.id

    @property
    def delete_url(self):
        return url_for(
            'attachment.delete_file', id=self.id,
        )

    @property
    def name(self):
        _, tail = os.path.split(self.key)
        return tail

    @property
    def url(self):
        return current_app.extensions['storage'].url(self.key)


class AttachmentAssociation(Base):
    """Associates a collection of Address objects
    with a particular parent.

    """
    __tablename__ = 'attachment_association'

    @classmethod
    def creator(cls, discriminator):
        """Provide a 'creator' function to use with
        the association proxy."""

        return lambda addresses: AttachmentAssociation(
            addresses=addresses,
            discriminator=discriminator
        )

    discriminator = sa.Column(sa.Unicode(255))
    """Refers to the type of parent."""

    @property
    def parent(self):
        """Return the parent object."""
        return getattr(self, "%s_parent" % self.discriminator)


class Attachment(Base):
    """The Address class.

    This represents all attachment records in a single table.
    """
    __tablename__ = 'attachment'

    association_id = sa.Column(
        sa.Integer, sa.ForeignKey('attachment_association.id')
    )
    association = relationship(
        'AttachmentAssociation',
        backref='addresses'
    )

    parent = association_proxy("association", "parent")


class HasAttachments(object):
    """HasAttachments mixin, creates a relationship to
    the attachment_association table for each parent.

    """
    @declared_attr
    def address_association_id(cls):
        return sa.Column(
            sa.Integer, sa.ForeignKey('attachment_association.id')
        )

    @declared_attr
    def address_association(cls):
        discriminator = cls.__name__.lower()
        cls.addresses = association_proxy(
            'attachment_association', 'attachments',
            creator=AddressAssociation.creator(discriminator)
        )
        return relationship(
            'AttachmentAssociation',
            backref=sa.orm.backref(
                "%s_parent" % discriminator,
                uselist=False
            )
        )


def attachment_form_factory(name, validators=[Optional()]):
    class AttachmentForm(ModelForm):
        class Meta:
            model = Attachment
            exclude = ['key', 'type', 'size']

        file = FileField(name, validators=validators)

        def populate_obj(self, obj):
            storage = current_app.extensions['storage']
            file_ = self.file.data

            if file_:
                contents = file_.read()
                if obj.id:
                    try:
                        storage.delete(obj.name)
                    except StorageException:
                        pass
                new_file = storage.save(file_.filename, contents)
                obj.key = unicode(new_file.name)
                obj.size = len(contents)
                obj.uploader = current_user


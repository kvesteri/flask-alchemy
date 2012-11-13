from datetime import datetime
import os

from flask import url_for
from flask.ext.storage import StorageException
from flask.ext.login import current_user
from wtforms_alchemy import ModelForm
from wtforms.fields import FileField
from wtforms.validators import DataRequired, Optional

from ..extensions import db, storage


class AttachmentMixin(object):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    type = db.Column(db.Unicode(255), nullable=False, index=True)
    key = db.Column(db.UnicodeText, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    uploader_id = db.Column(None, db.ForeignKey('user.id'), nullable=False)

    uploader = db.relationship('User')

    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
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
        return storage.url(self.key)


class AttachmentForm(ModelForm):
    class Meta:
        model = Attachment
        exclude = ['key', 'type', 'size']

    file = FileField(u'Picture', validators=[DataRequired()])

    def populate_obj(self, obj):
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


def attachment_form_factory(name, validators=[Optional()]):
    class OptionalAttachmentForm(AttachmentForm):
        file = FileField(name, validators=validators)

    return OptionalAttachmentForm

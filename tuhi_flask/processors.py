# Copyright 2015 icasdri
#
# This file is part of tuhi-flask.
#
# tuhi-flask is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# tuhi-flask is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with tuhi-flask.  If not, see <http://www.gnu.org/licenses/>.
from sqlalchemy import exists

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from tuhi_flask.database import db_session
from tuhi_flask.response_codes import *  # noqa
from tuhi_flask.models import User, Note, NoteContent

ERROR_FIELD_SUFFIX = "_errors"

class UnsuccessfulProcessing(Exception):
    def __init__(self, response):
        self.response = response

class ValidationError(Exception):
    def __init__(self, code=None, parallel_insert=None):
        self.code = code
        self.parallel_insert = parallel_insert

    def __int__(self):
        return self.code

class ValidationFailFastError(ValidationError):
    pass

class ValidationFatal(Exception):
    pass

class SingleUseViolation(ValidationFatal):
    pass


def _validate_type(val, type_):
    if type(val) is not type_:
        raise ValidationError(CODE_INCORRECT_TYPE)

def _validate_uuid(uuid):
    _validate_type(uuid, str)
    if len(uuid) != 36:
        raise ValidationError(CODE_INVALID_UUID)

def _validate_date(val):
    _validate_type(val, int)
    if not 1433131200 < val < 7258136400:  # June 1, 2015 to Jan. 1, 2200
        raise ValidationError(CODE_INVALID_DATE)


class ObjectProcessor(object):
    # Subclasses should define validation methods of the form _validate_<field_name>():
    # these methods should raise the appropriate ValidationError with error code on validation failures
    # and optionally return a parsed value of the field to be used by processing logic

    def __init__(self, **kwargs):
        # This init function allows a Processor to be instantiated with arguments defining
        # context, such as a specific user, permission-set, etc.
        for kw, val in kwargs.items():
            setattr(self, kw, val)

    # Subclasses should enumerate a list of fields here
    _fields = None

    # Subclasses should enumerate a list of fields that should
    # be rendered as is on the return response here
    _fields_reflected_on_error = None

    # Subclasses should set to True if one of the _validate functions
    # alters the global Processor state in an irreversible way or in a way
    # that does not sufficiently restore the state. This usually occurs
    # when one validation depends on the output of another
    _single_use = False
    # Counter of uses to enforce single-use
    _num_uses = 0

    def _process_object(self, obj):
        # Subclasses should override this to take an object in the form of a dict
        # with parsed field values and process it (creating database entries, etc.)
        # This method must NOT raise a ValidationError.
        pass

    def _pre_process_object(self, obj):
        # Subclasses should override this to perform any logic before execution of the
        # _process_object() method. This method should raise ValidationErrors with
        # parallel inserts but withoud error codes on preprocess/validation failure.
        # This method should be used to implement preprocessing/validation that does
        # not fit well with any one field (e.g. those depending on context, etc.)
        pass

    @staticmethod
    def _get_strlist_or_default(strlist, default):
        if strlist is None:
            strlist = default
        if isinstance(strlist, str):
            strlist = (strlist,)
        return strlist

    def process(self, target, fields=None, fields_reflected_on_error=None, fail_fast_on_missing=False):
        # This method validates the given target and processes it if valid, or returns a error response if not
        # This method returns a tuple of the form (passed, response)
        #   where passed is a boolean that is True if all validation on this target passed (False otherwise)
        #   and where response contains the data payload (can be None if no changes wanted)

        if self._single_use and self._num_uses > 0:
            raise SingleUseViolation(self.__class__)

        if not isinstance(target, dict):
            return False, CODE_INCORRECT_TYPE

        fields = ObjectProcessor._get_strlist_or_default(fields, self._fields)
        if fields is None:
            raise ValidationFatal("No fields to validate")

        fields_reflected_on_error = ObjectProcessor._get_strlist_or_default(fields_reflected_on_error,
                                                                            self._fields_reflected_on_error)
        if fields_reflected_on_error is None:
            fields_reflected_on_error = []

        self._num_uses += 1

        try:
            self._process_fields(fields, target, fail_fast_on_missing)
            self._call_pre_process(target)
        except UnsuccessfulProcessing as u:
            return self._render(False, u.response, target, fields_reflected_on_error)
        else:
            return True, self._process_object(target)

    def _process_fields(self, fields, target, fail_fast_on_missing):
        response = {}

        for field in fields:
            error_field = field + ERROR_FIELD_SUFFIX
            try:
                value = target[field]
                validation_func = self._get_validation_func(field)
                try:
                    new_value = validation_func(value)
                    if new_value is not None:
                        target[field] = new_value
                except ValidationError as ve:
                    response[error_field] = int(ve)
                    if ve.parallel_insert is not None:
                        response.update(ve.parallel_insert)
                    if isinstance(ve, ValidationFailFastError):
                        raise UnsuccessfulProcessing(response)
            except (ValueError, KeyError):
                response[error_field] = CODE_MISSING
                if fail_fast_on_missing:
                    raise UnsuccessfulProcessing(response)

        if len(response) > 0:
            raise UnsuccessfulProcessing(response)

    def _get_validation_func(self, field):
        try:
            return getattr(self, "_validate_" + field)
        except AttributeError:
            raise ValidationFatal("No validation method exists for field: {}".format(field))

    def _call_pre_process(self, target):
        try:
            self._pre_process_object(target)
        except ValidationError as ve:
            raise UnsuccessfulProcessing(ve.parallel_insert)

    def _render(self, passed, payload, target, reflect_fields):
        for field in reflect_fields:
            error_field = field + ERROR_FIELD_SUFFIX
            if not (error_field in payload and payload[error_field] == CODE_MISSING):
                payload[field] = target[field]
        return passed, payload


class TopLevelProcessor(ObjectProcessor):
    _fields = "notes", "note_contents"

    def _validate_notes(self, val):
        _validate_type(val, list)

    def _validate_note_contents(self, val):
        _validate_type(val, list)


class NoteProcessor(ObjectProcessor):
    # This Processor must be instantiated with a context containing 'user_id'
    _fields = "note_id", "title", "deleted", "date_modified"
    _fields_reflected_on_error = "note_id"

    def _validate_note_id(self, uuid):
        _validate_uuid(uuid)

    def _validate_title(self, val):
        _validate_type(val, str)

    def _validate_deleted(self, val):
        _validate_type(val, bool)

    def _validate_date_modified(self, date):
        _validate_date(date)

    def _pre_process_object(self, obj):
        # TODO: Somehow move actual UPDATE and INSERT logic into _process_object().
        # (is difficult because must check for if note exists, and must grab a
        #  user_id from database, and must be able to raise ValidationError on auth issue)
        try:
            # note = Note.query.filter_by(note_id=obj["note_id"]).one()
            # user_id = note.user_id
            (user_id, ) = db_session.query(Note.user_id).filter(Note.note_id == obj["note_id"]).one()
        except MultipleResultsFound:
            raise ValidationFatal("Non-unique note_id detected in database.")
        except NoResultFound:
            # Add as new
            obj["user_id"] = self.user_id
            note = Note(**obj)
            db_session.add(note)
            db_session.commit()
        else:
            # Update existing
            if user_id != self.user_id:
                raise ValidationFailFastError(parallel_insert={"authentication": CODE_FORBIDDEN})
            Note.query.filter(Note.note_id == obj["note_id"]).update(obj)
            db_session.commit()

    def _process_object(self, obj):
        pass


class NoteContentProcessor(ObjectProcessor):
    # This Processor must be instantiated with a context containing 'user_id'
    _fields = "note_content_id", "note", "data", "date_created"
    _fields_reflected_on_error = "note_content_id"

    def _validate_note_content_id(self, uuid):
        _validate_uuid(uuid)
        (uuid_conflict, ), = db_session.query(exists().where(NoteContent.note_content_id == uuid))
        if uuid_conflict:
            raise ValidationFailFastError(CODE_ALREADY_EXISTS_CONFLICT)

    def _validate_note(self, note_id):
        _validate_uuid(note_id)
        try:
            note_id, user_id = db_session.query(Note.note_id, Note.user_id).filter(Note.note_id == note_id).one()
        except NoResultFound:
            raise ValidationFailFastError(CODE_DOES_NOT_EXIST)
        except MultipleResultsFound:
            raise ValidationFatal("Non-unique note_id detected in database.")
        else:
            if user_id == self.user_id:
                self.note_id = note_id
            else:
                raise ValidationFailFastError(CODE_FORBIDDEN, parallel_insert={"authentication": CODE_FORBIDDEN})

    def _validate_data(self, data):
        _validate_type(data, str)

    def _validate_date_created(self, date):
        _validate_date(date)

    def _process_object(self, obj):
        obj["note_id"] = obj["note"]
        del obj["note"]
        note_content = NoteContent(**obj)
        db_session.add(note_content)
        db_session.commit()


class AuthenticationProcessor(ObjectProcessor):
    _fields = "username", "password"
    # _single_use = True

    def _validate_username(self, val):
        _validate_type(val, str)
        try:
            self.user_to_auth = User.query.filter_by(username=val).one()
        except NoResultFound:
            raise ValidationFailFastError(CODE_DOES_NOT_EXIST)
        except MultipleResultsFound:
            raise ValidationFatal("Non-unique usernames detected in database.")

    def _validate_password(self, val):
        _validate_type(val, str)
        if self.user_to_auth.check_password(val):
            return
        else:
            raise ValidationFailFastError(CODE_PASSWORD_INCORRECT)

    def _process_object(self, obj):
        return self.user_to_auth.user_id

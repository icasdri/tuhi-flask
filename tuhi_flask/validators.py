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

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from tuhi_flask.response_codes import *
from tuhi_flask.models import *

ERROR_FIELD_SUFFIX = "_errors"

class ValidationError(Exception):
    def __init__(self, code, parallel_insert=None):
        self.code = code
        self.parallel_insert = parallel_insert

    def __int__(self):
        return self.code

class ValidationFailFastError(ValidationError):
    pass

class ValidationFatal(Exception):
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


class Processor:
    def process(self, target):
        # This method validates the given target and processes it if valid, or returns a error response if not
        # Subclasses should override to actually do something
        #
        # Should return tuple (passed, response)
        #   where passed is a boolean that is True if all validation on this target passed (False otherwise)
        #   and where response contains the data payload (can be None if no changes wanted)
        pass

class ObjectProcessor(Processor):
    # Subclasses should define validation methods of the form _validate_<field_name>():
    # these methods should raise the appropriate ValidationError on validation failures
    # and optionally return a parsed value of the field to be used by processing logic

    def __init__(self, **kwargs):
        # This init function allows a Processor to be instantiated with arguments defining
        # context, such as a specific user, permission-set, etc.
        for kw, val in kwargs:
            setattr(self, kw, val)

    def _fields(self):
        # Subclasses should override this to enumerate a list of fields
        pass

    def _fields_reflected_on_error(self):
        # Subclasses should override this to enumerate a list of fields that should
        # be rendered as is on the return response
        pass

    def _process_object(self, obj):
        # Subclasses should override this to take an object in the form of a dict
        # with parsed field values and process it (creating database entries, etc.)
        pass

    def process(self, target, fields=None, fail_fast_on_missing=False):
        if not isinstance(target, dict):
            return False, CODE_INCORRECT_TYPE

        if fields is None:
            default_fields = self._fields()
            if default_fields is None:
                raise ValidationFatal("No fields to validate")
            else:
                fields = default_fields

        response = {}

        for field in fields:
            error_field = field + ERROR_FIELD_SUFFIX
            try:
                value = target[field]
                try:
                    validation_func = getattr(self, "_validate_" + field)
                except AttributeError:
                    raise ValidationFatal("No validation method exists for field: {}".format(field))

                try:
                    new_value = validation_func(value)
                    if new_value is not None:
                        target[field] = new_value
                except ValidationError as ve:
                    response[error_field] = int(ve)
                    if ve.parallel_insert is not None:
                        response.update(ve.parallel_insert)
                    if isinstance(ve, ValidationFailFastError):
                        return self._render(False, response, target)
                # except Exception as e:
                #     print(e)
                #     response[error_field] = CODE_UNKNOWN
                #     return self._render(False, response, target)
            except (ValueError, KeyError):
                response[error_field] = CODE_MISSING
                if fail_fast_on_missing:
                    return self._render(False, response, target)

        if len(response) > 0:
            return self._render(False, response, target)
        else:
            return True, self._process_object(target)

    def _render(self, passed, payload, target):
        fields_reflected_on_error = self._fields_reflected_on_error()
        if fields_reflected_on_error is not None:
            for field in fields_reflected_on_error:
                error_field = field + ERROR_FIELD_SUFFIX
                if not (error_field in payload and payload[error_field] == CODE_MISSING):
                    payload[field] = target[field]
        return passed, payload


class TopLevelProcessor(ObjectProcessor):
    def _fields(self):
        return "notes", "note_contents"

    def _validate_notes(self, val):
        _validate_type(val, list)

    def _validate_note_contents(self, val):
        _validate_type(val, list)


class NoteProcessor(ObjectProcessor):
    def _fields(self):
        return "note_id", "title", "deleted", "date_modified"

    def _fields_reflected_on_error(self):
        return ("note_id",)

    def _validate_note_id(self, uuid):
        _validate_uuid(uuid)

    def _validate_title(self, val):
        _validate_type(val, str)

    def _validate_deleted(self, val):
        _validate_type(val, bool)

    def _validate_date_modified(self, date):
        _validate_date(date)

    def _process_object(self, obj):
        pass


class NoteContentProcessor(ObjectProcessor):
    def _fields(self):
        return "note_content_id", "note", "data", "date_created"

    def _fields_reflected_on_error(self):
        return ("note_content_id",)

    def _validate_note_content_id(self, uuid):
        _validate_uuid(uuid)
        # TODO: Hit database to check for uuid conflicts

    def _validate_note(self, note_id):
        _validate_uuid(note_id)
        # TODO: Hit database to see if note actually exists

    def _validate_data(self, data):
        _validate_type(data, str)

    def _validate_date_created(self, date):
        _validate_date(date)

    def _process_object(self, obj):
        pass


class AuthenticationProcessor(ObjectProcessor):
    def _fields(self):
        return "username", "password"

    def _validate_username(self, val):
        _validate_type(val, str)
        try:
            self.user_to_auth = User.query.filter_by(username=val).one()
        except NoResultFound:
            raise ValidationFailFastError(CODE_USER_NOT_EXIST)
        except MultipleResultsFound:
            raise ValidationFatal("Non-unique usernames detected in database.")

    def _validate_password(self, val):
        _validate_type(val, str)
        if self.user_to_auth.check_password(val):
            return
        else:
            raise ValidationFailFastError(CODE_PASSWORD_INCORRECT)

    def _process_object(self, obj):
        return self.user_to_auth

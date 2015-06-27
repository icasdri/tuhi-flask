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

from tuhi_flask.response_codes import *

class ValidationError(Exception):
    def __init__(self, code):
        self.code = code

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


class Validator:
    def validate(self, target):
        # Subclasses should override to actually do something
        #
        # Should return tuple (success, response)
        #   where success if a boolean that is True if all validation on this target passed (False otherwise)
        #   and where response contains the data payload (can be None if no changes wanted)
        pass

class ObjectValidator(Validator):
    def _fields(self):
        # Subclasses should override this to enumerate a list of fields
        pass

    def validate(self, target, fields=None, fail_fast_on_missing=False):
        if type(target) is not dict:
            return False, CODE_INCORRECT_TYPE

        if fields is None:
            default_fields = self._fields()
            if default_fields is None:
                raise ValidationFatal("No fields to validate")
            else:
                fields = default_fields

        response = {}

        for field in fields:
            error_field = field + "_errors"
            try:
                value = target[field]
                try:
                    validation_func = getattr(self, "_validate_" + field)
                except AttributeError:
                    raise ValidationFatal("No validation method exists for field: {}".format(field))

                try:
                    validation_func(value)
                except ValidationFailFastError as vffe:
                    response[error_field] = int(vffe)
                    return False, response
                except ValidationError as ve:
                    response[error_field] = int(ve)
                except Exception:
                    response[error_field] = CODE_UNKNOWN
                    return False, response
            except ValueError:
                response[field] = CODE_MISSING
                if fail_fast_on_missing:
                    return False, response

        return True, None


class TopLevelValidator(ObjectValidator):
    def _validate_notes(self, val):
        _validate_type(val, list)

    def _validate_note_contents(self, val):
        _validate_type(val, list)


class NoteValidator(ObjectValidator):
    def _validate_note_id(self, uuid):
        _validate_uuid(uuid)

    def _validate_title(self, val):
        _validate_type(val, str)

    def _validate_deleted(self, val):
        _validate_type(val, bool)

    def _validate_date_modified(self, date):
        _validate_date(date)

class NoteContentValidator(ObjectValidator):
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
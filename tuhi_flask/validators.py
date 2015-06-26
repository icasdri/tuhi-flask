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

MISSING_MESSAGE = "missing"

class ValidationError(Exception):
    pass

class ValidationFailFastError(ValidationError):
    pass

class ValidationFatal(Exception):
    pass

class Validator:
    def _fields(self):
        # Subclasses should override this to enumerate a list of fields
        pass

    def validate(self, target, fields=None, fail_fast_on_missing=False):
        if fields is None:
            default_fields = self._fields()
            if default_fields is None:
                raise ValidationFatal("No fields to validate")
            else:
                fields = default_fields

        response = {}

        for field in fields:
            try:
                value = target[field]
            except ValueError:
                response[field] = MISSING_MESSAGE
                if fail_fast_on_missing:
                    return response

            try:
                validation_func = getattr(self, "_validate_" + field)
            except AttributeError:
                raise ValidationFatal("No validation method exists for field: {}".format(field))

            try:
                validation_func()
            except ValidationFailFastError as vffe:
                response[field] = str(vffe)
                return response
            except ValidationError as ve:
                response[field] = str(ve)
            except Exception:
                response[field] = "Unknown error"
                return response


class NoteValidator(Validator):
    def _validate_note_id(self, val):
        pass

    def _validate_title(self, val):
        pass

    def _validate_deleted(self, val):
        pass

    def _validate_date_modified(self, val):
        pass

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

class Serializer(object):
    # Subclasses can optionally define serialization methods of the form _serialize_<field_name>():
    # that take a value (taken from the model object) and serialize it into the desired form.
    # Enumerated fields without custom serialization methods will have their literal values from
    # the model object serialized be default.

    # Subclasses should enumerate a list of fields to be serialized here
    _fields = None

    # Subclasses can optionally provide a mapping of model object field names to
    # serialized field names here
    _field_mappings = {}

    def _default_serializer(self, val):
        return val

    def serialize(self, model_object):
        response = {}
        for field in self._fields:
            try:
                serialization_func = getattr(self, "_serialize_" + field)
            except AttributeError:
                serialization_func = self._default_serializer

            if field in self._field_mappings:
                target = self._field_mappings[field]
            else:
                target = field

            response[target] = serialization_func(getattr(model_object, field))
        return response


class NoteSerializer(Serializer):
    _fields = "note_id", "date_created"


class NoteContentSerializer(Serializer):
    _fields = "note_content_id", "note_id", "type", "data", "date_created"
    _field_mappings = {"note_id": "note"}

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

from functools import wraps
from flask import request, json
from flask_restful import Resource
from tuhi_flask.database import db_session
from tuhi_flask.models import *
from tuhi_flask.response_codes import *
from tuhi_flask.serializers import NoteSerializer, NoteContentSerializer
from tuhi_flask.validators import TopLevelProcessor, NoteProcessor, NoteContentProcessor, \
    AuthenticationProcessor, ValidationFatal

# For list of guaranteed-supported codes, check http://www.w3.org/Protocols/HTTP/HTRESP.html
RESPONSE_BAD_REQUEST = 400  # HTTP: Bad Requeset
RESPONSE_PARTIAL = 202  # HTTP: Accepted
RESPONSE_CONFLICT = 409  # HTTP: Conflict
RESPONSE_UNAUTHORIZED = 401  # HTTP: Unauthorized


top_level_processor = TopLevelProcessor()
authentication_processor = AuthenticationProcessor()

note_serializer = NoteSerializer()
note_content_serializer = NoteContentSerializer()


class NotesEndpoint(Resource):
    def _get_user(self):
        response = {}
        passed = False
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header is not None and auth_header != "":
                if auth_header.startswith("Basic"):
                    if request.authorization is not None:
                        passed, result = authentication_processor.process(request.authorization, fail_fast_on_missing=True)
                        response["authentication"] = result
                    else:
                        response["authentication_errors"] = CODE_BAD_BASIC_AUTH_FORMAT
                else:
                    try:
                        auth_dict = json.loads(auth_header)
                    except:
                        response["authentication_errors"] = CODE_BAD_JSON
                    else:
                        passed, result = authentication_processor.process(auth_dict, fail_fast_on_missing=True)
                        response["authentication"] = result
            else:
                response["authentication_errors"] = CODE_MISSING
        else:
            response["authentication_errors"] = CODE_MISSING

        if passed:
            return True, result
        else:
            return False, (response, RESPONSE_UNAUTHORIZED)

    def _query_objects(self, user_id, args):
        note_query = Note.query.filter(Note.user_id == user_id)
        note_content_query = NoteContent.query.filter(Note.user_id == user_id)

        if "head" in args and args["head"].lower() == "true":
            return (note_query.order_by(Note.date_modified.desc()).first(),), \
                   (note_content_query.order_by(NoteContent.date_created.desc()).first(),)
        elif "after" in args:
            try:
                after = int(args["after"])
            except ValueError:
                pass
            else:
                return note_query.filter(Note.date_modified > after).all(), \
                       note_content_query.filter(NoteContent.date_created > after).all()

        return note_query.all(), note_content_query.all()


    def get(self):
        auth_ok, auth_result = self._get_user()
        if not auth_ok:
            return auth_result
        else:
            user_id = auth_result

        note_objects, note_content_objects = self._query_objects(user_id, request.args)

        serialized_notes = []
        serialized_note_contents = []

        for note in note_objects:
            serialized_notes.append(note_serializer.serialize(note))

        for note_content in note_content_objects:
            serialized_note_contents.append(note_content_serializer.serialize(note_content))

        return {'notes': serialized_notes,
                'note_contents': serialized_note_contents}

    def post(self):
        auth_ok, auth_result = self._get_user()
        if not auth_ok:
            return auth_result
        else:
            user_id = auth_result

        data = request.get_json(force=True)
        notes_error_list = []
        note_contents_error_list = []

        top_level_passed, top_level_errors = top_level_processor.process(data)
        if not top_level_passed:
            return top_level_errors, RESPONSE_BAD_REQUEST

        note_processor = NoteProcessor(user_id=user_id)
        note_content_processor = NoteContentProcessor(user_id=user_id)

        response = {}

        for note in data["notes"]:
            note_passed, note_errors = note_processor.process(note)
            if not note_passed:
                notes_error_list.append(note_errors)

        for note_content in data["note_contents"]:
            note_content_passed, note_content_errors = note_content_processor.process(note_content)
            if not note_content_passed:
                note_contents_error_list.append(note_content_errors)

        if len(notes_error_list) > 0:
            response["notes"] = notes_error_list
        if len(note_contents_error_list) > 0:
            response["note_contents"] = note_contents_error_list

        if len(response) > 0:
            return response, RESPONSE_PARTIAL


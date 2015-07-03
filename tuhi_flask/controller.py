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
from tuhi_flask.response_codes import *
from tuhi_flask.validators import TopLevelProcessor, NoteProcessor, NoteContentProcessor, \
    AuthenticationProcessor, ValidationFatal

# For list of guaranteed-supported codes, check http://www.w3.org/Protocols/HTTP/HTRESP.html
RESPONSE_BAD_REQUEST = 400  # HTTP: Bad Requeset
RESPONSE_PARTIAL = 202  # HTTP: Accepted
RESPONSE_CONFLICT = 409  # HTTP: Conflict
RESPONSE_UNAUTHORIZED = 401  # HTTP: Unauthorized


top_level_processor = TopLevelProcessor()
authentication_processor = AuthenticationProcessor()


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
                        passed, result = authentication_processor.process(auth_dict, fail_fast_on_missing=True)
                        response["authentication"] = result
                    except:
                        response["authentication_errors"] = CODE_BAD_JSON
            else:
                response["authentication_errors"] = CODE_MISSING
        else:
            response["authentication_errors"] = CODE_MISSING

        if passed:
            return True, result
        else:
            return False, (response, RESPONSE_UNAUTHORIZED)

    def get(self):
        auth_ok, auth_result = self._get_user()
        if not auth_ok:
            return auth_result
        else:
            user = auth_result

        print(request.args)  # Query value will be in here, e.g. ?after=2015-06-14T19:04:43.238851
        return {'notes': [],
                'note_contents': []}

    def post(self):
        auth_ok, auth_result = self._get_user()
        if not auth_ok:
            return auth_result
        else:
            user = auth_result

        data = request.get_json(force=True)
        notes_error_list = []
        note_contents_error_list = []

        top_level_passed, top_level_errors = top_level_processor.process(data)
        if not top_level_passed:
            return top_level_errors, RESPONSE_BAD_REQUEST

        note_processor = NoteProcessor(user=user)
        note_content_processor = NoteContentProcessor(user=user)

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


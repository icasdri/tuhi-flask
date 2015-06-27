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

from flask import request
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from tuhi_flask.database import db_session

# For list of guaranteed-supported codes, check http://www.w3.org/Protocols/HTTP/HTRESP.html
RESPONSE_CODE = {
    "Bad Request": 400,  # HTTP: Bad Request
    "Conflict": 409,  # HTTP: Conflict
    "Partial": 202  # HTTP: Accepted
}

def _uuid_type(value):
    if type(value) is str and len(value) == 36:
        return value
    else:
        raise TypeError("Invalid UUID")

def _date_type(value):
    # TODO: Potential to add more sanity checks here
    return int(value)

# note_parser = RequestParser(bundle_errors=True)
# note_parser.add_argument("note_id", type=_uuid_type, required=True)
# note_parser.add_argument("title", type=str, required=True)
# note_parser.add_argument("deleted", type=bool, required=True)
# note_parser.add_argument("date_modified", type=_date_type, required=True)

class RespondImmediatelyWithReason(Exception):
    def __init__(self, reason, keep_response=True):
        if reason in RESPONSE_CODE:
            self.response_code = RESPONSE_CODE[reason]
        else:
            self.response_code = reason
        self.keep_response = keep_response


def _check_missing_keys(data, response):
    missing = []
    for needed in ("notes", "note_contents"):
        if needed not in data.keys() or type(data[needed]) is not list:
            missing.append(needed)
    if len(missing) != 0:
        response['missing'] = missing
        raise RespondImmediatelyWithReason("Bad Request")

def _check_ignoring_keys(data, response):
    ignoring = data.keys() - {"notes", "note_contents"}
    if ignoring == set():
        return
    else:
        response['ignoring'] = list(ignoring)

# TODO: Actual user logic (cannot remain as None), with authentication token
def _process_note(note_dict, user=None):
    response = {}
    uuid = _uuid_type(note_dict[])

def _process_note_content(note_content_dict):
    pass

class NotesEndpoint(Resource):
    def get(self):
        print(request.args)  # Query value will be in here, e.g. ?after=2015-06-14T19:04:43.238851
        return {'notes': [],
                'note_contents': []}

    def post(self):
        data = request.get_json(force=True)
        response = {}
        try:
            _check_missing_keys(data, response)
            _check_ignoring_keys(data, response)
        except RespondImmediatelyWithReason as riwr:
            if riwr.keep_response:
                return response, riwr.response_code
            else:
                return "", riwr.response_code
        return response

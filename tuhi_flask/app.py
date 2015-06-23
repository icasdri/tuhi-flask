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

import os
from flask import Flask
from flask_restful import Api
from tuhi_flask.database import db_session
from tuhi_flask.controller import NotesEndpoint

app = Flask(__name__)
app.config.from_object('tuhi_flask.default_config')
if os.getenv('TUHI_FLASK_CONFIG') is not None:
    app.config.from_envvar('TUHI_FLASK_CONFIG')
api = Api(app)

api.add_resource(NotesEndpoint, '/notes')

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run(debug=True)

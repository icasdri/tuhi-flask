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

from tuhi_flask.app import app as main_app
from tuhi_flask.models import *
from tuhi_flask.database import init_db

def init():
    with main_app.context():
        init_db()
        from tuhi_flask.database import db_session
        u = User(username="testuser", password="password")
        db_session.add(u)
        db_session.commit()

if __name__ == "__main__":
    init()
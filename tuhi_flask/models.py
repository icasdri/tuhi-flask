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

from sqlalchemy import Column, Integer, String, CHAR, Text, Boolean, DateTime, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from tuhi_flask.database import Base
from tuhi_flask.app import app

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password_hash = Column(String)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password,
                                                    method=app.config['PASSWORD_HASH_METHOD'],
                                                    salt_length=app.config['PASSWORD_SALT_LENGTH'])

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Note(Base):
    __tablename__ = 'notes'
    note_id = Column(CHAR(36), primary_key=True)
    user = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    deleted = Column(Boolean, default=False)
    date_modified = Column(DateTime)  # May need to use Integer from epoch here


class NoteContent(Base):
    __tablename__ = 'note_contents'
    note_content_id = Column(CHAR(36), primary_key=True)
    note = Column(CHAR(36), ForeignKey('notes.note_id'))
    data = Column(Text)
    date_created = Column(DateTime)  # May need to use Integer from epoch here


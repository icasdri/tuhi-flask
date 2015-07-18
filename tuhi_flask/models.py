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

from flask import current_app as app
from sqlalchemy import Column, Integer, String, CHAR, Text, Boolean, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from tuhi_flask.database import Base

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
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
    user_id = Column(Integer, ForeignKey('users.user_id'), index=True)
    deleted = Column(Boolean, default=False)
    date_modified = Column(Integer, index=True)  # Seconds from epoch


class NoteContent(Base):
    __tablename__ = 'note_contents'
    note_content_id = Column(CHAR(36), primary_key=True)
    note_id = Column(CHAR(36), ForeignKey('notes.note_id'), index=True)
    data = Column(Text)
    date_created = Column(Integer, index=True)  # Seconds from epoch

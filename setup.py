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
from setuptools import setup, find_packages

setup(
    name='tuhi-flask',
    version='0.1',
    license='AGPL3',
    author='icasdri',
    author_email='icasdri@gmail.com',
    description='Simple self-hosted synchronized notes (Tuhi Server Reference Implementation)',
    url='https://github.com/icasdri/tuhi-flask',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Office/Business',
        'Topic :: Text Editors',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    packages=find_packages(),
    install_requires=['sqlalchemy>=1.0', 'flask-restful>=0.3', 'flask>=0.10'],
    entry_points={
        'console_scripts': ['tuhi-flask-dev = tuhi_flask.app:main'],
    }
)

# Copyright (C) 2008-2012  Canonical, Ltd.
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""A test plugin."""

__metaclass__ = type
__all__ = ["AlphaCruft", "AlphaPlugin"]

from janitor.plugincore.cruft import Cruft
from janitor.plugincore.plugin import Plugin


class AlphaCruft(Cruft):
    def __init__(self, app):
        self.app = app

    def get_shortname(self):
        return "Alpha"

    def cleanup(self):
        # Tell the app we're cleaning up this cruft.
        self.app.notifications.append((self, "cruft"))


class AlphaPlugin(Plugin):
    def get_cruft(self):
        yield AlphaCruft(self.app)

    def post_cleanup(self):
        self.app.notifications.append((self, "post"))

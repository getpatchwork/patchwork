# Patchwork - automated patch tracking system
# Copyright (C) 2015 Intel Corporation
#
# This file is part of the Patchwork package.
#
# Patchwork is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Patchwork is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Patchwork; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from patchwork.tests.browser import SeleniumTestCase
from patchwork.tests.test_user import TestUser

class LoginTestCase(SeleniumTestCase):
    def setUp(self):
        super(LoginTestCase, self).setUp()
        self.user = TestUser()

    def test_default_focus(self):
        self.get('/user/login/')
        self.wait_until_focused('#id_username')

    def test_login(self):
        self.get('/user/login/')
        self.enter_text('username', self.user.username)
        self.enter_text('password', self.user.password)
        self.click('input[value="Login"]')
        dropdown = self.wait_until_visible('a.dropdown-toggle strong')
        self.assertEquals(dropdown.text, 'testuser')

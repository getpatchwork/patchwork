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

import errno
import os
import time

try:  # django 1.7+
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase
except:
    from django.test import LiveServerTestCase as StaticLiveServerTestCase
from selenium.common.exceptions import (
        NoSuchElementException, StaleElementReferenceException,
        TimeoutException)
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


class Wait(WebDriverWait):
    """Subclass of WebDriverWait.

    Includes a predetermined timeout and poll frequency. Also deals with a
    wider variety of exceptions.
    """
    _TIMEOUT = 10
    _POLL_FREQUENCY = 0.5

    def __init__(self, driver):
        super(Wait, self).__init__(driver, self._TIMEOUT, self._POLL_FREQUENCY)

    def until(self, method, message=''):
        """Call method with driver until it returns True."""
        end_time = time.time() + self._timeout

        while True:
            try:
                value = method(self._driver)
                if value:
                    return value
            except NoSuchElementException:
                pass
            except StaleElementReferenceException:
                pass

            time.sleep(self._poll)
            if(time.time() > end_time):
                break

        raise TimeoutException(message)

    def until_not(self, method, message=''):
        """Call method with driver until it returns True."""
        end_time = time.time() + self._timeout
        while(True):
            try:
                value = method(self._driver)
                if not value:
                    return value
            except NoSuchElementException:
                return True
            except StaleElementReferenceException:
                pass

            time.sleep(self._poll)
            if(time.time() > end_time):
                break

        raise TimeoutException(message)


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class SeleniumTestCase(StaticLiveServerTestCase):
    # TODO(stephenfin): This should handle non-UNIX paths
    _SCREENSHOT_DIR = os.path.dirname(__file__) + '/../../selenium_screenshots'

    def setUp(self):
        self.skip = os.getenv('PW_SKIP_BROWSER_TESTS', None)
        if self.skip:
            self.skipTest('Disabled by environment variable')

        super(SeleniumTestCase, self).setUp()

        self.browser = os.getenv('SELENIUM_BROWSER', 'chrome')
        if self.browser == 'firefox':
            self.selenium = webdriver.Firefox()
        if self.browser == 'chrome':
            self.selenium = webdriver.Chrome(
                service_args=['--verbose', '--log-path=selenium.log']
            )

        mkdir(self._SCREENSHOT_DIR)
        self._screenshot_number = 1

    def tearDown(self):
        self.selenium.quit()
        super(SeleniumTestCase, self).tearDown()

    def screenshot(self):
        name = '%s_%d.png' % (self._testMethodName, self._screenshot_number)
        path = os.path.join(self._SCREENSHOT_DIR, name)
        self.selenium.get_screenshot_as_file(path)
        self._screenshot_number += 1

    def get(self, relative_url):
        self.selenium.get('%s%s' % (self.live_server_url, relative_url))
        self.screenshot()

    def find(self, selector):
        return self.selenium.find_element_by_css_selector(selector)

    def focused_element(self):
        return self.selenium.switch_to.active_element

    def wait_until_present(self, name):
        is_present = lambda driver: driver.find_element_by_name(name)
        msg = "An element named '%s' should be on the page" % name
        element = Wait(self.selenium).until(is_present, msg)
        self.screenshot()
        return element

    def wait_until_visible(self, selector):
        is_visible = lambda driver: self.find(selector).is_displayed()
        msg = "The element matching '%s' should be visible" % selector
        Wait(self.selenium).until(is_visible, msg)
        self.screenshot()
        return self.find(selector)

    def wait_until_focused(self, selector):
        is_focused = lambda driver: (
            self.find(selector) == self.focused_element())
        msg = "The element matching '%s' should be focused" % selector
        Wait(self.selenium).until(is_focused, msg)
        self.screenshot()
        return self.find(selector)

    def enter_text(self, name, value):
        field = self.wait_until_present(name)
        field.send_keys(value)
        return field

    def click(self, selector):
        element = self.wait_until_visible(selector)
        element.click()
        return element

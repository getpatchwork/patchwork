# Patchwork - automated patch tracking system
# Copyright (C) 2014 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest
from xmlrpc import client as xmlrpc_client

from django.conf import settings
from django.test import LiveServerTestCase
from django.urls import reverse

from patchwork.tests import utils


class ServerProxy(xmlrpc_client.ServerProxy):

    def close(self):
        self.__close()


@unittest.skipUnless(settings.ENABLE_XMLRPC,
                     'requires xmlrpc interface (use the ENABLE_XMLRPC '
                     'setting)')
class XMLRPCTest(LiveServerTestCase):

    def setUp(self):
        self.url = self.live_server_url + reverse('xmlrpc')
        self.rpc = ServerProxy(self.url)

    def tearDown(self):
        self.rpc.close()


class XMLRPCGenericTest(XMLRPCTest):

    def test_pw_rpc_version(self):
        # If you update the RPC version, update the tests!
        self.assertEqual(self.rpc.pw_rpc_version(), [1, 3, 0])

    def test_get_redirect(self):
        response = self.client.patch(self.url)
        self.assertRedirects(response, reverse('project-list'))

    def test_invalid_method(self):
        with self.assertRaises(xmlrpc_client.Fault):
            self.rpc.xyzzy()

    def test_absent_auth(self):
        with self.assertRaises(xmlrpc_client.Fault):
            self.rpc.patch_set(0, {})


@unittest.skipUnless(settings.ENABLE_XMLRPC,
                     'requires xmlrpc interface (use the ENABLE_XMLRPC '
                     'setting)')
class XMLRPCAuthenticatedTest(LiveServerTestCase):

    def setUp(self):
        self.url = self.live_server_url + reverse('xmlrpc')
        # url is of the form http://localhost:PORT/PATH
        # strip the http and replace it with the username/passwd of a user.
        self.project = utils.create_project()
        self.user = utils.create_maintainer(self.project)
        self.url = ('http://%s:%s@' + self.url[7:]) % (self.user.username,
                                                       self.user.username)
        self.rpc = ServerProxy(self.url)

    def tearDown(self):
        self.rpc.close()

    def test_patch_set(self):
        patch = utils.create_patch(project=self.project)
        result = self.rpc.patch_get(patch.id)
        self.assertFalse(result['archived'])

        self.rpc.patch_set(patch.id, {'archived': True})

        # reload the patch
        result = self.rpc.patch_get(patch.id)
        self.assertTrue(result['archived'])


class XMLRPCModelTestMixin(object):

    def create_multiple(self, count):
        return [self.create_single() for i in range(count)]

    def test_get_none(self):
        self.assertEqual(self.get_endpoint(0), {})

    def test_list_none(self):
        self.assertEqual(self.list_endpoint(), [])

    def test_list_single(self):
        obj = self.create_single()
        result = self.list_endpoint()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], obj.id)

    def test_list_named(self):
        obj = self.create_single(name='FOOBARBAZ')
        self.create_multiple(5)
        result = self.list_endpoint('oobarb')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], obj.id)

    def test_list_named_none(self):
        self.create_multiple(5)
        result = self.list_endpoint('invisible')
        self.assertEqual(len(result), 0)

    def test_get_single(self):
        obj = self.create_single()
        result = self.get_endpoint(obj.id)
        self.assertEqual(result['id'], obj.id)

    def test_get_invalid(self):
        obj = self.create_single()
        result = self.get_endpoint(obj.id + 1)
        self.assertEqual(result, {})

    def test_list_multiple(self):
        self.create_multiple(5)
        result = self.list_endpoint()
        self.assertEqual(len(result), 5)

    def test_list_max_count(self):
        objs = self.create_multiple(5)
        result = self.list_endpoint("", 2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], objs[0].id)

    def test_list_negative_max_count(self):
        objs = self.create_multiple(5)
        result = self.list_endpoint("", -1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], objs[-1].id)


class XMLRPCFilterModelTestMixin(XMLRPCModelTestMixin):

    # override these tests due to the way you pass in filters
    def test_list_max_count(self):
        objs = self.create_multiple(5)
        result = self.list_endpoint({'max_count': 2})
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], objs[0].id)

    def test_list_negative_max_count(self):
        objs = self.create_multiple(5)
        result = self.list_endpoint({'max_count': -1})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], objs[-1].id)

    def test_list_named(self):
        obj = self.create_single(name='FOOBARBAZ')
        self.create_multiple(5)
        result = self.list_endpoint({'name__icontains': 'oobarb'})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], obj.id)

    def test_list_named_none(self):
        self.create_multiple(5)
        result = self.list_endpoint({'name__icontains': 'invisible'})
        self.assertEqual(len(result), 0)


class XMLRPCPatchTest(XMLRPCTest, XMLRPCFilterModelTestMixin):
    def setUp(self):
        super(XMLRPCPatchTest, self).setUp()
        self.get_endpoint = self.rpc.patch_get
        self.list_endpoint = self.rpc.patch_list
        self.create_multiple = utils.create_patches

    def create_single(self, **kwargs):
        return utils.create_patches(**kwargs)[0]

    def test_patch_check_get(self):
        patch = self.create_single()
        check = utils.create_check(patch=patch)
        result = self.rpc.patch_check_get(patch.id)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['checks'][0]['id'], check.id)
        self.assertEqual(result['checks'][0]['patch_id'], patch.id)

    def test_patch_get_by_hash(self):
        patch = self.create_single()
        result = self.rpc.patch_get_by_hash(patch.hash)
        self.assertEqual(result['id'], patch.id)


class XMLRPCPersonTest(XMLRPCTest, XMLRPCModelTestMixin):

    def setUp(self):
        super(XMLRPCPersonTest, self).setUp()
        self.get_endpoint = self.rpc.person_get
        self.list_endpoint = self.rpc.person_list
        self.create_single = utils.create_person


class XMLRPCProjectTest(XMLRPCTest, XMLRPCModelTestMixin):

    def setUp(self):
        super(XMLRPCProjectTest, self).setUp()
        self.get_endpoint = self.rpc.project_get
        self.list_endpoint = self.rpc.project_list
        self.create_single = utils.create_project

    def test_list_named(self):
        # project filters by linkname, not name!
        obj = self.create_single(linkname='FOOBARBAZ')
        result = self.list_endpoint('oobarb')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], obj.id)


class XMLRPCStateTest(XMLRPCTest, XMLRPCModelTestMixin):

    def setUp(self):
        super(XMLRPCStateTest, self).setUp()
        self.get_endpoint = self.rpc.state_get
        self.list_endpoint = self.rpc.state_list
        self.create_single = utils.create_state


class XMLRPCCheckTest(XMLRPCTest, XMLRPCFilterModelTestMixin):

    def setUp(self):
        super(XMLRPCCheckTest, self).setUp()
        self.get_endpoint = self.rpc.check_get
        self.list_endpoint = self.rpc.check_list
        self.create_single = utils.create_check

    def test_list_named(self):
        pass

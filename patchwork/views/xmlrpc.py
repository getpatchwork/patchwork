# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
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
#
# Patchwork XMLRPC interface
#

from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from DocXMLRPCServer import XMLRPCDocGenerator
import base64
import sys
import xmlrpclib

from django.core import urlresolvers
from django.contrib.auth import authenticate
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseServerError)
from django.views.decorators.csrf import csrf_exempt

from patchwork.models import Patch, Project, Person, State
from patchwork.views import patch_to_mbox


class PatchworkXMLRPCDispatcher(SimpleXMLRPCDispatcher,
                                XMLRPCDocGenerator):

    server_name = 'Patchwork XML-RPC API'
    server_title = 'Patchwork XML-RPC API v1 Documentation'

    def __init__(self):
        SimpleXMLRPCDispatcher.__init__(self, allow_none=False,
                                        encoding=None)
        XMLRPCDocGenerator.__init__(self)

        def _dumps(obj, *args, **kwargs):
            kwargs['allow_none'] = self.allow_none
            kwargs['encoding'] = self.encoding
            return xmlrpclib.dumps(obj, *args, **kwargs)

        self.dumps = _dumps

        # map of name => (auth, func)
        self.func_map = {}

    def register_function(self, fn, auth_required):
        self.funcs[fn.__name__] = fn  # needed by superclass methods
        self.func_map[fn.__name__] = (auth_required, fn)

    def _user_for_request(self, request):
        auth_header = None

        if 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META.get('HTTP_AUTHORIZATION')
        elif 'Authorization' in request.META:
            auth_header = request.META.get('Authorization')

        if auth_header is None or auth_header == '':
            raise Exception('No authentication credentials given')

        header = auth_header.strip()

        if not header.startswith('Basic '):
            raise Exception('Authentication scheme not supported')

        header = header[len('Basic '):].strip()

        try:
            decoded = base64.decodestring(header)
            username, password = decoded.split(':', 1)
        except:
            raise Exception('Invalid authentication credentials')

        return authenticate(username=username, password=password)

    def _dispatch(self, request, method, params):
        if method not in self.func_map.keys():
            raise Exception('method "%s" is not supported' % method)

        auth_required, fn = self.func_map[method]

        if auth_required:
            user = self._user_for_request(request)
            if not user:
                raise Exception('Invalid username/password')

            params = (user,) + params

        return fn(*params)

    def _marshaled_dispatch(self, request):
        try:
            params, method = xmlrpclib.loads(request.body)

            response = self._dispatch(request, method, params)
            # wrap response in a singleton tuple
            response = (response,)
            response = self.dumps(response, methodresponse=1)
        except xmlrpclib.Fault, fault:
            response = self.dumps(fault)
        except:
            # report exception back to server
            response = self.dumps(
                xmlrpclib.Fault(1, '%s:%s' % (sys.exc_type, sys.exc_value)),
            )

        return response

dispatcher = PatchworkXMLRPCDispatcher()

# XMLRPC view function


@csrf_exempt
def xmlrpc(request):
    if request.method not in ['POST', 'GET']:
        return HttpResponseRedirect(urlresolvers.reverse(
            'patchwork.views.help', kwargs={'path': 'pwclient/'}))

    response = HttpResponse()

    if request.method == 'POST':
        try:
            ret = dispatcher._marshaled_dispatch(request)
        except Exception:
            return HttpResponseServerError()
    else:
        ret = dispatcher.generate_html_documentation()

    response.write(ret)

    return response

# decorator for XMLRPC methods. Setting login_required to true will call
# the decorated function with a non-optional user as the first argument.


def xmlrpc_method(login_required=False):
    def wrap(f):
        dispatcher.register_function(f, login_required)
        return f

    return wrap


# We allow most of the Django field lookup types for remote queries
LOOKUP_TYPES = ['iexact', 'contains', 'icontains', 'gt', 'gte', 'lt',
                'in', 'startswith', 'istartswith', 'endswith',
                'iendswith', 'range', 'year', 'month', 'day', 'isnull']


#######################################################################
# Helper functions
#######################################################################

def project_to_dict(obj):
    """Return a trimmed down dictionary representation of a Project
    object which is OK to send to the client."""
    return {
        'id': obj.id,
        'linkname': obj.linkname,
        'name': obj.name,
    }


def person_to_dict(obj):
    """Return a trimmed down dictionary representation of a Person
    object which is OK to send to the client."""

    # Make sure we don't return None even if the user submitted a patch
    # with no real name.  XMLRPC can't marshall None.
    if obj.name is not None:
        name = obj.name
    else:
        name = obj.email

    return {
        'id': obj.id,
        'email': obj.email,
        'name': name,
        'user': unicode(obj.user).encode('utf-8'),
    }


def patch_to_dict(obj):
    """Return a trimmed down dictionary representation of a Patch
    object which is OK to send to the client."""
    return {
        'id': obj.id,
        'date': unicode(obj.date).encode('utf-8'),
        'filename': obj.filename(),
        'msgid': obj.msgid,
        'name': obj.name,
        'project': unicode(obj.project).encode('utf-8'),
        'project_id': obj.project_id,
        'state': unicode(obj.state).encode('utf-8'),
        'state_id': obj.state_id,
        'archived': obj.archived,
        'submitter': unicode(obj.submitter).encode('utf-8'),
        'submitter_id': obj.submitter_id,
        'delegate': unicode(obj.delegate).encode('utf-8'),
        'delegate_id': max(obj.delegate_id, 0),
        'commit_ref': max(obj.commit_ref, ''),
    }


def bundle_to_dict(obj):
    """Return a trimmed down dictionary representation of a Bundle
    object which is OK to send to the client."""
    return {
        'id': obj.id,
        'name': obj.name,
        'n_patches': obj.n_patches(),
        'public_url': obj.public_url(),
    }


def state_to_dict(obj):
    """Return a trimmed down dictionary representation of a State
    object which is OK to send to the client."""
    return {
        'id': obj.id,
        'name': obj.name,
    }


#######################################################################
# Public XML-RPC methods
#######################################################################

@xmlrpc_method()
def pw_rpc_version():
    """Return Patchwork XML-RPC interface version."""
    return 1


@xmlrpc_method()
def project_list(search_str='', max_count=0):
    """Get a list of projects matching the given filters."""
    try:
        if len(search_str) > 0:
            projects = Project.objects.filter(linkname__icontains=search_str)
        else:
            projects = Project.objects.all()

        if max_count > 0:
            return map(project_to_dict, projects)[:max_count]
        else:
            return map(project_to_dict, projects)
    except Project.DoesNotExist:
        return []


@xmlrpc_method()
def project_get(project_id):
    """Return structure for the given project ID."""
    try:
        project = Project.objects.filter(id=project_id)[0]
        return project_to_dict(project)
    except Project.DoesNotExist:
        return {}


@xmlrpc_method()
def person_list(search_str="", max_count=0):
    """Get a list of Person objects matching the given filters."""
    try:
        if len(search_str) > 0:
            people = (Person.objects.filter(name__icontains=search_str) |
                      Person.objects.filter(email__icontains=search_str))
        else:
            people = Person.objects.all()

        if max_count > 0:
            return map(person_to_dict, people)[:max_count]
        else:
            return map(person_to_dict, people)
    except Person.DoesNotExist:
        return []


@xmlrpc_method()
def person_get(person_id):
    """Return structure for the given person ID."""
    try:
        person = Person.objects.filter(id=person_id)[0]
        return person_to_dict(person)
    except Person.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_list(filt=None):
    """Get a list of patches matching the given filters."""
    if filt is None:
        filt = {}

    try:
        # We allow access to many of the fields.  But, some fields are
        # filtered by raw object so we must lookup by ID instead over
        # XML-RPC.
        ok_fields = [
            'id',
            'name',
            'project_id',
            'submitter_id',
            'delegate_id',
            'archived',
            'state_id',
            'date',
            'commit_ref',
            'hash',
            'msgid',
            'max_count',
        ]

        dfilter = {}
        max_count = 0

        for key in filt:
            parts = key.split('__')
            if parts[0] not in ok_fields:
                # Invalid field given
                return []
            if len(parts) > 1:
                if LOOKUP_TYPES.count(parts[1]) == 0:
                    # Invalid lookup type given
                    return []

            if parts[0] == 'project_id':
                dfilter['project'] = Project.objects.filter(id=filt[key])[0]
            elif parts[0] == 'submitter_id':
                dfilter['submitter'] = Person.objects.filter(id=filt[key])[0]
            elif parts[0] == 'delegate_id':
                dfilter['delegate'] = Person.objects.filter(id=filt[key])[0]
            elif parts[0] == 'state_id':
                dfilter['state'] = State.objects.filter(id=filt[key])[0]
            elif parts[0] == 'max_count':
                max_count = filt[key]
            else:
                dfilter[key] = filt[key]

        patches = Patch.objects.filter(**dfilter)

        if max_count > 0:
            return map(patch_to_dict, patches[:max_count])
        else:
            return map(patch_to_dict, patches)
    except Patch.DoesNotExist:
        return []


@xmlrpc_method()
def patch_get(patch_id):
    """Return structure for the given patch ID."""
    try:
        patch = Patch.objects.filter(id=patch_id)[0]
        return patch_to_dict(patch)
    except Patch.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_get_by_hash(hash):
    """Return structure for the given patch hash."""
    try:
        patch = Patch.objects.filter(hash=hash)[0]
        return patch_to_dict(patch)
    except Patch.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_get_by_project_hash(project, hash):
    """Return structure for the given patch hash."""
    try:
        patch = Patch.objects.filter(project__linkname=project,
                                     hash=hash)[0]
        return patch_to_dict(patch)
    except Patch.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_get_mbox(patch_id):
    """Return mbox string for the given patch ID."""
    try:
        patch = Patch.objects.filter(id=patch_id)[0]
        return patch_to_mbox(patch).as_string(True)
    except Patch.DoesNotExist:
        return ''


@xmlrpc_method()
def patch_get_diff(patch_id):
    """Return diff for the given patch ID."""
    try:
        patch = Patch.objects.filter(id=patch_id)[0]
        return patch.content
    except Patch.DoesNotExist:
        return ''


@xmlrpc_method(login_required=True)
def patch_set(user, patch_id, params):
    """Update a patch with the key,value pairs in params. Only some parameters
       can be set"""
    try:
        ok_params = ['state', 'commit_ref', 'archived']

        patch = Patch.objects.get(id=patch_id)

        if not patch.is_editable(user):
            raise Exception('No permissions to edit this patch')

        for (k, v) in params.iteritems():
            if k not in ok_params:
                continue

            if k == 'state':
                patch.state = State.objects.get(id=v)

            else:
                setattr(patch, k, v)

        patch.save()

        return True

    except Patch.DoesNotExist:
        raise


@xmlrpc_method()
def state_list(search_str='', max_count=0):
    """Get a list of state structures matching the given search string."""
    try:
        if len(search_str) > 0:
            states = State.objects.filter(name__icontains=search_str)
        else:
            states = State.objects.all()

        if max_count > 0:
            return map(state_to_dict, states)[:max_count]
        else:
            return map(state_to_dict, states)
    except State.DoesNotExist:
        return []


@xmlrpc_method()
def state_get(state_id):
    """Return structure for the given state ID."""
    try:
        state = State.objects.filter(id=state_id)[0]
        return state_to_dict(state)
    except State.DoesNotExist:
        return {}

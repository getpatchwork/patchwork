# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import base64
from xmlrpc.server import XMLRPCDocGenerator
import sys

from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from xmlrpc import client as xmlrpc_client
from xmlrpc.server import SimpleXMLRPCDispatcher

from patchwork.models import Check
from patchwork.models import Patch
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import State
from patchwork.views.utils import patch_to_mbox


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
            return xmlrpc_client.dumps(obj, *args, **kwargs)

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
            decoded = base64.b64decode(header.encode('ascii')).decode('ascii')
            username, password = decoded.split(':', 1)
        except ValueError:
            raise Exception('Invalid authentication credentials')

        return authenticate(username=username, password=password)

    def _dispatch(self, request, method, params):
        if method not in list(self.func_map.keys()):
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
            params, method = xmlrpc_client.loads(request.body)

            response = self._dispatch(request, method, params)
            # wrap response in a singleton tuple
            response = (response,)
            response = self.dumps(response, methodresponse=1)
        except xmlrpc_client.Fault as fault:
            response = self.dumps(fault)
        except Exception:  # noqa
            # report exception back to server
            response = self.dumps(
                xmlrpc_client.Fault(
                    1, '%s:%s' % (sys.exc_info()[0], sys.exc_info()[1])),
            )

        return response


dispatcher = PatchworkXMLRPCDispatcher()

# XMLRPC view function


@csrf_exempt
def xmlrpc(request):
    if request.method not in ['POST', 'GET']:
        return HttpResponseRedirect(reverse('project-list'))

    response = HttpResponse()

    if request.method == 'POST':
        try:
            ret = dispatcher._marshaled_dispatch(request)
        except Exception:  # noqa
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
    """Serialize a project object.

    Return a trimmed down dictionary representation of a Project
    object which is safe to send to the client. For example:

    {
        'id': 1,
        'linkname': 'my-project',
        'name': 'My Project',
    }

    Args:
        Project object to serialize.

    Returns:
        Serialized Project object.
    """
    return {
        'id': obj.id,
        'linkname': obj.linkname,
        'name': obj.name,
    }


def person_to_dict(obj):
    """Serialize a person object.

    Return a trimmed down dictionary representation of a Person
    object which is safe to send to the client. For example:

    {
        'id': 1,
        'email': 'joe.bloggs@example.com',
        'name': 'Joe Bloggs',
        'user': None,
    }

    Args:
        Person object to serialize.

    Returns:
        Serialized Person object.
    """

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
        'user': str(obj.user).encode('utf-8'),
    }


def patch_to_dict(obj):
    """Serialize a patch object.

    Return a trimmed down dictionary representation of a Patch
    object which is safe to send to the client. For example:

    {
        'id': 1
        'date': '2000-12-31 00:11:22',
        'filename': 'Fix-all-the-bugs.patch',
        'msgid': '<BLU438-SMTP36690BBDD2CE71A7138B082511A@phx.gbl>',
        'name': "Fix all the bugs",
        'project': 'my-project',
        'project_id': 1,
        'state': 'New',
        'state_id': 1,
        'archived': False,
        'submitter': 'Joe Bloggs <joe.bloggs at example.com>',
        'submitter_id': 1,
        'delegate': 'admin',
        'delegate_id': 1,
        'commit_ref': '',
        'hash': '',
    }

    Args:
        Patch object to serialize.

    Returns:
        Serialized Patch object.
    """
    return {
        'id': obj.id,
        'date': str(obj.date).encode('utf-8'),
        'filename': obj.filename,
        'msgid': obj.msgid,
        'name': obj.name,
        'project': str(obj.project).encode('utf-8'),
        'project_id': obj.project_id,
        'state': str(obj.state).encode('utf-8'),
        'state_id': obj.state_id,
        'archived': obj.archived,
        'submitter': str(obj.submitter).encode('utf-8'),
        'submitter_id': obj.submitter_id,
        'delegate': str(obj.delegate).encode('utf-8'),
        'delegate_id': obj.delegate_id or 0,
        'commit_ref': obj.commit_ref or '',
        'hash': obj.hash or '',
    }


def state_to_dict(obj):
    """Serialize a state object.

    Return a trimmed down dictionary representation of a State
    object which is safe to send to the client. For example:

    {
        'id': 1,
        'name': 'New',
    }

    Args:
        State object to serialize.

    Returns:
        Serialized State object.
    """
    return {
        'id': obj.id,
        'name': obj.name,
    }


def check_to_dict(obj):
    """Return a trimmed down dictionary representation of a Check
    object which is OK to send to the client."""
    return {
        'id': obj.id,
        'date': str(obj.date).encode('utf-8'),
        'patch': str(obj.patch).encode('utf-8'),
        'patch_id': obj.patch_id,
        'user': str(obj.user).encode('utf-8'),
        'user_id': obj.user_id,
        'state': obj.get_state_display(),
        'target_url': obj.target_url,
        'description': obj.description,
        'context': obj.context,
    }


def patch_check_to_dict(obj):
    """Return a combined patch check."""
    return {
        'state': obj.combined_check_state,
        'total': len(obj.checks),
        'checks': [check_to_dict(check) for check in obj.checks]
    }


#######################################################################
# Public XML-RPC methods
#######################################################################

def _get_objects(serializer, objects, max_count):
    if max_count > 0:
        return [serializer(x) for x in objects[:max_count]]
    elif max_count < 0:
        min_count = objects.count() + max_count
        return [serializer(x) for x in objects[min_count:]]
    else:
        return [serializer(x) for x in objects]


@xmlrpc_method()
def pw_rpc_version():
    """Return Patchwork XML-RPC interface version.

    The API is versioned separately from patchwork itself. The API
    version only changes when the API itself changes. As these changes
    can include the removal or modification of methods, it is highly
    recommended that one first test the API version for compatibility
    before making method calls.

    History:

        1.0.0: Patchwork 1.0 release
        1.1.0: ???
        1.2.0: ???
        1.3.0: Add support for negative indexing of Checks

    Returns:
        Version of the API.
    """
    return (1, 3, 0)


@xmlrpc_method()
def project_list(search_str=None, max_count=0):
    """List projects matching a given linkname filter.

    Filter projects by linkname. Projects are compared to the search
    string via a case-insensitive containment test, a.k.a. a partial
    match.

    Args:
        search_str: The string to compare project names against. If
            blank, all projects will be returned.
        max_count (int): The maximum number of projects to return.

    Returns:
        A serialized list of projects matching filter, if any. A list
        of all projects if no filter given.
    """
    if search_str:
        projects = Project.objects.filter(linkname__icontains=search_str)
    else:
        projects = Project.objects.all()

    return _get_objects(project_to_dict, projects, max_count)


@xmlrpc_method()
def project_get(project_id):
    """Get a project by its ID.

    Retrieve a project matching a given project ID, if any exists.

    Args:
        project_id (int): The ID of the project to retrieve.

    Returns:
        The serialized project matching the ID, if any, else an empty
        dict.
    """
    try:
        project = Project.objects.get(id=project_id)
        return project_to_dict(project)
    except Project.DoesNotExist:
        return {}


@xmlrpc_method()
def person_list(search_str=None, max_count=0):
    """List persons matching a given name or email filter.

    Filter persons by name and email. Persons are compared to the
    search string via a case-insensitive containment test, a.k.a. a
    partial match.

    Args:
        search_str: The string to compare person names or emails
            against. If blank, all persons will be returned.
        max_count (int): The maximum number of persons to return.

    Returns:
        A serialized list of persons matching filter, if any. A list
        of all persons if no filter given.
    """
    if search_str:
        people = (Person.objects.filter(name__icontains=search_str) |
                  Person.objects.filter(email__icontains=search_str))
    else:
        people = Person.objects.all()

    return _get_objects(person_to_dict, people, max_count)


@xmlrpc_method()
def person_get(person_id):
    """Get a person by its ID.

    Retrieve a person matching a given person ID, if any exists.

    Args:
        person_id (int): The ID of the person to retrieve.

    Returns:
        The serialized person matching the ID, if any, else an empty
        dict.
    """
    try:
        person = Person.objects.get(id=person_id)
        return person_to_dict(person)
    except Person.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_list(filt=None):
    """List patches matching all of a given set of filters.

    Filter patches by one or more of the below fields:

     * id
     * name
     * project_id
     * submitter_id
     * delegate_id
     * archived
     * state_id
     * date
     * commit_ref
     * hash
     * msgid

    It is also possible to specify the number of patches returned via
    a ``max_count`` filter.

     * max_count

    With the exception of ``max_count``, the specified field of the
    patches are compared to the search string using a provided
    field lookup type, which can be one of:

     * iexact
     * contains
     * icontains
     * gt
     * gte
     * lt
     * in
     * startswith
     * istartswith
     * endswith
     * iendswith
     * range
     * year
     * month
     * day
     * isnull

    Please refer to the Django documentation for more information on
    these field lookup types.

    An example filter would look like so:

    {
        'name__icontains': 'Joe Bloggs',
        'max_count': 1,
    }

    Args:
        filt (dict): The filters specifying the field to compare, the
            lookup type and the value to compare against. Keys are of
            format ``[FIELD_NAME]`` or ``[FIELD_NAME]__[LOOKUP_TYPE]``.
            Example: ``name__icontains``. Values are plain strings to
            compare against.

    Returns:
        A serialized list of patches matching filters, if any. A list
        of all patches if no filter given.
    """
    if filt is None:
        filt = {}

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
        if len(parts) > 1 and LOOKUP_TYPES.count(parts[1]) == 0:
            # Invalid lookup type given
            return []

        try:
            if parts[0] == 'project_id':
                dfilter['project'] = Project.objects.get(id=filt[key])
            elif parts[0] == 'submitter_id':
                dfilter['submitter'] = Person.objects.get(id=filt[key])
            elif parts[0] == 'delegate_id':
                dfilter['delegate'] = Person.objects.get(id=filt[key])
            elif parts[0] == 'state_id':
                dfilter['state'] = State.objects.get(id=filt[key])
            elif parts[0] == 'max_count':
                max_count = filt[key]
            else:
                dfilter[key] = filt[key]
        except (Project.DoesNotExist, Person.DoesNotExist, State.DoesNotExist):
            # Invalid Project, Person or State given
            return []

    patches = Patch.objects.filter(**dfilter)

    # Only extract the relevant fields. This saves a big db load as we
    # no longer fetch content/headers/etc for potentially every patch
    # in a project.
    patches = patches.defer('content', 'headers', 'diff')

    return _get_objects(patch_to_dict, patches, max_count)


@xmlrpc_method()
def patch_get(patch_id):
    """Get a patch by its ID.

    Retrieve a patch matching a given patch ID, if any exists.

    Args:
        patch_id (int): The ID of the patch to retrieve

    Returns:
        The serialized patch matching the ID, if any, else an empty
        dict.
    """
    try:
        patch = Patch.objects.get(id=patch_id)
        return patch_to_dict(patch)
    except Patch.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_get_by_hash(hash):  # noqa
    """Get a patch by its hash.

    Retrieve a patch matching a given patch hash, if any exists.

    Args:
        hash: The hash of the patch to retrieve

    Returns:
        The serialized patch matching the hash, if any, else an empty
        dict.
    """
    try:
        patch = Patch.objects.get(hash=hash)
        return patch_to_dict(patch)
    except Patch.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_get_by_project_hash(project, hash):
    """Get a patch by its project and hash.

    Retrieve a patch matching a given project and patch hash, if any
    exists.

    Args:
        project (str): The project of the patch to retrieve.
        hash: The hash of the patch to retrieve.

    Returns:
        The serialized patch matching both the project and the hash,
        if any, else an empty dict.
    """
    try:
        patch = Patch.objects.get(project__linkname=project,
                                  hash=hash)
        return patch_to_dict(patch)
    except Patch.DoesNotExist:
        return {}


@xmlrpc_method()
def patch_get_mbox(patch_id):
    """Get a patch by its ID in mbox format.

    Retrieve a patch matching a given patch ID, if any exists, and
    return in mbox format.

    Args:
        patch_id (int): The ID of the patch to retrieve.

    Returns:
        The serialized patch matching the ID, if any, in mbox format,
        else an empty string.
    """
    try:
        patch = Patch.objects.get(id=patch_id)
        return patch_to_mbox(patch)
    except Patch.DoesNotExist:
        return ''


@xmlrpc_method()
def patch_get_diff(patch_id):
    """Get a patch by its ID in diff format.

    Retrieve a patch matching a given patch ID, if any exists, and
    return in diff format.

    Args:
        patch_id (int): The ID of the patch to retrieve.

    Returns:
        The serialized patch matching the ID, if any, in diff format,
        else an empty string.
    """
    try:
        patch = Patch.objects.get(id=patch_id)
        return patch.diff
    except Patch.DoesNotExist:
        return ''


@xmlrpc_method(login_required=True)
def patch_set(user, patch_id, params):
    """Set fields of a patch.

    Modify a patch matching a given patch ID, if any exists, and using
    the provided ``key,value`` pairs. Only the following parameters may
    be set:

     * state
     * commit_ref
     * archived

    Any other field will be rejected.

    **NOTE:** Authentication is required for this method.

    Args:
        user (User): The user making the request. This will be
            populated from HTTP Basic Auth.
        patch_id (int): The ID of the patch to modify.
        params (dict): A dictionary of keys corresponding to patch
            object fields and the values that said fields should be
            set to.

    Returns:
        True, if successful else raise exception.

    Raises:
        Exception: User did not have necessary permissions to edit this
            patch
        Patch.DoesNotExist: The patch did not exist.
    """
    ok_params = ['state', 'commit_ref', 'archived']

    patch = Patch.objects.get(id=patch_id)

    if not patch.is_editable(user):
        raise Exception('No permissions to edit this patch')

    for (k, v) in params.items():
        if k not in ok_params:
            continue

        if k == 'state':
            patch.state = State.objects.get(id=v)

        else:
            setattr(patch, k, v)

    patch.save()

    return True


@xmlrpc_method()
def state_list(search_str=None, max_count=0):
    """List states matching a given name filter.

    Filter states by name. States are compared to the search string
    via a case-insensitive containment test, a.k.a. a partial match.

    Args:
        search_str: The string to compare state names against. If
            blank, all states will be returned.
        max_count (int): The maximum number of states to return.

    Returns:
        A serialized list of states matching filter, if any. A list
        of all states if no filter given.
    """
    if search_str:
        states = State.objects.filter(name__icontains=search_str)
    else:
        states = State.objects.all()

    return _get_objects(state_to_dict, states, max_count)


@xmlrpc_method()
def state_get(state_id):
    """Get a state by its ID.

    Retrieve a state matching a given state ID, if any exists.

    Args:
        state_id: The ID of the state to retrieve.

    Returns:
        The serialized state matching the ID, if any, else an empty
        dict.
    """
    try:
        state = State.objects.get(id=state_id)
        return state_to_dict(state)
    except State.DoesNotExist:
        return {}


@xmlrpc_method()
def check_list(filt=None):
    """List checks matching all of a given set of filters.

    Filter checks by one or more of the below fields:

     * id
     * user
     * project_id
     * patch_id

    It is also possible to specify the number of patches returned via
    a ``max_count`` filter.

     * max_count

    With the exception of ``max_count``, the specified field of the
    patches are compared to the search string using a provided
    field lookup type, which can be one of:

     * iexact
     * contains
     * icontains
     * gt
     * gte
     * lt
     * in
     * startswith
     * istartswith
     * endswith
     * iendswith
     * range
     * year
     * month
     * day
     * isnull

    Please refer to the Django documentation for more information on
    these field lookup types.

    An example filter would look like so:

    {
        'user__icontains': 'Joe Bloggs',
        'max_count': 1,
    }

    Args:
        filt (dict): The filters specifying the field to compare, the
            lookup type and the value to compare against. Keys are of
            format ``[FIELD_NAME]`` or ``[FIELD_NAME]__[LOOKUP_TYPE]``.
            Example: ``name__icontains``. Values are plain strings to
            compare against.

    Returns:
        A serialized list of Checks matching filters, if any. A list
        of all Checks if no filter given.
    """
    if filt is None:
        filt = {}

    # We allow access to many of the fields. But, some fields are
    # filtered by raw object so we must lookup by ID instead over
    # XML-RPC.
    ok_fields = [
        'id',
        'user',
        'project_id',
        'patch_id',
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

        if parts[0] == 'user_id':
            dfilter['user'] = Person.objects.filter(id=filt[key])[0]
        if parts[0] == 'project_id':
            dfilter['patch__project'] = Project.objects.filter(
                id=filt[key])[0]
        elif parts[0] == 'patch_id':
            dfilter['patch'] = Patch.objects.filter(id=filt[key])[0]
        elif parts[0] == 'max_count':
            max_count = filt[key]
        else:
            dfilter[key] = filt[key]

    checks = Check.objects.filter(**dfilter)

    return _get_objects(check_to_dict, checks, max_count)


@xmlrpc_method()
def check_get(check_id):
    """Get a check by its ID.

    Retrieve a check matching a given check ID, if any exists.

    Args:
        check_id (int): The ID of the check to retrieve

    Returns:
        The serialized check matching the ID, if any, else an empty
        dict.
    """
    try:
        check = Check.objects.get(id=check_id)
        return check_to_dict(check)
    except Check.DoesNotExist:
        return {}


@xmlrpc_method(login_required=True)
def check_create(user, patch_id, context, state, target_url="",
                 description=""):
    """Add a Check to a patch.

    **NOTE:** Authentication is required for this method.

    Args:
        patch_id (id): The ID of the patch to create the check against.
        context: Type of test or system that generated this check.
        state: "pending", "success", "warning", or "fail"
        target_url: Link to artifact(s) relating to this check.
        description: A brief description of the check.

    Returns:
        True, if successful else raise exception.
    """
    patch = Patch.objects.get(id=patch_id)
    if not patch.is_editable(user):
        raise Exception('No permissions to edit this patch')
    for state_val, state_str in Check.STATE_CHOICES:
        if state == state_str:
            state = state_val
            break
    else:
        raise Exception("Invalid check state: %s" % state)
    Check.objects.create(patch=patch, context=context, state=state, user=user,
                         target_url=target_url, description=description)
    return True


@xmlrpc_method()
def patch_check_get(patch_id):
    """Get a patch's combined checks by its ID.

    Retrieve a patch's combined checks for the patch matching a given
    patch ID, if any exists.

    Args:
        patch_id (int): The ID of the patch to retrieve checks for

    Returns:
        The serialized combined patch checks matching the ID, if any,
        else an empty dict.
    """
    try:
        patch = Patch.objects.get(id=patch_id)
        return patch_check_to_dict(patch)
    except Patch.DoesNotExist:
        return {}

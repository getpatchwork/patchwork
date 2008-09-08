# Patchwork - automated patch tracking system
# Copyright (C) 2008 Nate Case <ncase@xes-inc.com>
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
# The XML-RPC interface provides a watered down, read-only interface to
# the Patchwork database.  It's intended to be safe to export to the public
# Internet.  A small subset of the object data is included, and the type
# of requests/queries you can do is limited by the methods
# that we export.

from patchwork.models import Patch, Project, Person, Bundle, State

# We allow most of the Django field lookup types for remote queries
LOOKUP_TYPES = ["iexact", "contains", "icontains", "gt", "gte", "lt",
                "in", "startswith", "istartswith", "endswith",
                "iendswith", "range", "year", "month", "day", "isnull" ]

#######################################################################
# Helper functions
#######################################################################

def project_to_dict(obj):
    """Return a trimmed down dictionary representation of a Project
    object which is OK to send to the client."""
    return \
        {
         'id'           : obj.id,
         'linkname'     : obj.linkname,
         'name'         : obj.name,
        }

def person_to_dict(obj):
    """Return a trimmed down dictionary representation of a Person
    object which is OK to send to the client."""
    return \
        {
         'id'           : obj.id,
         'email'        : obj.email,
         'name'         : obj.name,
         'user'         : str(obj.user),
        }

def patch_to_dict(obj):
    """Return a trimmed down dictionary representation of a Patch
    object which is OK to send to the client."""
    return \
        {
         'id'           : obj.id,
         'date'         : str(obj.date),
         'filename'     : obj.filename(),
         'msgid'        : obj.msgid,
         'name'         : obj.name,
         'project'      : str(obj.project),
         'project_id'   : obj.project_id,
         'state'        : str(obj.state),
         'state_id'     : obj.state_id,
         'submitter'    : str(obj.submitter),
         'submitter_id' : obj.submitter_id,
         'delegate'     : str(obj.delegate),
         'delegate_id'  : max(obj.delegate_id, 0),
         'commit_ref'   : max(obj.commit_ref, ''),
        }

def bundle_to_dict(obj):
    """Return a trimmed down dictionary representation of a Bundle
    object which is OK to send to the client."""
    return \
        {
         'id'           : obj.id,
         'name'         : obj.name,
         'n_patches'    : obj.n_patches(),
         'public_url'   : obj.public_url(),
        }

def state_to_dict(obj):
    """Return a trimmed down dictionary representation of a State
    object which is OK to send to the client."""
    return \
        {
         'id'           : obj.id,
         'name'         : obj.name,
        }

#######################################################################
# Public XML-RPC methods
#######################################################################

def pw_rpc_version():
    """Return Patchwork XML-RPC interface version."""
    return 1

def project_list(search_str="", max_count=0):
    """Get a list of projects matching the given filters."""
    try:
        if len(search_str) > 0:
            projects = Project.objects.filter(linkname__icontains = search_str)
        else:
            projects = Project.objects.all()

        if max_count > 0:
            return map(project_to_dict, projects)[:max_count]
        else:
            return map(project_to_dict, projects)
    except:
        return []

def project_get(project_id):
    """Return structure for the given project ID."""
    try:
        project = Project.objects.filter(id = project_id)[0]
        return project_to_dict(project)
    except:
        return {}

def person_list(search_str="", max_count=0):
    """Get a list of Person objects matching the given filters."""
    try:
        if len(search_str) > 0:
            people = (Person.objects.filter(name__icontains = search_str) |
                Person.objects.filter(email__icontains = search_str))
        else:
            people = Person.objects.all()

        if max_count > 0:
            return map(person_to_dict, people)[:max_count]
        else:
            return map(person_to_dict, people)

    except:
        return []

def person_get(person_id):
    """Return structure for the given person ID."""
    try:
        person = Person.objects.filter(id = person_id)[0]
        return person_to_dict(person)
    except:
        return {}

def patch_list(filter={}):
    """Get a list of patches matching the given filters."""
    try:
        # We allow access to many of the fields.  But, some fields are
        # filtered by raw object so we must lookup by ID instead over
        # XML-RPC.
        ok_fields = [
            "id",
            "name",
            "project_id",
            "submitter_id",
            "delegate_id",
            "state_id",
            "date",
            "commit_ref",
            "hash",
            "msgid",
            "name",
            "max_count",
            ]

        dfilter = {}
        max_count = 0

        for key in filter:
            parts = key.split("__")
            if ok_fields.count(parts[0]) == 0:
                # Invalid field given
                return []
            if len(parts) > 1:
                if LOOKUP_TYPES.count(parts[1]) == 0:
                    # Invalid lookup type given
                    return []

            if parts[0] == 'project_id':
                dfilter['project'] = Project.objects.filter(id =
                                        filter[key])[0]
            elif parts[0] == 'submitter_id':
                dfilter['submitter'] = Person.objects.filter(id =
                                        filter[key])[0]
            elif parts[0] == 'state_id':
                dfilter['state'] = State.objects.filter(id =
                                        filter[key])[0]
            elif parts[0] == 'max_count':
                max_count = filter[key]
            else:
                dfilter[key] = filter[key]

        patches = Patch.objects.filter(**dfilter)

        if max_count > 0:
            return map(patch_to_dict, patches)[:max_count]
        else:
            return map(patch_to_dict, patches)

    except:
        return []

def patch_get(patch_id):
    """Return structure for the given patch ID."""
    try:
        patch = Patch.objects.filter(id = patch_id)[0]
        return patch_to_dict(patch)
    except:
        return {}

def patch_get_mbox(patch_id):
    """Return mbox string for the given patch ID."""
    try:
        patch = Patch.objects.filter(id = patch_id)[0]
        return patch.mbox().as_string()
    except:
        return ""

def patch_get_diff(patch_id):
    """Return diff for the given patch ID."""
    try:
        patch = Patch.objects.filter(id = patch_id)[0]
        return patch.content
    except:
        return ""

def state_list(search_str="", max_count=0):
    """Get a list of state structures matching the given search string."""
    try:
        if len(search_str) > 0:
            states = State.objects.filter(name__icontains = search_str)
        else:
            states = State.objects.all()

        if max_count > 0:
            return map(state_to_dict, states)[:max_count]
        else:
            return map(state_to_dict, states)
    except:
        return []

def state_get(state_id):
    """Return structure for the given state ID."""
    try:
        state = State.objects.filter(id = state_id)[0]
        return state_to_dict(state)
    except:
        return {}

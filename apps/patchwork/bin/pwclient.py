#!/usr/bin/env python
#
# Patchwork command line client
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

import os
import sys
import xmlrpclib
import getopt
import string
import tempfile
import subprocess

# Default Patchwork remote XML-RPC server URL
# This script will check the PW_XMLRPC_URL environment variable
# for the URL to access.  If that is unspecified, it will fallback to
# the hardcoded default value specified here.
DEFAULT_URL = "http://patchwork:80/xmlrpc/"

PW_XMLRPC_URL = os.getenv("PW_XMLRPC_URL")
if not PW_XMLRPC_URL:
    PW_XMLRPC_URL = DEFAULT_URL

class Filter:
    """Filter for selecting patches."""
    def __init__(self):
        # These fields refer to specific objects, so they are special
        # because we have to resolve them to IDs before passing the
        # filter to the server
        self.state = ""
        self.project = ""

        # The dictionary that gets passed to via XML-RPC
        self.d = {}

    def add(self, field, value):
        if field == 'state':
            self.state = value
        elif field == 'project':
            self.project = value
        else:
            # OK to add directly
            self.d[field] = value

    def resolve_ids(self, rpc):
        """Resolve State, Project, and Person IDs based on filter strings."""
        if self.state != "":
            id = state_id_by_name(rpc, self.state)
            if id == 0:
                sys.stderr.write("Note: No State found matching %s*, " \
                                 "ignoring filter\n" % self.state)
            else:
                self.d['state_id'] = id

        if self.project != "":
            id = project_id_by_name(rpc, self.project)
            if id == 0:
                sys.stderr.write("Note: No Project found matching %s, " \
                                 "ignoring filter\n" % self.project)
            else:
                self.d['project_id'] = id

    def __str__(self):
        """Return human-readable description of the filter."""
        return str(self.d)

def usage():
    sys.stderr.write("Usage: %s <action> [options]\n\n" % \
                        (os.path.basename(sys.argv[0])))
    sys.stderr.write("Where <action> is one of:\n")
    sys.stderr.write(
"""        apply <ID>    : Apply a patch (in the current dir, using -p1)
        get <ID>      : Download a patch and save it locally
        projects      : List all projects
        states        : Show list of potential patch states
        list [str]    : List patches, using the optional filters specified
                        below and an optional substring to search for patches
                        by name
        search [str]  : Same as 'list'
        view <ID>     : View a patch\n""")
    sys.stderr.write("""\nFilter options for 'list' and 'search':
        -s <state>    : Filter by patch state (e.g., 'New', 'Accepted', etc.)
        -p <project>  : Filter by project name (see 'projects' for list)
        -w <who>      : Filter by submitter (name, e-mail substring search)
        -d <who>      : Filter by delegate (name, e-mail substring search)
        -n <max #>    : Restrict number of results\n""")
    sys.exit(1)

def project_id_by_name(rpc, linkname):
    """Given a project short name, look up the Project ID."""
    if len(linkname) == 0:
        return 0
    # The search requires - instead of _
    search = linkname.replace("_", "-")
    projects = rpc.project_list(search, 0)
    for project in projects:
        if project['linkname'].replace("_", "-") == search:
            return project['id']
    return 0

def state_id_by_name(rpc, name):
    """Given a partial state name, look up the state ID."""
    if len(name) == 0:
        return 0
    states = rpc.state_list(name, 0)
    for state in states:
        if state['name'].lower().startswith(name.lower()):
            return state['id']
    return 0

def person_ids_by_name(rpc, name):
    """Given a partial name or email address, return a list of the
    person IDs that match."""
    if len(name) == 0:
        return []
    people = rpc.person_list(name, 0)
    return map(lambda x: x['id'], people)

def list_patches(patches):
    """Dump a list of patches to stdout."""
    print("%-5s %-12s %s" % ("ID", "State", "Name"))
    print("%-5s %-12s %s" % ("--", "-----", "----"))
    for patch in patches:
        print("%-5d %-12s %s" % (patch['id'], patch['state'], patch['name']))

def action_list(rpc, filter, submitter_str, delegate_str):
    filter.resolve_ids(rpc)

    if submitter_str != "":
        ids = person_ids_by_name(rpc, submitter_str)
        if len(ids) == 0:
            sys.stderr.write("Note: Nobody found matching *%s*\n", \
                             submitter_str)
        else:
            for id in ids:
                person = rpc.person_get(id)
                print "Patches submitted by %s <%s>:" % \
                        (person['name'], person['email'])
                f = filter
                f.add("submitter_id", id)
                patches = rpc.patch_list(f.d)
                list_patches(patches)
        return

    if delegate_str != "":
        ids = person_ids_by_name(rpc, delegate_str)
        if len(ids) == 0:
            sys.stderr.write("Note: Nobody found matching *%s*\n", \
                             delegate_str)
        else:
            for id in ids:
                person = rpc.person_get(id)
                print "Patches delegated to %s <%s>:" % \
                        (person['name'], person['email'])
                f = filter
                f.add("delegate_id", id)
                patches = rpc.patch_list(f.d)
                list_patches(patches)
        return

    patches = rpc.patch_list(filter.d)
    list_patches(patches)

def action_projects(rpc):
    projects = rpc.project_list("", 0)
    print("%-5s %-24s %s" % ("ID", "Name", "Description"))
    print("%-5s %-24s %s" % ("--", "----", "-----------"))
    for project in projects:
        print("%-5d %-24s %s" % (project['id'], \
                project['linkname'].replace("_", "-"), \
                project['name']))

def action_states(rpc):
    states = rpc.state_list("", 0)
    print("%-5s %s" % ("ID", "Name"))
    print("%-5s %s" % ("--", "----"))
    for state in states:
        print("%-5d %s" % (state['id'], state['name']))

def action_get(rpc, patch_id):
    patch = rpc.patch_get(patch_id)
    s = rpc.patch_get_mbox(patch_id)

    if patch == {} or len(s) == 0:
        sys.stderr.write("Unable to get patch %d\n" % patch_id)
        sys.exit(1)

    base_fname = fname = os.path.basename(patch['filename'])
    i = 0
    while os.path.exists(fname):
        fname = "%s.%d" % (base_fname, i)
        i += 1

    try:
        f = open(fname, "w")
    except:
        sys.stderr.write("Unable to open %s for writing\n" % fname)
        sys.exit(1)

    try:
        f.write(s)
        f.close()
        print "Saved patch to %s" % fname
    except:
        sys.stderr.write("Failed to write to %s\n" % fname)
        sys.exit(1)

def action_apply(rpc, patch_id):
    patch = rpc.patch_get(patch_id)
    if patch == {}:
        sys.stderr.write("Error getting information on patch ID %d\n" % \
                         patch_id)
        sys.exit(1)
    print "Applying patch #%d to current directory" % patch_id
    print "Description: %s" % patch['name']
    s = rpc.patch_get_mbox(patch_id)
    if len(s) > 0:
        proc = subprocess.Popen(['patch', '-p1'], stdin = subprocess.PIPE)
        proc.communicate(s)
    else:
        sys.stderr.write("Error: No patch content found\n")
        sys.exit(1)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[2:], 's:p:w:d:n:')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    if len(sys.argv) < 2:
        usage()

    action = sys.argv[1].lower()

    filt = Filter()
    submitter_str = ""
    delegate_str = ""

    for name, value in opts:
        if name == '-s':
            filt.add("state", value)
        elif name == '-p':
            filt.add("project", value)
        elif name == '-w':
            submitter_str = value
        elif name == '-d':
            delegate_str = value
        elif name == '-n':
            try:
                filt.add("max_count", int(value))
            except:
                sys.stderr.write("Invalid maximum count '%s'\n" % value)
                usage()
        else:
            sys.stderr.write("Unknown option '%s'\n" % name)
            usage()

    if len(args) > 1:
        sys.stderr.write("Too many arguments specified\n")
        usage()

    try:
        rpc = xmlrpclib.Server(PW_XMLRPC_URL)
    except:
        sys.stderr.write("Unable to connect to %s\n" % PW_XMLRPC_URL)
        sys.exit(1)

    if action == 'list' or action == 'search':
        if len(args) > 0:
            filt.add("name__icontains", args[0])
        action_list(rpc, filt, submitter_str, delegate_str)

    elif action.startswith('project'):
        action_projects(rpc)

    elif action.startswith('state'):
        action_states(rpc)

    elif action == 'view':
        try:
            patch_id = int(args[0])
        except:
            sys.stderr.write("Invalid patch ID given\n")
            sys.exit(1)

        s = rpc.patch_get_mbox(patch_id)
        if len(s) > 0:
            print s

    elif action == 'get' or action == 'save':
        try:
            patch_id = int(args[0])
        except:
            sys.stderr.write("Invalid patch ID given\n")
            sys.exit(1)

        action_get(rpc, patch_id)

    elif action == 'apply':
        try:
            patch_id = int(args[0])
        except:
            sys.stderr.write("Invalid patch ID given\n")
            sys.exit(1)

        action_apply(rpc, patch_id)

    else:
        sys.stderr.write("Unknown action '%s'\n" % action)
        usage()

if __name__ == "__main__":
    main()

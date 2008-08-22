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

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.conf import settings
import django.oldforms as oldforms

import re
import datetime, time
import string
import random
from email.mime.text import MIMEText
import email.utils

class Person(models.Model):
    email = models.CharField(max_length=255, unique = True)
    name = models.CharField(max_length=255, null = True)
    user = models.ForeignKey(User, null = True)

    def __str__(self):
        if self.name:
            return '%s <%s>' % (self.name, self.email)
        else:
            return self.email

    def link_to_user(self, user):
        self.name = user.get_profile().name()
        self.user = user

    class Meta:
        verbose_name_plural = 'People'

class Project(models.Model):
    linkname = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, unique=True)
    listid = models.CharField(max_length=255, unique=True)
    listemail = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique = True)
    primary_project = models.ForeignKey(Project, null = True)
    maintainer_projects = models.ManyToManyField(Project,
            related_name = 'maintainer_project')
    send_email = models.BooleanField(default = False,
            help_text = 'Selecting this option allows patchwork to send ' +
                'email on your behalf')
    patches_per_page = models.PositiveIntegerField(default = 100,
            null = False, blank = False,
            help_text = 'Number of patches to display per page')

    def name(self):
        if self.user.first_name or self.user.last_name:
	    names = filter(bool, [self.user.first_name, self.user.last_name])
	    return ' '.join(names)
        return self.user.username

    def contributor_projects(self):
        submitters = Person.objects.filter(user = self.user)
        return Project.objects \
            .filter(id__in = \
                    Patch.objects.filter(
                        submitter__in = submitters) \
                    .values('project_id').query)


    def sync_person(self):
        pass

    def n_todo_patches(self):
        return self.todo_patches().count()

    def todo_patches(self, project = None):

        # filter on project, if necessary
        if project:
            qs = Patch.objects.filter(project = project)
        else:
            qs = Patch.objects

        qs = qs.filter(archived = False) \
             .filter(delegate = self.user) \
             .filter(state__in = \
                     State.objects.filter(action_required = True) \
                         .values('pk').query)
        return qs

    def save(self):
	super(UserProfile, self).save()
	people = Person.objects.filter(email = self.user.email)
	if not people:
	    person = Person(email = self.user.email,
		    name = self.name(), user = self.user)
            person.save()
	else:
	    for person in people:
		 person.user = self.user
		 person.save()

    def __str__(self):
        return self.name()

def _confirm_key():
    allowedchars = string.ascii_lowercase + string.digits
    str = ''
    for i in range(1, 32):
        str += random.choice(allowedchars)
    return str;

class UserPersonConfirmation(models.Model):
    user = models.ForeignKey(User)
    email = models.CharField(max_length = 200)
    key = models.CharField(max_length = 32, default = _confirm_key)
    date = models.DateTimeField(default=datetime.datetime.now)
    active = models.BooleanField(default = True)

    def confirm(self):
	if not self.active:
	    return
        person = None
        try:
            person = Person.objects.get(email = self.email)
        except Exception:
            pass
        if not person:
            person = Person(email = self.email)

        person.link_to_user(self.user)
        person.save()
        self.active = False

class State(models.Model):
    name = models.CharField(max_length = 100)
    ordering = models.IntegerField(unique = True)
    action_required = models.BooleanField(default = True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['ordering']

class HashField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, algorithm = 'sha1', *args, **kwargs):
        self.algorithm = algorithm
        try:
            import hashlib
            self.hashlib = True
        except ImportError:
            self.hashlib = False
            if algorithm == 'sha1':
                import sha
                self.hash_constructor = sha.new
            elif algorithm == 'md5':
                import md5
                self.hash_constructor = md5.new
            else:
                raise NameError("Unknown algorithm '%s'" % algorithm)
            
        super(HashField, self).__init__(*args, **kwargs)

    def db_type(self):
        if self.hashlib:
            n_bytes = len(hashlib.new(self.algorithm).digest())
        else:
            n_bytes = len(self.hash_constructor().digest())
	if settings.DATABASE_ENGINE == 'postgresql':
	    return 'bytea'
	elif settings.DATABASE_ENGINE == 'mysql':
	    return 'binary(%d)' % n_bytes

    def to_python(self, value):
        return value

    def get_db_prep_save(self, value):
        return ''.join(map(lambda x: '\\%03o' % ord(x), value))

    def get_manipulator_field_objs(self):
        return [oldforms.TextField]

class Patch(models.Model):
    project = models.ForeignKey(Project)
    msgid = models.CharField(max_length=255, unique = True)
    name = models.CharField(max_length=255)
    date = models.DateTimeField(default=datetime.datetime.now)
    submitter = models.ForeignKey(Person)
    delegate = models.ForeignKey(User, blank = True, null = True)
    state = models.ForeignKey(State)
    archived = models.BooleanField(default = False)
    headers = models.TextField(blank = True)
    content = models.TextField()
    commit_ref = models.CharField(max_length=255, null = True, blank = True)
    hash = HashField()

    def __str__(self):
        return self.name

    def comments(self):
	return Comment.objects.filter(patch = self)

    def save(self):
	try:
            s = self.state
        except:
            self.state = State.objects.get(ordering =  0)
        if hash is None:
            print "no hash"
        super(Patch, self).save()

    def is_editable(self, user):
        if not user.is_authenticated():
            return False

        if self.submitter.user == user or self.delegate == user:
            return True

        profile = user.get_profile()
        return self.project in user.get_profile().maintainer_projects.all()

    def form(self):
        f = PatchForm(instance = self, prefix = self.id)
        return f

    def filename(self):
        fname_re = re.compile('[^-_A-Za-z0-9\.]+')
        str = fname_re.sub('-', self.name)
        return str.strip('-') + '.patch'

    def mbox(self):
        comment = None
        try:
            comment = Comment.objects.get(msgid = self.msgid)
        except Exception:
            pass

        body = ''
        if comment:
            body = comment.content.strip() + "\n\n"
        body += self.content

        mail = MIMEText(body)
        mail['Subject'] = self.name
        mail['Date'] = email.utils.formatdate(
                        time.mktime(self.date.utctimetuple()))
        mail['From'] = str(self.submitter)
        mail['X-Patchwork-Id'] = str(self.id)
        mail.set_unixfrom('From patchwork ' + self.date.ctime())

        return mail


    @models.permalink
    def get_absolute_url(self):
        return ('patchwork.views.patch.patch', (), {'patch_id': self.id})

    class Meta:
        verbose_name_plural = 'Patches'
        ordering = ['date']

class Comment(models.Model):
    patch = models.ForeignKey(Patch)
    msgid = models.CharField(max_length=255, unique = True)
    submitter = models.ForeignKey(Person)
    date = models.DateTimeField(default = datetime.datetime.now)
    headers = models.TextField(blank = True)
    content = models.TextField()

    class Meta:
        ordering = ['date']

class Bundle(models.Model):
    owner = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    name = models.CharField(max_length = 50, null = False, blank = False)
    patches = models.ManyToManyField(Patch)
    public = models.BooleanField(default = False)

    def n_patches(self):
        return self.patches.all().count()

    class Meta:
        unique_together = [('owner', 'name')]

    def public_url(self):
        if not self.public:
            return None
        site = Site.objects.get_current()
        return 'http://%s%s' % (site.domain,
                reverse('patchwork.views.bundle.public',
                        kwargs = {
                                'username': self.owner.username,
                                'bundlename': self.name
                        }))

    def mbox(self):
        return '\n'.join([p.mbox().as_string(True) \
                        for p in self.patches.all()])


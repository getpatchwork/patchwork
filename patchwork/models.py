# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
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

from __future__ import absolute_import

from collections import Counter, OrderedDict
import datetime
import random
import re

from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.six.moves import filter

from patchwork.fields import HashField
from patchwork.parser import extract_tags, hash_patch


@python_2_unicode_compatible
class Person(models.Model):
    # properties

    email = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True,
                             on_delete=models.SET_NULL)

    def link_to_user(self, user):
        self.name = user.profile.name()
        self.user = user

    def __str__(self):
        if self.name:
            return '%s <%s>' % (self.name, self.email)
        else:
            return self.email

    class Meta:
        verbose_name_plural = 'People'


@python_2_unicode_compatible
class Project(models.Model):
    # properties

    linkname = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, unique=True)
    listid = models.CharField(max_length=255, unique=True)
    listemail = models.CharField(max_length=200)

    # url metadata

    web_url = models.CharField(max_length=2000, blank=True)
    scm_url = models.CharField(max_length=2000, blank=True)
    webscm_url = models.CharField(max_length=2000, blank=True)

    # configuration options

    send_notifications = models.BooleanField(default=False)
    use_tags = models.BooleanField(default=True)

    def is_editable(self, user):
        if not user.is_authenticated():
            return False
        return self in user.profile.maintainer_projects.all()

    @cached_property
    def tags(self):
        if not self.use_tags:
            return []
        return list(Tag.objects.all())

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['linkname']


@python_2_unicode_compatible
class DelegationRule(models.Model):
    user = models.ForeignKey(User)
    path = models.CharField(max_length=255)
    project = models.ForeignKey(Project)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.path

    class Meta:
        ordering = ['-priority', 'path']
        unique_together = (('path', 'project'))


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, related_name='profile')

    # projects

    primary_project = models.ForeignKey(Project, null=True, blank=True)
    maintainer_projects = models.ManyToManyField(
        Project, related_name='maintainer_project', blank=True)

    # configuration options

    send_email = models.BooleanField(
        default=False,
        help_text='Selecting this option allows patchwork to send email on'
        ' your behalf')
    items_per_page = models.PositiveIntegerField(
        default=100, null=False, blank=False,
        help_text='Number of items to display per page')

    def name(self):
        if self.user.first_name or self.user.last_name:
            names = list(filter(
                bool, [self.user.first_name, self.user.last_name]))
            return ' '.join(names)
        return self.user.username

    def contributor_projects(self):
        submitters = Person.objects.filter(user=self.user)
        return Project.objects.filter(id__in=Submission.objects.filter(
            submitter__in=submitters).values('project_id').query)

    def sync_person(self):
        pass

    def n_todo_patches(self):
        return self.todo_patches().count()

    def todo_patches(self, project=None):
        # filter on project, if necessary
        if project:
            qs = Patch.objects.filter(project=project)
        else:
            qs = Patch.objects

        qs = qs.filter(archived=False).filter(
            delegate=self.user).filter(state__in=State.objects.filter(
                action_required=True).values('pk').query)
        return qs

    def __str__(self):
        return self.name()


def _user_saved_callback(sender, created, instance, **kwargs):
    try:
        profile = instance.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=instance)
    profile.save()

models.signals.post_save.connect(_user_saved_callback, sender=User)


@python_2_unicode_compatible
class State(models.Model):
    name = models.CharField(max_length=100)
    ordering = models.IntegerField(unique=True)
    action_required = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['ordering']


@python_2_unicode_compatible
class Tag(models.Model):
    name = models.CharField(max_length=20)
    pattern = models.CharField(
        max_length=50, help_text='A simple regex to match the tag in the'
        ' content of a message. Will be used with MULTILINE and IGNORECASE'
        ' flags. eg. ^Acked-by:')
    abbrev = models.CharField(
        max_length=2, unique=True, help_text='Short (one-or-two letter)'
        ' abbreviation for the tag, used in table column headers')

    @property
    def attr_name(self):
        return 'tag_%d_count' % self.id

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['abbrev']


class PatchTag(models.Model):
    patch = models.ForeignKey('Patch')
    tag = models.ForeignKey('Tag')
    count = models.IntegerField(default=1)

    class Meta:
        unique_together = [('patch', 'tag')]


def get_default_initial_patch_state():
    return State.objects.get(ordering=0)


class PatchQuerySet(models.query.QuerySet):

    def with_tag_counts(self, project):
        if not project.use_tags:
            return self

        # We need the project's use_tags field loaded for Project.tags().
        # Using prefetch_related means we'll share the one instance of
        # Project, and share the project.tags cache between all patch.project
        # references.
        qs = self.prefetch_related('project')
        select = OrderedDict()
        select_params = []
        for tag in project.tags:
            select[tag.attr_name] = (
                "coalesce("
                "(SELECT count FROM patchwork_patchtag"
                " WHERE patchwork_patchtag.patch_id="
                "patchwork_patch.submission_ptr_id"
                " AND patchwork_patchtag.tag_id=%s), 0)")
            select_params.append(tag.id)

        return qs.extra(select=select, select_params=select_params)


class PatchManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return PatchQuerySet(self.model, using=self.db)

    def with_tag_counts(self, project):
        return self.get_queryset().with_tag_counts(project)


class EmailMixin(models.Model):
    """Mixin for models with an email-origin."""
    # email metadata

    msgid = models.CharField(max_length=255)
    date = models.DateTimeField(default=datetime.datetime.now)
    headers = models.TextField(blank=True)

    # content

    submitter = models.ForeignKey(Person)
    content = models.TextField(null=True, blank=True)

    response_re = re.compile(
        r'^(Tested|Reviewed|Acked|Signed-off|Nacked|Reported)-by: .*$',
        re.M | re.I)

    def patch_responses(self):
        if not self.content:
            return ''

        return ''.join([match.group(0) + '\n' for match in
                        self.response_re.finditer(self.content)])

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Submission(EmailMixin, models.Model):
    # parent

    project = models.ForeignKey(Project)

    # submission metadata

    name = models.CharField(max_length=255)

    # patchwork metadata

    def refresh_tag_counts(self):
        pass  # TODO(sfinucan) Once this is only called for patches, remove

    def is_editable(self, user):
        return False

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['date']
        unique_together = [('msgid', 'project')]


class CoverLetter(Submission):
    pass


@python_2_unicode_compatible
class Patch(Submission):
    # patch metadata

    diff = models.TextField(null=True, blank=True)
    commit_ref = models.CharField(max_length=255, null=True, blank=True)
    pull_url = models.CharField(max_length=255, null=True, blank=True)
    tags = models.ManyToManyField(Tag, through=PatchTag)

    # patchwork metadata

    delegate = models.ForeignKey(User, blank=True, null=True)
    state = models.ForeignKey(State, null=True)
    archived = models.BooleanField(default=False)
    hash = HashField(null=True, blank=True)

    objects = PatchManager()

    def _set_tag(self, tag, count):
        if count == 0:
            self.patchtag_set.filter(tag=tag).delete()
            return
        patchtag, _ = PatchTag.objects.get_or_create(patch=self, tag=tag)
        if patchtag.count != count:
            patchtag.count = count
            patchtag.save()

    def refresh_tag_counts(self):
        tags = self.project.tags
        counter = Counter()

        if self.content:
            counter += extract_tags(self.content, tags)

        for comment in self.comments.all():
            counter = counter + extract_tags(comment.content, tags)

        for tag in tags:
            self._set_tag(tag, counter[tag])

    def save(self, **kwargs):
        if not hasattr(self, 'state') or not self.state:
            self.state = get_default_initial_patch_state()

        if self.hash is None and self.diff is not None:
            self.hash = hash_patch(self.diff).hexdigest()

        super(Patch, self).save(**kwargs)

        self.refresh_tag_counts()

    def is_editable(self, user):
        if not user.is_authenticated():
            return False

        if self.submitter.user == user or self.delegate == user:
            return True

        return self.project.is_editable(user)

    def filename(self):
        fname_re = re.compile(r'[^-_A-Za-z0-9\.]+')
        str = fname_re.sub('-', self.name)
        return str.strip('-') + '.patch'

    @property
    def combined_check_state(self):
        """Return the combined state for all checks.

        Generate the combined check's state for this patch. This check
        is one of the following, based on the value of each unique
        check:

          * failure, if any context's latest check reports as failure
          * warning, if any context's latest check reports as warning
          * pending, if there are no checks, or a context's latest
              Check reports as pending
          * success, if latest checks for all contexts reports as
              success
        """
        states = [check.state for check in self.checks]

        if not states:
            return Check.STATE_PENDING

        for state in [Check.STATE_FAIL, Check.STATE_WARNING,
                      Check.STATE_PENDING]:  # order sensitive
            if state in states:
                return state

        return Check.STATE_SUCCESS

    @property
    def checks(self):
        """Return the list of unique checks.

        Generate a list of checks associated with this patch for each
        type of Check. Only "unique" checks are considered,
        identified by their 'context' field. This means, given n
        checks with the same 'context', the newest check is the only
        one counted regardless of its value. The end result will be a
        association of types to number of unique checks for said
        type.
        """
        unique = {}

        for check in self.check_set.all():
            ctx = check.context

            # recheck condition - ignore the older result
            if ctx in unique and unique[ctx].date > check.date:
                continue

            unique[ctx] = check

        return list(unique.values())

    @property
    def check_count(self):
        """Generate a list of unique checks for each patch.

        Compile a list of checks associated with this patch for each
        type of check. Only "unique" checks are considered, identified
        by their 'context' field. This means, given n checks with the
        same 'context', the newest check is the only one counted
        regardless of its value. The end result will be a association
        of types to number of unique checks for said type.
        """
        counts = {key: 0 for key, _ in Check.STATE_CHOICES}

        for check in self.checks:
            counts[check.state] += 1

        return counts

    @models.permalink
    def get_absolute_url(self):
        return ('patch-detail', (), {'patch_id': self.id})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Patches'


class Comment(EmailMixin, models.Model):
    # parent

    submission = models.ForeignKey(Submission, related_name='comments',
                                   related_query_name='comment')

    def save(self, *args, **kwargs):
        super(Comment, self).save(*args, **kwargs)
        self.submission.refresh_tag_counts()

    def delete(self, *args, **kwargs):
        super(Comment, self).delete(*args, **kwargs)
        self.submission.refresh_tag_counts()

    class Meta:
        ordering = ['date']
        unique_together = [('msgid', 'submission')]


class Bundle(models.Model):
    owner = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=50, null=False, blank=False)
    patches = models.ManyToManyField(Patch, through='BundlePatch')
    public = models.BooleanField(default=False)

    def n_patches(self):
        return self.patches.all().count()

    def ordered_patches(self):
        return self.patches.order_by('bundlepatch__order')

    def append_patch(self, patch):
        # todo: use the aggregate queries in django 1.1
        orders = BundlePatch.objects.filter(bundle=self).order_by('-order') \
            .values('order')

        if len(orders) > 0:
            max_order = orders[0]['order']
        else:
            max_order = 0

        # see if the patch is already in this bundle
        if BundlePatch.objects.filter(bundle=self,
                                      patch=patch).count():
            raise Exception('patch is already in bundle')

        bp = BundlePatch.objects.create(bundle=self, patch=patch,
                                        order=max_order + 1)
        bp.save()

    def public_url(self):
        if not self.public:
            return None
        site = Site.objects.get_current()
        return 'http://%s%s' % (site.domain,
                                reverse('bundle-detail',
                                        kwargs={
                                            'username': self.owner.username,
                                            'bundlename': self.name
                                        }))

    @models.permalink
    def get_absolute_url(self):
        return ('bundle-detail', (), {
            'username': self.owner.username,
            'bundlename': self.name,
        })

    class Meta:
        unique_together = [('owner', 'name')]


class BundlePatch(models.Model):
    patch = models.ForeignKey(Patch)
    bundle = models.ForeignKey(Bundle)
    order = models.IntegerField()

    class Meta:
        unique_together = [('bundle', 'patch')]
        ordering = ['order']


@python_2_unicode_compatible
class Check(models.Model):

    """Check for a patch.

    Checks store the results of any tests executed (or executing) for a
    given patch. This is useful, for example, when using a continuous
    integration (CI) system to test patches.
    """
    STATE_PENDING = 0
    STATE_SUCCESS = 1
    STATE_WARNING = 2
    STATE_FAIL = 3
    STATE_CHOICES = (
        (STATE_PENDING, 'pending'),
        (STATE_SUCCESS, 'success'),
        (STATE_WARNING, 'warning'),
        (STATE_FAIL, 'fail'),
    )

    patch = models.ForeignKey(Patch)
    user = models.ForeignKey(User)
    date = models.DateTimeField(default=datetime.datetime.now)

    state = models.SmallIntegerField(
        choices=STATE_CHOICES, default=STATE_PENDING,
        help_text='The state of the check.')
    target_url = models.URLField(
        blank=True, null=True,
        help_text='The target URL to associate with this check. This should'
        ' be specific to the patch.')
    description = models.TextField(
        blank=True, null=True, help_text='A brief description of the check.')
    context = models.CharField(
        max_length=255, default='default', blank=True, null=True,
        help_text='A label to discern check from checks of other testing '
        'systems.')

    def __repr__(self):
        return "<Check id='%d' context='%s' state='%s'" % (
            self.id, self.context, self.get_state_display())

    def __str__(self):
        return '%s (%s)' % (self.context, self.get_state_display())


class EmailConfirmation(models.Model):
    validity = datetime.timedelta(days=settings.CONFIRMATION_VALIDITY_DAYS)
    type = models.CharField(max_length=20, choices=[
        ('userperson', 'User-Person association'),
        ('registration', 'Registration'),
        ('optout', 'Email opt-out'),
    ])
    email = models.CharField(max_length=200)
    user = models.ForeignKey(User, null=True)
    key = HashField()
    date = models.DateTimeField(default=datetime.datetime.now)
    active = models.BooleanField(default=True)

    def deactivate(self):
        self.active = False
        self.save()

    def is_valid(self):
        return self.date + self.validity > datetime.datetime.now()

    def save(self):
        max = 1 << 32
        if self.key == '':
            str = '%s%s%d' % (self.user, self.email, random.randint(0, max))
            self.key = self._meta.get_field('key').construct(str).hexdigest()
        super(EmailConfirmation, self).save()


@python_2_unicode_compatible
class EmailOptout(models.Model):
    email = models.CharField(max_length=200, primary_key=True)

    @classmethod
    def is_optout(cls, email):
        email = email.lower().strip()
        return cls.objects.filter(email=email).count() > 0

    def __str__(self):
        return self.email


class PatchChangeNotification(models.Model):
    patch = models.OneToOneField(Patch, primary_key=True)
    last_modified = models.DateTimeField(default=datetime.datetime.now)
    orig_state = models.ForeignKey(State)


def _patch_change_callback(sender, instance, **kwargs):
    # we only want notification of modified patches
    if instance.pk is None:
        return

    if instance.project is None or not instance.project.send_notifications:
        return

    try:
        orig_patch = Patch.objects.get(pk=instance.pk)
    except Patch.DoesNotExist:
        return

    # If there's no interesting changes, abort without creating the
    # notification
    if orig_patch.state == instance.state:
        return

    notification = None
    try:
        notification = PatchChangeNotification.objects.get(patch=instance)
    except PatchChangeNotification.DoesNotExist:
        pass

    if notification is None:
        notification = PatchChangeNotification(patch=instance,
                                               orig_state=orig_patch.state)
    elif notification.orig_state == instance.state:
        # If we're back at the original state, there is no need to notify
        notification.delete()
        return

    notification.last_modified = datetime.datetime.now()
    notification.save()

models.signals.pre_save.connect(_patch_change_callback, sender=Patch)

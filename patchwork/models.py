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

from collections import Counter
from collections import OrderedDict
import datetime
import random
import re

import django
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property

from patchwork.compat import is_authenticated
from patchwork.compat import reverse
from patchwork.fields import HashField
from patchwork.hasher import hash_diff

if settings.ENABLE_REST_API:
    from rest_framework.authtoken.models import Token


@python_2_unicode_compatible
class Person(models.Model):
    # properties

    email = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True,
                             on_delete=models.SET_NULL)

    def link_to_user(self, user):
        self.name = user.profile.name
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
        if not is_authenticated(user):
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
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text='A user to delegate the patch to.')
    path = models.CharField(
        max_length=255,
        help_text='An fnmatch-style pattern to match filenames against.')
    priority = models.IntegerField(
        default=0,
        help_text='The priority of the rule. Rules with a higher priority '
        'will override rules with lower priorities')

    def __str__(self):
        return self.path

    class Meta:
        ordering = ['-priority', 'path']
        unique_together = (('path', 'project'))


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, related_name='profile',
                                on_delete=models.CASCADE)

    # projects

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
    show_ids = models.BooleanField(
        default=False,
        help_text='Show click-to-copy patch IDs in the list view')

    @property
    def name(self):
        if self.user.first_name or self.user.last_name:
            names = [self.user.first_name, self.user.last_name]
            return ' '.join([x for x in names if x])
        return self.user.username

    @property
    def contributor_projects(self):
        submitters = Person.objects.filter(user=self.user)
        return Project.objects.filter(id__in=Submission.objects.filter(
            submitter__in=submitters).values('project_id').query)

    @property
    def n_todo_patches(self):
        return self.todo_patches().count()

    @property
    def token(self):
        if not settings.ENABLE_REST_API:
            return

        try:
            return Token.objects.get(user=self.user)
        except Token.DoesNotExist:
            return

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
        return self.name


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

    @property
    def slug(self):
        return '-'.join(self.name.lower().split())

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
    show_column = models.BooleanField(help_text='Show a column displaying this'
                                      ' tag\'s count in the patch list view',
                                      default=True)

    @property
    def attr_name(self):
        return 'tag_%d_count' % self.id

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['abbrev']


class PatchTag(models.Model):
    patch = models.ForeignKey('Patch', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    count = models.IntegerField(default=1)

    class Meta:
        unique_together = [('patch', 'tag')]


def get_default_initial_patch_state():
    return State.objects.get(ordering=0)


class PatchQuerySet(models.query.QuerySet):

    def with_tag_counts(self, project=None):
        if project and not project.use_tags:
            return self

        # We need the project's use_tags field loaded for Project.tags().
        # Using prefetch_related means we'll share the one instance of
        # Project, and share the project.tags cache between all patch.project
        # references.
        qs = self.prefetch_related('project')
        select = OrderedDict()
        select_params = []

        # All projects have the same tags, so we're good to go here
        if project:
            tags = project.tags
        else:
            tags = Tag.objects.all()

        for tag in tags:
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
    # NOTE(stephenfin): This is necessary to silence a warning with Django >=
    # 1.10. Remove when 1.10 is the minimum supported version.
    silence_use_for_related_fields_deprecation = True

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

    submitter = models.ForeignKey(Person, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)

    response_re = re.compile(
        r'^(Tested|Reviewed|Acked|Signed-off|Nacked|Reported)-by:.*$',
        re.M | re.I)

    @property
    def patch_responses(self):
        if not self.content:
            return ''

        return ''.join([match.group(0) + '\n' for match in
                        self.response_re.finditer(self.content)])

    def save(self, *args, **kwargs):
        # Modifying a submission via admin interface changes '\n' newlines in
        # message content to '\r\n'. We need to fix them to avoid problems,
        # especially as git complains about malformed patches when PW runs
        # on PY2
        self.content = self.content.replace('\r\n', '\n')
        super(EmailMixin, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class FilenameMixin(object):

    @property
    def filename(self):
        """Return a sanitized filename without extension."""
        fname_re = re.compile(r'[^-_A-Za-z0-9\.]+')
        fname = fname_re.sub('-', str(self)).strip('-')
        return fname


@python_2_unicode_compatible
class Submission(FilenameMixin, EmailMixin, models.Model):
    # parent

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # submission metadata

    name = models.CharField(max_length=255)

    # patchwork metadata

    def is_editable(self, user):
        return False

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['date']
        unique_together = [('msgid', 'project')]


class SeriesMixin(object):

    @property
    def latest_series(self):
        """Get the latest series this is a member of.

        Return the last series that (ordered by date) that this
        submission is a member of.

        .. warning::
          Be judicious in your use of this. For example, do not use it
          in list templates as doing so will result in a new query for
          each item in the list.
        """
        # NOTE(stephenfin): We don't use 'latest()' here, as this can raise an
        # exception if no series exist
        return self.series.order_by('-date').first()


class CoverLetter(SeriesMixin, Submission):

    def get_mbox_url(self):
        return reverse('cover-mbox', kwargs={'cover_id': self.id})


@python_2_unicode_compatible
class Patch(SeriesMixin, Submission):
    # patch metadata

    diff = models.TextField(null=True, blank=True)
    commit_ref = models.CharField(max_length=255, null=True, blank=True)
    pull_url = models.CharField(max_length=255, null=True, blank=True)
    tags = models.ManyToManyField(Tag, through=PatchTag)

    # patchwork metadata

    delegate = models.ForeignKey(User, blank=True, null=True,
                                 on_delete=models.CASCADE)
    state = models.ForeignKey(State, null=True, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)
    hash = HashField(null=True, blank=True)

    objects = PatchManager()

    @staticmethod
    def extract_tags(content, tags):
        counts = Counter()

        for tag in tags:
            regex = re.compile(tag.pattern, re.MULTILINE | re.IGNORECASE)
            counts[tag] = len(regex.findall(content))

        return counts

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
            counter += self.extract_tags(self.content, tags)

        for comment in self.comments.all():
            counter = counter + self.extract_tags(comment.content, tags)

        for tag in tags:
            self._set_tag(tag, counter[tag])

    def save(self, *args, **kwargs):
        if not hasattr(self, 'state') or not self.state:
            self.state = get_default_initial_patch_state()

        if self.hash is None and self.diff is not None:
            self.hash = hash_diff(self.diff)

        super(Patch, self).save(**kwargs)

        self.refresh_tag_counts()

    def is_editable(self, user):
        if not is_authenticated(user):
            return False

        if user in [self.submitter.user, self.delegate]:
            return True

        return self.project.is_editable(user)

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
        state_names = dict(Check.STATE_CHOICES)
        states = [check.state for check in self.checks]

        if not states:
            return state_names[Check.STATE_PENDING]

        for state in [Check.STATE_FAIL, Check.STATE_WARNING,
                      Check.STATE_PENDING]:  # order sensitive
            if state in states:
                return state_names[state]

        return state_names[Check.STATE_SUCCESS]

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
        duplicates = []

        for check in self.check_set.all():
            ctx = check.context
            user = check.user

            if user in unique and ctx in unique[user]:
                # recheck condition - ignore the older result
                if unique[user][ctx].date > check.date:
                    duplicates.append(check.id)
                    continue
                duplicates.append(unique[user][ctx].id)

            if user not in unique:
                unique[user] = {}

            unique[user][ctx] = check

        # filter out the "duplicates" or older, now-invalid results

        # Why don't we use filter or exclude here? Surprisingly, it's
        # an optimisation in the common case. Where we're looking at
        # checks in anything that uses a generic_list() in the view,
        # we do a prefetch_related('check_set'). But, if we then do a
        # .filter or a .exclude, that throws out the existing, cached
        # information, and does another query. (See the Django docs on
        # prefetch_related.) So, do it 'by hand' in Python. We can
        # also be confident that this won't be worse, seeing as we've
        # just iterated over self.check_set.all() *anyway*.
        return [c for c in self.check_set.all() if c.id not in duplicates]

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

    def get_absolute_url(self):
        return reverse('patch-detail', kwargs={'patch_id': self.id})

    def get_mbox_url(self):
        return reverse('patch-mbox', kwargs={'patch_id': self.id})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Patches'
        if django.VERSION >= (1, 10):
            base_manager_name = 'objects'


class Comment(EmailMixin, models.Model):
    # parent

    submission = models.ForeignKey(Submission, related_name='comments',
                                   related_query_name='comment',
                                   on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super(Comment, self).save(*args, **kwargs)
        if hasattr(self.submission, 'patch'):
            self.submission.patch.refresh_tag_counts()

    def delete(self, *args, **kwargs):
        super(Comment, self).delete(*args, **kwargs)
        if hasattr(self.submission, 'patch'):
            self.submission.patch.refresh_tag_counts()

    class Meta:
        ordering = ['date']
        unique_together = [('msgid', 'submission')]


@python_2_unicode_compatible
class Series(FilenameMixin, models.Model):
    """An collection of patches."""

    # parent
    project = models.ForeignKey(Project, related_name='series', null=True,
                                blank=True, on_delete=models.CASCADE)

    # content
    cover_letter = models.ForeignKey(CoverLetter,
                                     related_name='series',
                                     null=True, blank=True,
                                     on_delete=models.CASCADE)
    patches = models.ManyToManyField(Patch, through='SeriesPatch',
                                     related_name='series')

    # metadata
    name = models.CharField(max_length=255, blank=True, null=True,
                            help_text='An optional name to associate with '
                            'the series, e.g. "John\'s PCI series".')
    date = models.DateTimeField()
    submitter = models.ForeignKey(Person, on_delete=models.CASCADE)
    version = models.IntegerField(default=1,
                                  help_text='Version of series as indicated '
                                  'by the subject prefix(es)')
    total = models.IntegerField(help_text='Number of patches in series as '
                                'indicated by the subject prefix(es)')

    @staticmethod
    def _format_name(obj):
        # The parser ensure 'Submission.name' will always take the form
        # 'subject' or '[prefix_a,prefix_b,...] subject'. There will never be
        # multiple prefixes (text inside brackets), thus, we don't need to
        # account for multiple prefixes here.
        prefix_re = re.compile(r'^\[([^\]]*)\]\s*(.*)$')
        match = prefix_re.match(obj.name)
        if match:
            return match.group(2)
        return obj.name.strip()

    @property
    def received_total(self):
        return self.patches.count()

    @property
    def received_all(self):
        return self.total <= self.received_total

    def add_cover_letter(self, cover):
        """Add a cover letter to the series.

        Helper method so we can use the same pattern to add both
        patches and cover letters.
        """

        if self.cover_letter:
            # TODO(stephenfin): We may wish to raise an exception here in the
            # future
            return

        self.cover_letter = cover

        # we allow "upgrading of series names. Names from different
        # sources are prioritized:
        #
        # 1. user-provided names
        # 2. cover letter-based names
        # 3. first patch-based (i.e. 01/nn) names
        #
        # Names are never "downgraded" - a cover letter received after
        # the first patch will result in the name being upgraded to a
        # cover letter-based name, but receiving the first patch after
        # the cover letter will not change the name of the series.
        #
        # If none of the above are available, the name will be null.

        if not self.name:
            self.name = self._format_name(cover)
        else:
            try:
                name = SeriesPatch.objects.get(series=self,
                                               number=1).patch.name
            except SeriesPatch.DoesNotExist:
                name = None

            if self.name == name:
                self.name = self._format_name(cover)

        self.save()

    def add_patch(self, patch, number):
        """Add a patch to the series."""
        # see if the patch is already in this series
        if SeriesPatch.objects.filter(series=self, patch=patch).count():
            # TODO(stephenfin): We may wish to raise an exception here in the
            # future
            return

        # both user defined names and cover letter-based names take precedence
        if not self.name and number == 1:
            self.name = patch.name  # keep the prefixes for patch-based names
            self.save()

        return SeriesPatch.objects.create(series=self,
                                          patch=patch,
                                          number=number)

    def get_mbox_url(self):
        return reverse('series-mbox', kwargs={'series_id': self.id})

    def __str__(self):
        return self.name if self.name else 'Untitled series #%d' % self.id

    class Meta:
        ordering = ('date',)
        verbose_name_plural = 'Series'


@python_2_unicode_compatible
class SeriesPatch(models.Model):
    """A patch in a series.

    Patches can belong to many series. This allows for things like
    auto-completion of partial series.
    """
    patch = models.ForeignKey(Patch, on_delete=models.CASCADE)
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField(
        help_text='The number assigned to this patch in the series')

    def __str__(self):
        return self.patch.name

    class Meta:
        unique_together = [('series', 'patch'), ('series', 'number')]
        ordering = ['number']


@python_2_unicode_compatible
class SeriesReference(models.Model):
    """A reference found in a series.

    Message IDs should be created for all patches in a series,
    including those of patches that have not yet been received. This is
    required to handle the case whereby one or more patches are
    received before the cover letter.
    """
    series = models.ForeignKey(Series, related_name='references',
                               related_query_name='reference',
                               on_delete=models.CASCADE)
    msgid = models.CharField(max_length=255)

    def __str__(self):
        return self.msgid

    class Meta:
        unique_together = [('series', 'msgid')]


class Bundle(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=False, blank=False)
    patches = models.ManyToManyField(Patch, through='BundlePatch')
    public = models.BooleanField(default=False)

    def ordered_patches(self):
        return self.patches.order_by('bundlepatch__order')

    def append_patch(self, patch):
        orders = BundlePatch.objects.filter(bundle=self).aggregate(
            models.Max('order'))

        if orders and orders['order__max']:
            max_order = orders['order__max']
        else:
            max_order = 0

        if BundlePatch.objects.filter(bundle=self, patch=patch).exists():
            return

        return BundlePatch.objects.create(bundle=self, patch=patch,
                                          order=max_order + 1)

    def get_absolute_url(self):
        return reverse('bundle-detail', kwargs={
            'username': self.owner.username,
            'bundlename': self.name,
        })

    def get_mbox_url(self):
        return reverse('bundle-mbox', kwargs={
            'bundlename': self.name,
            'username': self.owner.username
        })

    class Meta:
        unique_together = [('owner', 'name')]


class BundlePatch(models.Model):
    patch = models.ForeignKey(Patch, on_delete=models.CASCADE)
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE)
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

    patch = models.ForeignKey(Patch, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=datetime.datetime.now)

    state = models.SmallIntegerField(
        choices=STATE_CHOICES, default=STATE_PENDING,
        help_text='The state of the check.')
    target_url = models.URLField(
        blank=True, null=True,
        help_text='The target URL to associate with this check. This should '
        'be specific to the patch.')
    description = models.TextField(
        blank=True, null=True, help_text='A brief description of the check.')
    context = models.SlugField(
        max_length=255, default='default',
        help_text='A label to discern check from checks of other testing '
        'systems.')

    def __repr__(self):
        return "<Check id='%d' context='%s' state='%s'" % (
            self.id, self.context, self.get_state_display())

    def __str__(self):
        return '%s (%s)' % (self.context, self.get_state_display())


class Event(models.Model):
    """An event raised against a patch.

    Events are created whenever certain attributes of a patch are
    changed.

    This model makes extensive use of nullification of fields. This is more
    performant than a solution using concrete subclasses while still providing
    the integrity promises that foreign keys provide. Generic foreign keys
    are another solution, but using these will result in a lot of massaging
    should we wish to add support for an 'expand' paramter in the REST API in
    the future. Refer to https://code.djangoproject.com/ticket/24272 for more
    information.
    """
    CATEGORY_COVER_CREATED = 'cover-created'
    CATEGORY_PATCH_CREATED = 'patch-created'
    CATEGORY_PATCH_COMPLETED = 'patch-completed'
    CATEGORY_PATCH_STATE_CHANGED = 'patch-state-changed'
    CATEGORY_PATCH_DELEGATED = 'patch-delegated'
    CATEGORY_CHECK_CREATED = 'check-created'
    CATEGORY_SERIES_CREATED = 'series-created'
    CATEGORY_SERIES_COMPLETED = 'series-completed'
    CATEGORY_CHOICES = (
        (CATEGORY_COVER_CREATED, 'Cover Letter Created'),
        (CATEGORY_PATCH_CREATED, 'Patch Created'),
        (CATEGORY_PATCH_COMPLETED, 'Patch Completed'),
        (CATEGORY_PATCH_STATE_CHANGED, 'Patch State Changed'),
        (CATEGORY_PATCH_DELEGATED, 'Patch Delegate Changed'),
        (CATEGORY_CHECK_CREATED, 'Check Created'),
        (CATEGORY_SERIES_CREATED, 'Series Created'),
        (CATEGORY_SERIES_COMPLETED, 'Series Completed'),
    )

    # parents

    project = models.ForeignKey(
        Project, related_name='+', db_index=True,
        on_delete=models.CASCADE,
        help_text='The project that the events belongs to.')

    # event metadata

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text='The category of the event.')
    date = models.DateTimeField(
        default=datetime.datetime.now,
        help_text='The time this event was created.')

    # event object

    # only one of the below should be used, depending on which category was
    # used

    patch = models.ForeignKey(
        Patch, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE,
        help_text='The patch that this event was created for.')
    series = models.ForeignKey(
        Series, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE,
        help_text='The series that this event was created for.')
    cover = models.ForeignKey(
        CoverLetter, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE,
        help_text='The cover letter that this event was created for.')

    # fields for 'patch-state-changed' events

    previous_state = models.ForeignKey(
        State, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE)
    current_state = models.ForeignKey(
        State, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE)

    # fields for 'patch-delegate-changed' events

    previous_delegate = models.ForeignKey(
        User, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE)
    current_delegate = models.ForeignKey(
        User, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE)

    # fields or 'patch-check-created' events

    created_check = models.ForeignKey(
        Check, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE)

    # TODO(stephenfin): Validate that the correct fields are being set by way
    # of a 'clean' method

    def __repr__(self):
        return "<Event id='%d' category='%s'" % (self.id, self.category)

    class Meta:
        ordering = ['-date']


class EmailConfirmation(models.Model):
    validity = datetime.timedelta(days=settings.CONFIRMATION_VALIDITY_DAYS)
    type = models.CharField(max_length=20, choices=[
        ('userperson', 'User-Person association'),
        ('registration', 'Registration'),
        ('optout', 'Email opt-out'),
    ])
    email = models.CharField(max_length=200)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    key = HashField()
    date = models.DateTimeField(default=datetime.datetime.now)
    active = models.BooleanField(default=True)

    def deactivate(self):
        self.active = False
        self.save()

    def is_valid(self):
        return self.date + self.validity > datetime.datetime.now()

    def save(self, *args, **kwargs):
        limit = 1 << 32
        if not self.key:
            key = '%s%s%d' % (self.user, self.email, random.randint(0, limit))
            self.key = self._meta.get_field('key').construct(key).hexdigest()
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
    patch = models.OneToOneField(Patch, primary_key=True,
                                 on_delete=models.CASCADE)
    last_modified = models.DateTimeField(default=datetime.datetime.now)
    orig_state = models.ForeignKey(State, on_delete=models.CASCADE)

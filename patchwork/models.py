# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from collections import Counter
from collections import OrderedDict
import datetime
import random
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.core.validators import validate_unicode_slug

from patchwork.fields import HashField
from patchwork.hasher import hash_diff

if settings.ENABLE_REST_API:
    from rest_framework.authtoken.models import Token


def validate_regex_compiles(regex_string):
    try:
        re.compile(regex_string)
    except Exception:
        raise ValidationError('Invalid regular expression entered!')


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


class Project(models.Model):
    # properties

    linkname = models.CharField(max_length=255, unique=True,
                                validators=[validate_unicode_slug])
    name = models.CharField(max_length=255, unique=True)
    listid = models.CharField(max_length=255)
    listemail = models.CharField(max_length=200)
    subject_match = models.CharField(
        max_length=64, blank=True, default='',
        validators=[validate_regex_compiles], help_text='Regex to match the '
        'subject against if only part of emails sent to the list belongs to '
        'this project. Will be used with IGNORECASE and MULTILINE flags. If '
        'rules for more projects match the first one returned from DB is '
        'chosen; empty field serves as a default for every email which has no '
        'other match.')

    # url metadata

    web_url = models.CharField(max_length=2000, blank=True)
    scm_url = models.CharField(max_length=2000, blank=True)
    webscm_url = models.CharField(max_length=2000, blank=True)
    list_archive_url = models.CharField(max_length=2000, blank=True)
    list_archive_url_format = models.CharField(
        max_length=2000,
        blank=True,
        help_text="URL format for the list archive's Message-ID redirector. "
        "{} will be replaced by the Message-ID.")
    commit_url_format = models.CharField(
        max_length=2000,
        blank=True,
        help_text='URL format for a particular commit. '
        '{} will be replaced by the commit SHA.')

    # configuration options

    send_notifications = models.BooleanField(default=False)
    use_tags = models.BooleanField(default=True)

    def is_editable(self, user):
        if not user.is_authenticated:
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
        unique_together = (('listid', 'subject_match'),)
        ordering = ['linkname']


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
        return Project.objects.filter(id__in=Patch.objects.filter(
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
        profile.user = instance
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=instance)
    profile.save()


models.signals.post_save.connect(_user_saved_callback, sender=User)


class State(models.Model):
    # Both of these fields should be unique
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    ordering = models.IntegerField(unique=True)
    action_required = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['ordering']


class Tag(models.Model):
    name = models.CharField(max_length=20)
    pattern = models.CharField(
        max_length=50, validators=[validate_regex_compiles],
        help_text='A simple regex to match the tag in the content of a '
        'message. Will be used with MULTILINE and IGNORECASE flags. eg. '
        '^Acked-by:')
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
                " WHERE patchwork_patchtag.patch_id=patchwork_patch.id"
                " AND patchwork_patchtag.tag_id=%s), 0)")
            select_params.append(tag.id)

        return qs.extra(select=select, select_params=select_params)


class PatchManager(models.Manager):

    def get_queryset(self):
        return PatchQuerySet(self.model, using=self.db)

    def with_tag_counts(self, project):
        return self.get_queryset().with_tag_counts(project)


class EmailMixin(models.Model):
    """Mixin for models with an email-origin."""
    # email metadata

    msgid = models.CharField(max_length=255)
    date = models.DateTimeField(default=datetime.datetime.utcnow)
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

    @property
    def url_msgid(self):
        """A trimmed messageid, suitable for inclusion in URLs"""
        if settings.DEBUG:
            assert self.msgid[0] == '<' and self.msgid[-1] == '>'

        return self.msgid.strip('<>')

    def save(self, *args, **kwargs):
        # Modifying a submission via admin interface changes '\n' newlines in
        # message content to '\r\n'. We need to fix them to avoid problems,
        # especially as git complains about malformed patches when PW runs
        if self.content:
            # on PY2 TODO: is this still needed on PY3?
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


class SubmissionMixin(FilenameMixin, EmailMixin, models.Model):
    # parent

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # submission metadata

    name = models.CharField(max_length=255)

    @property
    def list_archive_url(self):
        if not self.project.list_archive_url_format:
            return None

        if not self.msgid:
            return None

        return self.project.list_archive_url_format.format(
            self.url_msgid,
        )

    # patchwork metadata

    def is_editable(self, user):
        return False

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Cover(SubmissionMixin):

    def get_absolute_url(self):
        return reverse('cover-detail',
                       kwargs={'project_id': self.project.linkname,
                               'msgid': self.url_msgid})

    def get_mbox_url(self):
        return reverse('cover-mbox',
                       kwargs={'project_id': self.project.linkname,
                               'msgid': self.url_msgid})

    class Meta:
        ordering = ['date']
        unique_together = [('msgid', 'project')]
        indexes = [
            # This is a covering index for the /list/ query
            # Like what we have for Patch, but used for displaying what we want
            # rather than for working out the count (of course, this all
            # depends on the SQL optimiser of your DB engine)
            models.Index(
                fields=['date', 'project', 'submitter', 'name'],
                name='cover_covering_idx',
            ),
        ]


class Patch(SubmissionMixin):

    diff = models.TextField(null=True, blank=True)
    commit_ref = models.CharField(max_length=255, null=True, blank=True)
    pull_url = models.CharField(max_length=255, null=True, blank=True)
    tags = models.ManyToManyField(Tag, through=PatchTag)

    # patchwork metadata

    delegate = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    state = models.ForeignKey(State, null=True, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)
    hash = HashField(null=True, blank=True)

    # series metadata

    series = models.ForeignKey(
        'Series',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='patches',
        related_query_name='patch',
    )
    number = models.PositiveSmallIntegerField(
        default=None,
        null=True,
        help_text='The number assigned to this patch in the series',
    )

    # related patches metadata

    related = models.ForeignKey(
        'PatchRelation', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='patches', related_query_name='patch')

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
        if not user.is_authenticated:
            return False

        if user in [self.submitter.user, self.delegate]:
            self._edited_by = user
            return True

        if self.project.is_editable(user):
            self._edited_by = user
            return True
        return False

    @staticmethod
    def filter_unique_checks(checks):
        """Filter the provided checks to generate the unique list."""
        unique = {}
        duplicates = []

        for check in checks:
            ctx = check.context
            user = check.user_id

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
        return [c for c in checks if c.id not in duplicates]

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
        return self.filter_unique_checks(self.check_set.all())

    @property
    def combined_check_state(self):
        """Return the combined state for all checks.

        Generate the combined check's state for this patch. This check
        is one of the following, based on the value of each unique
        check:

        * failure, if any context's latest check reports as failure
        * warning, if any context's latest check reports as warning
        * pending, if there are no checks, or a context's latest check reports
          as pending
        * success, if latest checks for all contexts reports as success
        """
        state_names = dict(Check.STATE_CHOICES)
        states = [check.state for check in self.checks]

        if not states:
            return state_names[Check.STATE_PENDING]

        # order sensitive
        for state in (
            Check.STATE_FAIL, Check.STATE_WARNING, Check.STATE_PENDING,
        ):
            if state in states:
                return state_names[state]

        return state_names[Check.STATE_SUCCESS]

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
        return reverse('patch-detail',
                       kwargs={'project_id': self.project.linkname,
                               'msgid': self.url_msgid})

    def get_mbox_url(self):
        return reverse('patch-mbox',
                       kwargs={'project_id': self.project.linkname,
                               'msgid': self.url_msgid})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Patches'
        ordering = ['date']
        base_manager_name = 'objects'
        unique_together = [('msgid', 'project'), ('series', 'number')]
        indexes = [
            # This is a covering index for the /list/ query
            models.Index(
                fields=[
                    'archived',
                    'state',
                    'delegate',
                    'date',
                    'project',
                    'submitter',
                    'name',
                ],
                name='patch_covering_idx',
            ),
        ]


class CoverComment(EmailMixin, models.Model):

    cover = models.ForeignKey(
        Cover,
        related_name='comments',
        related_query_name='comment',
        on_delete=models.CASCADE,
    )
    addressed = models.BooleanField(null=True)

    @property
    def list_archive_url(self):
        if not self.cover.project.list_archive_url_format:
            return None

        if not self.msgid:
            return None

        return self.cover.project.list_archive_url_format.format(
            self.url_msgid,
        )

    def get_absolute_url(self):
        return reverse('comment-redirect', kwargs={'comment_id': self.id})

    def is_editable(self, user):
        if not user.is_authenticated:
            return False

        # user submitted comment
        if user == self.submitter.user:
            return True

        # user submitted cover letter
        if user == self.cover.submitter.user:
            return True

        # user is project maintainer
        if self.cover.project.is_editable(user):
            return True
        return False

    class Meta:
        ordering = ['date']
        unique_together = [('msgid', 'cover')]
        indexes = [
            models.Index(name='cover_date_idx', fields=['cover', 'date']),
        ]


class PatchComment(EmailMixin, models.Model):
    # parent

    patch = models.ForeignKey(
        Patch,
        related_name='comments',
        related_query_name='comment',
        on_delete=models.CASCADE,
    )
    addressed = models.BooleanField(null=True)

    @property
    def list_archive_url(self):
        if not self.patch.project.list_archive_url_format:
            return None

        if not self.msgid:
            return None

        return self.patch.project.list_archive_url_format.format(
            self.url_msgid,
        )

    def get_absolute_url(self):
        return reverse('comment-redirect', kwargs={'comment_id': self.id})

    def save(self, *args, **kwargs):
        super(PatchComment, self).save(*args, **kwargs)
        self.patch.refresh_tag_counts()

    def delete(self, *args, **kwargs):
        super(PatchComment, self).delete(*args, **kwargs)
        self.patch.refresh_tag_counts()

    def is_editable(self, user):
        if user == self.submitter.user:
            return True
        return self.patch.is_editable(user)

    class Meta:
        ordering = ['date']
        unique_together = [('msgid', 'patch')]
        indexes = [
            models.Index(name='patch_date_idx', fields=['patch', 'date']),
        ]


class Series(FilenameMixin, models.Model):
    """A collection of patches."""

    # parent
    project = models.ForeignKey(Project, related_name='series', null=True,
                                blank=True, on_delete=models.CASCADE)

    # content
    cover_letter = models.OneToOneField(
        Cover,
        related_name='series',
        null=True,
        on_delete=models.CASCADE
    )

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
        # The parser ensure 'Cover.name' will always take the form 'subject' or
        # '[prefix_a,prefix_b,...] subject'. There will never be multiple
        # prefixes (text inside brackets), thus, we don't need to account for
        # multiple prefixes here.
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
                name = Patch.objects.get(series=self, number=1).name
            except Patch.DoesNotExist:
                name = None

            if self.name == name:
                self.name = self._format_name(cover)

        self.save()

    def add_patch(self, patch, number):
        """Add a patch to the series."""
        # both user defined names and cover letter-based names take precedence
        if not self.name and number == 1:
            self.name = patch.name  # keep the prefixes for patch-based names
            self.save()

        patch.series = self
        patch.number = number
        patch.save()

        return patch

    def get_absolute_url(self):
        # TODO(stephenfin): We really need a proper series view
        return reverse('patch-list',
                       kwargs={'project_id': self.project.linkname}) + (
            '?series=%d' % self.id)

    def get_mbox_url(self):
        return reverse('series-mbox', kwargs={'series_id': self.id})

    def __str__(self):
        return self.name if self.name else 'Untitled series #%d' % self.id

    class Meta:
        verbose_name_plural = 'Series'


class SeriesReference(models.Model):
    """A reference found in a series.

    Message IDs should be created for all patches in a series,
    including those of patches that have not yet been received. This is
    required to handle the case whereby one or more patches are
    received before the cover letter.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    series = models.ForeignKey(Series, related_name='references',
                               related_query_name='reference',
                               on_delete=models.CASCADE)
    msgid = models.CharField(max_length=255)

    def __str__(self):
        return self.msgid

    class Meta:
        unique_together = [('project', 'msgid')]


class Bundle(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='bundles',
                              related_query_name='bundle')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=False, blank=False)
    patches = models.ManyToManyField(Patch, through='BundlePatch')
    public = models.BooleanField(default=False)

    def is_editable(self, user):
        if not user.is_authenticated:
            return False
        return user == self.owner

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

    def overwrite_patches(self, patches):
        BundlePatch.objects.filter(bundle=self).delete()

        for patch in patches:
            self.append_patch(patch)

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


class PatchRelation(models.Model):

    def __str__(self):
        patches = self.patches.all()
        if not patches:
            return '<Empty>'
        name = ', '.join(patch.name for patch in patches[:10])
        if len(name) > 60:
            name = name[:60] + '...'
        return name


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
    date = models.DateTimeField(default=datetime.datetime.utcnow)

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
    CATEGORY_PATCH_RELATION_CHANGED = 'patch-relation-changed'
    CATEGORY_CHECK_CREATED = 'check-created'
    CATEGORY_SERIES_CREATED = 'series-created'
    CATEGORY_SERIES_COMPLETED = 'series-completed'
    CATEGORY_CHOICES = (
        (CATEGORY_COVER_CREATED, 'Cover Letter Created'),
        (CATEGORY_PATCH_CREATED, 'Patch Created'),
        (CATEGORY_PATCH_COMPLETED, 'Patch Completed'),
        (CATEGORY_PATCH_STATE_CHANGED, 'Patch State Changed'),
        (CATEGORY_PATCH_DELEGATED, 'Patch Delegate Changed'),
        (CATEGORY_PATCH_RELATION_CHANGED, 'Patch Relation Changed'),
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
        max_length=25,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text='The category of the event.')
    date = models.DateTimeField(
        default=datetime.datetime.utcnow,
        help_text='The time this event was created.')
    actor = models.ForeignKey(
        User, related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text='The user that caused/created this event.')

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
        Cover, related_name='+', null=True, blank=True,
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

    # fields for 'patch-relation-changed-changed' events

    previous_relation = models.ForeignKey(
        PatchRelation, related_name='+', null=True, blank=True,
        on_delete=models.CASCADE)
    current_relation = models.ForeignKey(
        PatchRelation, related_name='+', null=True, blank=True,
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
    date = models.DateTimeField(default=datetime.datetime.utcnow)
    active = models.BooleanField(default=True)

    def deactivate(self):
        self.active = False
        self.save()

    def is_valid(self):
        return self.date + self.validity > datetime.datetime.utcnow()

    def save(self, *args, **kwargs):
        limit = 1 << 32
        if not self.key:
            key = '%s%s%d' % (self.user, self.email, random.randint(0, limit))
            self.key = self._meta.get_field('key').construct(key).hexdigest()
        super(EmailConfirmation, self).save()


class EmailOptout(models.Model):
    email = models.CharField(max_length=200, primary_key=True)

    @classmethod
    def is_optout(cls, email):
        email = email.lower().strip()
        return cls.objects.filter(email=email).count() > 0

    def __str__(self):
        return self.email


class PatchChangeNotification(models.Model):
    patch = models.OneToOneField(
        Patch,
        primary_key=True,
        on_delete=models.CASCADE,
    )
    last_modified = models.DateTimeField(default=datetime.datetime.utcnow)
    orig_state = models.ForeignKey(State, on_delete=models.CASCADE)

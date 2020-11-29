# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime as dt

from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver

from patchwork.models import Check
from patchwork.models import Cover
from patchwork.models import Event
from patchwork.models import Patch
from patchwork.models import PatchChangeNotification
from patchwork.models import Series


@receiver(pre_save, sender=Patch)
def patch_change_callback(sender, instance, raw, **kwargs):
    # we only want notification of modified patches
    if raw or instance.pk is None:
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

    notification.last_modified = dt.utcnow()
    notification.save()


@receiver(post_save, sender=Cover)
def create_cover_created_event(sender, instance, created, raw, **kwargs):

    def create_event(cover):
        return Event.objects.create(
            category=Event.CATEGORY_COVER_CREATED,
            project=cover.project,
            cover=cover)

    # don't trigger for items loaded from fixtures or new items
    if raw or not created:
        return

    create_event(instance)


@receiver(post_save, sender=Patch)
def create_patch_created_event(sender, instance, created, raw, **kwargs):

    def create_event(patch):
        return Event.objects.create(
            category=Event.CATEGORY_PATCH_CREATED,
            project=patch.project,
            patch=patch)

    # don't trigger for items loaded from fixtures or new items
    if raw or not created:
        return

    create_event(instance)


@receiver(pre_save, sender=Patch)
def create_patch_state_changed_event(sender, instance, raw, **kwargs):

    def create_event(patch, before, after):
        return Event.objects.create(
            category=Event.CATEGORY_PATCH_STATE_CHANGED,
            project=patch.project,
            actor=getattr(patch, '_edited_by', None),
            patch=patch,
            previous_state=before,
            current_state=after)

    # don't trigger for items loaded from fixtures or new items
    if raw or not instance.pk:
        return

    orig_patch = Patch.objects.get(pk=instance.pk)

    if orig_patch.state == instance.state:
        return

    create_event(instance, orig_patch.state, instance.state)


@receiver(pre_save, sender=Patch)
def create_patch_delegated_event(sender, instance, raw, **kwargs):

    def create_event(patch, before, after):
        return Event.objects.create(
            category=Event.CATEGORY_PATCH_DELEGATED,
            project=patch.project,
            actor=getattr(patch, '_edited_by', None),
            patch=patch,
            previous_delegate=before,
            current_delegate=after)

    # don't trigger for items loaded from fixtures or new items
    if raw or not instance.pk:
        return

    orig_patch = Patch.objects.get(pk=instance.pk)

    if orig_patch.delegate == instance.delegate:
        return

    create_event(instance, orig_patch.delegate, instance.delegate)


@receiver(pre_save, sender=Patch)
def create_patch_relation_changed_event(sender, instance, raw, **kwargs):

    def create_event(patch):
        return Event.objects.create(
            category=Event.CATEGORY_PATCH_RELATION_CHANGED,
            project=patch.project,
            actor=getattr(patch, '_edited_by', None),
            patch=patch)

    # don't trigger for items loaded from fixtures or new items
    if raw or not instance.pk:
        return

    orig_patch = Patch.objects.get(pk=instance.pk)

    if orig_patch.related == instance.related:
        return

    create_event(instance)


@receiver(pre_save, sender=Patch)
def create_patch_completed_event(sender, instance, raw, **kwargs):

    def create_event(patch):
        return Event.objects.create(
            category=Event.CATEGORY_PATCH_COMPLETED,
            project=patch.project,
            patch=patch,
            series=patch.series)

    # don't trigger for items loaded from fixtures, new items or items that
    # (still) don't have a series
    if raw or not instance.pk or not instance.series:
        return

    orig_patch = Patch.objects.get(pk=instance.pk)

    # we don't currently allow users to change a series, though this might
    # change in the future. However, we handle that here nonetheless
    if orig_patch.series == instance.series:
        return

    # if dependencies not met, don't raise event. There's also no point raising
    # events for successors since they'll have the same issue
    predecessors = Patch.objects.filter(
        series=instance.series, number__lt=instance.number)
    if predecessors.count() != instance.number - 1:
        return

    create_event(instance)

    # if this satisfies dependencies for successor patch, raise events for
    # those
    count = instance.number + 1
    for successor in Patch.objects.order_by('number').filter(
            series=instance.series, number__gt=instance.number):
        if successor.number != count:
            break

        create_event(successor)
        count += 1


@receiver(post_save, sender=Check)
def create_check_created_event(sender, instance, created, raw, **kwargs):

    def create_event(check):
        # TODO(stephenfin): It might make sense to add a 'project' field to
        # 'check' to prevent lookups here and in the REST API
        return Event.objects.create(
            category=Event.CATEGORY_CHECK_CREATED,
            project=check.patch.project,
            actor=check.user,
            patch=check.patch,
            created_check=check)

    # don't trigger for items loaded from fixtures or existing items
    if raw or not created:
        return

    create_event(instance)


@receiver(post_save, sender=Series)
def create_series_created_event(sender, instance, created, raw, **kwargs):

    def create_event(series):
        return Event.objects.create(
            category=Event.CATEGORY_SERIES_CREATED,
            project=series.project,
            series=series)

    # don't trigger for items loaded from fixtures or existing items
    if raw or not created:
        return

    create_event(instance)


@receiver(pre_save, sender=Patch)
def create_series_completed_event(sender, instance, raw, **kwargs):

    # NOTE(stephenfin): It's actually possible for this event to be fired
    # multiple times for a given series. To trigger this case, you would need
    # to send an additional patch to already exisiting series. This pattern
    # exists in the wild ('PATCH 5/n'), so we probably want to retest a series
    # in that case.

    def create_event(series):
        return Event.objects.create(
            category=Event.CATEGORY_SERIES_COMPLETED,
            project=series.project,
            series=series)

    # don't trigger for items loaded from fixtures, new items or items that
    # (still) don't have a series
    if raw or not instance.pk or not instance.series:
        return

    orig_patch = Patch.objects.get(pk=instance.pk)

    # we don't currently allow users to change a series (though this might
    # change in the future) meaning if the patch already had a series, there's
    # nothing to notify about
    if orig_patch.series:
        return

    # we can't use "series.received_all" here since we haven't actually saved
    # the instance yet so we duplicate that logic here but with an offset
    if (instance.series.received_total + 1) >= instance.series.total:
        create_event(instance.series)

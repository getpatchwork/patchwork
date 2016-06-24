# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
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

import email.parser

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import (
    CurrentUserDefault, HiddenField, HyperlinkedModelSerializer,
    ListSerializer, ModelSerializer, SerializerMethodField)

from patchwork.models import Check, Patch, Person, Project


class URLSerializer(HyperlinkedModelSerializer):
    """Just like parent but puts _url for fields"""

    def to_representation(self, instance):
        data = super(URLSerializer, self).to_representation(instance)
        for name, field in self.fields.items():
            if isinstance(field, HyperlinkedRelatedField) and name != 'url':
                data[name + '_url'] = data.pop(name)
        return data


class PersonSerializer(URLSerializer):
    class Meta:
        model = Person


class UserSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = User
        exclude = ('date_joined', 'groups', 'is_active', 'is_staff',
                   'is_superuser', 'last_login', 'password',
                   'user_permissions')


class ProjectSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Project
        exclude = ('send_notifications', 'use_tags')

    def to_representation(self, instance):
        data = super(ProjectSerializer, self).to_representation(instance)
        data['link_name'] = data.pop('linkname')
        data['list_email'] = data.pop('listemail')
        data['list_id'] = data.pop('listid')
        return data


class PatchListSerializer(ListSerializer):
    """Semi hack to make the list of patches more efficient"""
    def to_representation(self, data):
        del self.child.fields['content']
        del self.child.fields['headers']
        del self.child.fields['diff']
        return super(PatchListSerializer, self).to_representation(data)


class PatchSerializer(URLSerializer):
    class Meta:
        model = Patch
        list_serializer_class = PatchListSerializer
        read_only_fields = ('project', 'name', 'date', 'submitter', 'diff',
                            'content', 'hash', 'msgid')
        # there's no need to expose an entire "tags" endpoint, so we custom
        # render this field
        exclude = ('tags',)
    check_names = dict(Check.STATE_CHOICES)
    mbox_url = SerializerMethodField()
    state = SerializerMethodField()

    def get_state(self, obj):
        return obj.state.name

    def get_mbox_url(self, patch):
        request = self.context.get('request', None)
        return request.build_absolute_uri(patch.get_mbox_url())

    def to_representation(self, instance):
        data = super(PatchSerializer, self).to_representation(instance)
        data['checks_url'] = data['url'] + 'checks/'
        data['check'] = instance.combined_check_state
        headers = data.get('headers')
        if headers is not None:
            data['headers'] = email.parser.Parser().parsestr(headers, True)
        data['tags'] = [{'name': x.tag.name, 'count': x.count}
                        for x in instance.patchtag_set.all()]
        return data


class CurrentPatchDefault(object):
    def set_context(self, serializer_field):
        self.patch = serializer_field.context['request'].patch

    def __call__(self):
        return self.patch


class ChecksSerializer(ModelSerializer):
    user = HyperlinkedRelatedField(
        'user-detail', read_only=True, default=CurrentUserDefault())
    patch = HiddenField(default=CurrentPatchDefault())

    def run_validation(self, data):
        for val, label in Check.STATE_CHOICES:
            if label == data['state']:
                data['state'] = val
                break
        return super(ChecksSerializer, self).run_validation(data)

    def to_representation(self, instance):
        data = super(ChecksSerializer, self).to_representation(instance)
        data['state'] = instance.get_state_display()
        # drf-nested doesn't handle HyperlinkedModelSerializers properly,
        # so we have to put the url in by hand here.
        url = self.context['request'].build_absolute_uri(reverse(
            'api_1.0:patch-detail', args=[instance.patch.id]))
        data['url'] = url + 'checks/%s/' % instance.id
        data['users_url'] = data.pop('user')
        return data

    class Meta:
        model = Check
        read_only_fields = ('date', )

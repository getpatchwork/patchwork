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

from django.contrib.auth.models import User

from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import HyperlinkedModelSerializer

from patchwork.models import Person, Project


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

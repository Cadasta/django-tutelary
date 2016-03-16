import rest_framework.generics as generic
import json

from rest_framework.test import APIRequestFactory

from tutelary.engine import Object
from tutelary.models import Policy
from tutelary.mixins import PermissionRequiredMixin
from tutelary.decorators import permissioned_model
from django.db import models

from .datadir import datadir  # noqa
from .factories import UserFactory, PolicyFactory


# Include a dummy Organization model to be able to make Project
# objects.

@permissioned_model
class Organization(models.Model):
    name = models.CharField(max_length=100)

    class TutelaryMeta:
        perm_type = 'organization'
        path_fields = ('pk',)
        actions = [
            ('organization.detail',
             {'description': 'View organization'}),
        ]


# Pretty much as from Oliver.

@permissioned_model
class Project(models.Model):
    organization = models.ForeignKey(Organization)

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organization', 'pk',)
        actions = [
            ('project.users.list',
             {'description': 'List users within a project'}),
        ]


# You need something to pretend to be a serializer to make view-based
# tests go through with DRF.  It doesn't need to pretend very well...

class DummySerializer:
    data = 'dummy-data'

    def __init__(*args, **kwargs):
        pass

    def is_valid(self, *args, **kwargs):
        return True

    def save(self, *args, **kwargs):
        pass


# This is how I've been faking up views for testing.  For DRF, you
# need to have either "get_object" (for single object views) or
# "get_queryset" (for multi-object views) or both (for multi-action
# views, one of which is single object and one of which is
# multi-object, like here).  The constructor and "object" attribute
# here are just to make it so that you can pass an object to as_view.

class ProjectUsers(PermissionRequiredMixin, generic.ListCreateAPIView):
    object = None
    serializer_class = DummySerializer
    permission_required = {
        'GET': 'project.users.list',
        'POST': 'project.users.add',
    }

    def __init__(self, *args, **kwargs):
        if 'object' in kwargs:
            self.model = kwargs['object']
            self.object = kwargs['object']

    def get_object(self):
        return self.object

    def get_queryset(self):
        return [self.object]


def test_oliver_bug(db):
    clause = {
        "clause": [
            {
                "effect": "allow",
                "object": ["organization/*"],
                "action": ["organization.*"]
            },
            {
                "effect": "allow",
                "object": ["project/*/*"],
                "action": ["project.*.*"]
            }
        ]
    }

    policy = Policy.objects.create(name='default', body=json.dumps(clause))

    user = UserFactory.create(username='testuser')
    user.assign_policies(policy)

    # The "successful_authenticator" thing here is more or less
    # equivalent to calling force_authenticate, I think, but it
    # requires less "real" DRF stuff.
    req1 = APIRequestFactory().get('/check')
    req1.user = user
    req1.successful_authenticator = True
    req2 = APIRequestFactory().post('/check')
    req2.user = user
    req2.successful_authenticator = True

    org = Organization(pk='TestOrg')
    proj = Project(pk='TestProj', organization=org)

    # This works!
    rsp1 = ProjectUsers().as_view(object=proj)(req1).render()
    assert rsp1.status_code == 200

    # This works too!
    rsp2 = ProjectUsers().as_view(object=proj)(req2).render()
    assert rsp2.status_code == 201


def test_oliver_bug_2(datadir, db):  # noqa
    PolicyFactory.set_directory(str(datadir))
    PolicyFactory.create(name='org-admin', file='org-admin.json')

    policy = Policy.objects.get(name='org-admin')
    user = UserFactory.create(username='testuser')
    user.assign_policies((policy, {'organization': 'TestOrg'}))

    org1 = Organization(pk='TestOrg')
    assert user.has_perm('org.delete', org1)

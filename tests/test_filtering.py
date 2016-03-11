from django.db import models
import factory

from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
import rest_framework.generics as generics

from tutelary.decorators import permissioned_model
from tutelary.mixins import PermissionRequiredMixin

import pytest
from rest_framework.test import APIRequestFactory

from .factories import UserFactory, PolicyFactory
from .datadir import datadir  # noqa


@permissioned_model
class Org(models.Model):
    name = models.CharField(max_length=100)

    class TutelaryMeta:
        perm_type = 'org'
        path_fields = ('name',)
        actions = [('org.list', {'permissions_object': None})]


class OrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = Org
        fields = ('name',)


@permissioned_model
class Proj(models.Model):
    name = models.CharField(max_length=100)
    org = models.ForeignKey(Org)

    class TutelaryMeta:
        perm_type = 'proj'
        path_fields = ('org', 'name',)
        actions = [('proj.list', {'permissions_object': 'org'}),
                   'proj.detail',
                   'proj.delete']


class ProjSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proj
        fields = ('name', 'org')
        depth = 1


class BaseProjList(generics.ListAPIView):
    objects = None
    serializer_class = ProjSerializer

    def __init__(self, *args, **kwargs):
        if 'objects' in kwargs:
            self.objects = kwargs['objects']

    def get_queryset(self):
        return self.objects


class NormalProjList(PermissionRequiredMixin, BaseProjList):
    permission_required = 'proj.list'


class FilterProjList(PermissionRequiredMixin, BaseProjList):
    permission_required = 'proj.list'
    permission_filter_queryset = True


class DetailProjList(PermissionRequiredMixin, BaseProjList):
    permission_required = 'proj.list'
    permission_filter_queryset = ['project.detail']


class DeleteProjList(PermissionRequiredMixin, BaseProjList):
    permission_required = 'proj.list'
    permission_filter_queryset = ['project.delete']


class DetailDeleteProjList(PermissionRequiredMixin, BaseProjList):
    permission_required = 'proj.list'
    permission_filter_queryset = ['project.detail', 'project.delete']


def api_get(url, user):
    req = APIRequestFactory().get(url)
    req.user = user
    req.successful_authenticator = True
    return req


# POLICIES
#                    1  2  3  4  5
#
# org.list           X  X  X  X  X
#
# proj.list
#   org1             X  X        X
#   org2             X     X     X
#
# proj.detail
#   org1/proj1       X  X        X
#   org1/proj2       X  X        X
#   org1/proj3       X  X        X
#   org1/proj4       X           X
#   org1/proj5       X           X
#   org1/proj6       X
#   org1/proj7       X
#   org2/proj8       X     X     X
#   org2/proj9       X     X     X
#   org2/proj10      X     X     X
#
# proj.delete
#   org1/proj1       X  X
#   org1/proj2       X
#   org1/proj3       X
#   org1/proj4       X
#   org1/proj5       X
#   org1/proj6       X
#   org1/proj7       X
#   org2/proj8       X     X
#   org2/proj9       X     X
#   org2/proj10      X

@pytest.fixture(scope="function")  # noqa
def setup(datadir, db):
    users = []
    pols = []
    PolicyFactory.set_directory(str(datadir))
    for i in range(1, 6):
        user = UserFactory.create(username='user{}'.format(i))
        pol = PolicyFactory.create(name='pol{}'.format(i),
                                   file='policy-{}.json'.format(i))
        user.assign_policies(pol)
        users.append(user)
        pols.append(pol)

    orgs = []
    for i in range(1, 3):
        orgs.append(Org(name='org{}'.format(i)))

    projs = []
    for i in range(1, 11):
        projs.append(Proj(name='proj{}'.format(i),
                          org=orgs[0] if i < 8 else orgs[1]))

    return (users, pols, orgs, projs)


def test_normal_listing(datadir, setup):  # noqa
    users, pols, orgs, projs = setup
    r1, r2, r3, r4, r5 = map(lambda u: api_get('/projs', u), users)

    view = NormalProjList().as_view(objects=projs)
    assert len(view(r1).render().data) == 10
    with pytest.raises(PermissionDenied):
        rsp2 = view(r2).render()  # noqa
    with pytest.raises(PermissionDenied):
        rsp3 = view(r3).render()  # noqa
    with pytest.raises(PermissionDenied):
        rsp4 = view(r4).render()  # noqa
    assert len(view(r5).render().data) == 10


def test_basic_filter_listing(datadir, setup):  # noqa
    users, pols, orgs, projs = setup
    r1, r2, r3, r4, r5 = map(lambda u: api_get('/projs', u), users)

    view = FilterProjList().as_view(objects=projs)
    assert len(view(r1).render().data) == 10
    assert len(view(r2).render().data) == 7
    assert len(view(r3).render().data) == 3
    assert len(view(r4).render().data) == 0
    assert len(view(r5).render().data) == 10


def test_detail_filter_listing(datadir, setup):  # noqa
    users, pols, orgs, projs = setup
    r1, r2, r3, r4, r5 = map(lambda u: api_get('/projs', u), users)

    view = DetailProjList().as_view(objects=projs)
    assert len(view(r1).render().data) == 10
    assert len(view(r2).render().data) == 3
    assert len(view(r3).render().data) == 3
    assert len(view(r4).render().data) == 0
    assert len(view(r5).render().data) == 8


def test_delete_filter_listing(datadir, setup):  # noqa
    users, pols, orgs, projs = setup
    r1, r2, r3, r4, r5 = map(lambda u: api_get('/projs', u), users)

    view = DeleteProjList().as_view(objects=projs)
    assert len(view(r1).render().data) == 10
    assert len(view(r2).render().data) == 1
    assert len(view(r3).render().data) == 2
    assert len(view(r4).render().data) == 0
    assert len(view(r5).render().data) == 0


def test_detail_delete_filter_listing(datadir, setup):  # noqa
    users, pols, orgs, projs = setup
    r1, r2, r3, r4, r5 = map(lambda u: api_get('/projs', u), users)

    view = DetailDeleteProjList().as_view(objects=projs)
    assert len(view(r1).render().data) == 10
    assert len(view(r2).render().data) == 1
    assert len(view(r3).render().data) == 2
    assert len(view(r4).render().data) == 0
    assert len(view(r5).render().data) == 0

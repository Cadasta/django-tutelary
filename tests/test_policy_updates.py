from tutelary.models import (
    PermissionSet, Policy, PolicyInstance
)
from tutelary.engine import Object
from django.contrib.auth.models import User
import pytest
from .datadir import datadir  # noqa


@pytest.fixture(scope="function")  # noqa
def setup(datadir, db):
    user1 = User.objects.create(username='user1')
    user1.save()
    user2 = User.objects.create(username='user2')
    user1.save()
    user3 = User.objects.create(username='user3')
    user1.save()

    def_pol = Policy.objects.create(
        name='def',
        body=datadir.join('default-policy.json').read()
    )
    def_pol.save()
    org_pol = Policy.objects.create(
        name='org',
        body=datadir.join('org-policy-1.json').read()
    )
    org_pol.save()
    prj_pol = Policy.objects.create(
        name='prj',
        body=datadir.join('project-policy-1.json').read()
    )
    prj_pol.save()

    user1.assign_policies(def_pol)
    user2.assign_policies(def_pol,
                          (org_pol, {'organisation': 'Cadasta'}))
    user3.assign_policies(def_pol,
                          (org_pol, {'organisation': 'Cadasta'}),
                          (prj_pol, {'organisation': 'Cadasta',
                                     'project': 'TestProj'}))

    return (user1, user2, user3, def_pol, org_pol, prj_pol)


def check(nuser=None, npol=None, npolin=None, npset=None):
    if nuser is not None:
        assert User.objects.count() == nuser
    if npol is not None:
        assert Policy.objects.count() == npol
    if npolin is not None:
        assert PolicyInstance.objects.count() == npolin
    if npset is not None:
        assert PermissionSet.objects.count() == npset


def test_policy_update_1(datadir, setup):  # noqa
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    check(nuser=3, npol=3, npolin=6, npset=3)

    obj1 = Object('parcel/Cadasta/TestProj/123')
    obj2 = Object('parcel/Cadasta/Proj2/114')
    obj3 = Object('parcel/SkunkWorks/SR-71/Area51')

    assert not user1.has_perm('parcel.edit', obj1)
    assert user2.has_perm('parcel.edit', obj1)
    assert user3.has_perm('parcel.edit', obj1)

    assert not user1.has_perm('parcel.view', obj2)
    assert user2.has_perm('parcel.view', obj2)
    assert user3.has_perm('parcel.view', obj2)

    assert not user1.has_perm('parcel.view', obj3)
    assert not user2.has_perm('parcel.view', obj3)
    assert not user3.has_perm('parcel.view', obj3)

    org_pol.body = datadir.join('org-policy-2.json').read()
    org_pol.save()

    check(nuser=3, npol=3, npolin=6, npset=3)

    assert not user1.has_perm('parcel.edit', obj1)
    assert not user2.has_perm('parcel.edit', obj1)
    assert not user3.has_perm('parcel.edit', obj1)

    assert not user1.has_perm('parcel.view', obj2)
    assert user2.has_perm('parcel.view', obj2)
    assert user3.has_perm('parcel.view', obj2)

    assert not user1.has_perm('parcel.view', obj3)
    assert not user2.has_perm('parcel.view', obj3)
    assert not user3.has_perm('parcel.view', obj3)


def test_policy_update_2(datadir, setup):  # noqa
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    check(nuser=3, npol=3, npolin=6, npset=3)

    obj1 = Object('parcel/Cadasta/TestProj/123')
    obj2 = Object('parcel/Cadasta/Proj2/114')
    obj3 = Object('parcel/SkunkWorks/SR-71/Area51')
    obj4 = Object('party/Cadasta/TestProj/345')

    assert user3.has_perm('parcel.edit', obj1)
    assert not user3.has_perm('parcel.view', obj1)
    assert user3.has_perm('parcel.view', obj2)
    assert not user3.has_perm('parcel.view', obj3)
    assert not user3.has_perm('party.view', obj4)

    prj_pol.body = datadir.join('project-policy-2.json').read()
    prj_pol.save()

    check(nuser=3, npol=3, npolin=6, npset=3)

    assert user3.has_perm('parcel.edit', obj1)
    assert not user3.has_perm('parcel.view', obj1)
    assert user3.has_perm('parcel.view', obj2)
    assert not user3.has_perm('parcel.view', obj3)
    assert user3.has_perm('party.view', obj4)

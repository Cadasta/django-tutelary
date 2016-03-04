from tutelary.models import (
    PermissionSet, Policy, Role, PolicyInstance
)
from tutelary.engine import Object
from django.contrib.auth.models import User
import pytest
from .factories import UserFactory, PolicyFactory, RoleFactory
from .datadir import datadir  # noqa


@pytest.fixture(scope="function")  # noqa
def setup(datadir, db):
    user1 = UserFactory.create(username='user1')
    user2 = UserFactory.create(username='user2')
    user3 = UserFactory.create(username='user3')

    PolicyFactory.set_directory(str(datadir))
    def_pol = PolicyFactory.create(name='def', file='default-policy.json')
    org_pol = PolicyFactory.create(name='org', file='org-policy-1.json')
    prj_pol = PolicyFactory.create(name='prj', file='project-policy-1.json')

    org_role = RoleFactory.create(
        name='cadasta_org', policies=[def_pol, org_pol],
        variables={'organisation': 'Cadasta'}
    )
    prj_role = RoleFactory.create(
        name='testproj_proj', policies=[def_pol, org_pol, prj_pol],
        variables={'organisation': 'Cadasta', 'project': 'TestProj'}
    )

    user1.assign_policies(def_pol)
    user2.assign_policies((org_role, {'organisation': 'Cadasta'}))
    user3.assign_policies((prj_role, {'organisation': 'Cadasta',
                                      'project': 'TestProj'}))

    return (user1, user2, user3, def_pol, org_pol, prj_pol, org_role, prj_role)


def check(nuser=None, npol=None, nrole=None, npolin=None, npset=None):
    if nuser is not None:
        assert User.objects.count() == nuser
    if npol is not None:
        assert Policy.objects.count() == npol
    if nrole is not None:
        assert Role.objects.count() == nrole
    if npolin is not None:
        assert PolicyInstance.objects.count() == npolin
    if npset is not None:
        assert PermissionSet.objects.count() == npset


def test_role_policy_update(datadir, setup):  # noqa
    u1, u2, u3, def_pol, org_pol, prj_pol, org_role, prj_role = setup

    obj1 = Object('parcel/Cadasta/TestProj/123')
    obj2 = Object('parcel/Cadasta/Proj2/114')
    obj3 = Object('parcel/SkunkWorks/SR-71/Area51')

    check(nuser=3, npol=3, nrole=2, npolin=6, npset=3)

    assert not u1.has_perm('parcel.edit', obj1)
    assert u2.has_perm('parcel.edit', obj1)
    assert u3.has_perm('parcel.edit', obj1)

    assert not u1.has_perm('parcel.view', obj2)
    assert u2.has_perm('parcel.view', obj2)
    assert u3.has_perm('parcel.view', obj2)

    assert not u1.has_perm('parcel.view', obj3)
    assert not u2.has_perm('parcel.view', obj3)
    assert not u3.has_perm('parcel.view', obj3)

    assert str(org_pol) == 'org'
    org_pol.body = datadir.join('org-policy-2.json').read()
    org_pol.save()

    check(nuser=3, npol=3, nrole=2, npolin=6, npset=3)

    assert not u1.has_perm('parcel.edit', obj1)
    assert not u2.has_perm('parcel.edit', obj1)
    assert not u3.has_perm('parcel.edit', obj1)

    assert not u1.has_perm('parcel.view', obj2)
    assert u2.has_perm('parcel.view', obj2)
    assert u3.has_perm('parcel.view', obj2)

    assert not u1.has_perm('parcel.view', obj3)
    assert not u2.has_perm('parcel.view', obj3)
    assert not u3.has_perm('parcel.view', obj3)

from tutelary.models import (
    PermissionSet, Policy, Role, PolicyInstance, RolePolicyAssign,
)
from tutelary.engine import Object
from django.contrib.auth.models import User
import pytest
from .factories import UserFactory, PolicyFactory, RoleFactory
from .datadir import datadir  # noqa
from .settings import DEBUG


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

    org_pol.body = datadir.join('org-policy-2.json').read()
    org_pol.save()
    for u in (u1, u2, u3):
        del u.permset_tree

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


def debug(s):
    if DEBUG:
        print(s)
        print()
        for p in Policy.objects.all():
            print(repr(p))
        print()
        for r in Role.objects.all():
            print(repr(r))
        print()
        for rpa in RolePolicyAssign.objects.all():
            print(repr(rpa))
        print()
        for pi in PolicyInstance.objects.all():
            print(repr(pi))
        print()
        for pset in PermissionSet.objects.all():
            print(repr(pset))
        print()
        for user in User.objects.all():
            print((user, user.permissionset.first().pk))
        print()


def test_role_policies_update(datadir, setup):  # noqa
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

    debug('HERE 1')
    replacement_role = RoleFactory.create(
        name='replacement_role', policies=[def_pol, org_pol],
        variables=org_role.variables
    )
    u3.assign_policies(replacement_role)
    prj_role.delete()
    debug('HERE 2')

    check(nuser=3, npol=3, nrole=2, npolin=5, npset=3)

    assert not u1.has_perm('parcel.edit', obj1)
    assert u2.has_perm('parcel.edit', obj1)
    assert u3.has_perm('parcel.edit', obj1)

    assert not u1.has_perm('parcel.view', obj2)
    assert u2.has_perm('parcel.view', obj2)
    assert u3.has_perm('parcel.view', obj2)

    assert not u1.has_perm('parcel.view', obj3)
    assert not u2.has_perm('parcel.view', obj3)
    assert not u3.has_perm('parcel.view', obj3)


def test_user_role_update(datadir, setup):  # noqa
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

    u3.assign_policies(def_pol)

    check(nuser=3, npol=3, nrole=2, npolin=3, npset=2)

    assert not u1.has_perm('parcel.edit', obj1)
    assert u2.has_perm('parcel.edit', obj1)
    assert not u3.has_perm('parcel.edit', obj1)

    assert not u1.has_perm('parcel.view', obj2)
    assert u2.has_perm('parcel.view', obj2)
    assert not u3.has_perm('parcel.view', obj2)

    assert not u1.has_perm('parcel.view', obj3)
    assert not u2.has_perm('parcel.view', obj3)
    assert not u3.has_perm('parcel.view', obj3)

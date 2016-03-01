from tutelary.models import assign_user_policies
from tutelary.engine import Object, Action
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_backends
import pytest
from .factories import UserFactory, PolicyFactory
from .datadir import datadir  # noqa


@pytest.fixture(scope="function")  # noqa
def setup(datadir, db):
    user1 = UserFactory.create(username='user1')
    user2 = UserFactory.create(username='user2')
    user3 = UserFactory.create(username='user3')
    user4 = UserFactory.create(username='user4')
    user5 = UserFactory.create(username='user5')

    PolicyFactory.set_directory(str(datadir))
    def_pol = PolicyFactory.create(name='def', file='default-policy.json')
    org_pol = PolicyFactory.create(name='org', file='org-policy.json')
    prj_pol = PolicyFactory.create(name='prj', file='project-policy.json')
    deny_pol = PolicyFactory.create(name='prj', file='deny-policy.json')

    Action.register(['party.list', 'party.view', 'parcel.list', 'parcel.view',
                     'party.edit', 'parcel.edit'])

    assign_user_policies(None, def_pol)
    user1.assign_policies(def_pol)
    user2.assign_policies(def_pol,
                          (org_pol, {'organisation': 'Cadasta'}))
    user3.assign_policies(def_pol,
                          (org_pol, {'organisation': 'Cadasta'}),
                          (prj_pol, {'organisation': 'Cadasta',
                                     'project': 'TestProj'}),
                          (deny_pol, {'organisation': 'Cadasta',
                                      'project': 'Proj2'}))
    user4.assign_policies(def_pol,
                          (org_pol, {'organisation': 'OtherOrg'}))
    user5.assign_policies(def_pol,
                          (org_pol, {'organisation': 'Cadasta'}),
                          (prj_pol, {'organisation': 'Cadasta',
                                     'project': 'TestProj2'}))

    return (user1, user2, user3, user4, user5,
            def_pol, org_pol, prj_pol, deny_pol)


def test_basic(datadir, setup):  # noqa
    u1, u2, u3, u4, u5, def_pol, org_pol, prj_pol, deny_pol = setup

    obj1 = Object('parcel/Cadasta/TestProj/123')
    assert not u1.has_perm('parcel.edit', obj1)
    assert u2.has_perm('parcel.edit', obj1)
    assert not u3.has_perm('parcel.edit', obj1)

    obj2 = Object('parcel/Cadasta/Proj2/114')
    assert not u1.has_perm('parcel.view', obj2)
    assert u2.has_perm('parcel.view', obj2)
    assert u3.has_perm('parcel.view', obj2)

    obj3 = Object('parcel/SkunkWorks/SR-71/Area51')
    assert not u1.has_perm('parcel.view', obj3)
    assert not u2.has_perm('parcel.view', obj3)
    assert not u3.has_perm('parcel.view', obj3)


def test_basic_anonymous(datadir, setup):  # noqa
    u1, u2, u3, u4, u5, def_pol, org_pol, prj_pol, deny_pol = setup

    obj1 = Object('parcel/Cadasta/TestProj/123')
    assert not AnonymousUser().has_perm('parcel.edit', obj1)
    assign_user_policies(None,
                         def_pol,
                         (org_pol, {'organisation': 'Cadasta'}))
    assert AnonymousUser().has_perm('parcel.edit', obj1)


def test_collective(datadir, setup):  # noqa
    u1, u2, u3, u4, u5, def_pol, org_pol, prj_pol, deny_pol = setup

    parcel1 = Object('parcel/Cadasta/TestProj/123')
    proj1 = Object('project/Cadasta/TestProj')
    assert not u1.has_perm('parcel.view', parcel1)
    assert not u1.has_perm('parcel.list', proj1)
    assert u2.has_perm('parcel.view', parcel1)
    assert u2.has_perm('parcel.list', proj1)
    assert u3.has_perm('parcel.view', parcel1)
    assert u3.has_perm('parcel.list', proj1)

    parcel2 = Object('parcel/Cadasta/Proj2/114')
    proj2 = Object('project/Cadasta/Proj2')
    assert not u1.has_perm('parcel.view', parcel2)
    assert not u1.has_perm('parcel.list', proj2)
    assert u2.has_perm('parcel.view', parcel2)
    assert u2.has_perm('parcel.list', proj2)
    assert u3.has_perm('parcel.view', parcel2)
    assert not u3.has_perm('parcel.list', proj2)

    parcel3 = Object('parcel/SkunkWorks/SR-71/Area51')
    proj3 = Object('project/SkunkWorks/SR-71')
    assert not u1.has_perm('parcel.view', parcel3)
    assert not u1.has_perm('parcel.list', proj3)
    assert not u2.has_perm('parcel.view', parcel3)
    assert not u2.has_perm('parcel.list', proj3)
    assert not u3.has_perm('parcel.view', parcel3)
    assert not u3.has_perm('parcel.list', proj3)


def test_permitted_actions(datadir, setup):  # noqa
    u1, u2, u3, u4, u5, def_pol, org_pol, prj_pol, deny_pol = setup

    def chk(u, obj):
        return [str(a) for
                a in get_backends()[0].permitted_actions(u, lambda a: obj)]
    parcel1 = Object('parcel/Cadasta/TestProj/123')
    proj1 = Object('project/Cadasta/TestProj')
    assert chk(u1, parcel1) == []
    assert chk(u1, proj1) == []
    assert set(chk(u2, parcel1)) == set(['parcel.view', 'parcel.edit'])
    assert set(chk(u2, proj1)) == set(['parcel.list', 'party.list'])
    assert chk(u3, parcel1) == ['parcel.view']
    assert set(chk(u3, proj1)) == set(['parcel.list', 'party.list'])
    assert chk(u4, parcel1) == []
    assert chk(u4, proj1) == []
    assert set(chk(u5, parcel1)) == set(['parcel.view', 'parcel.edit'])
    assert set(chk(u5, proj1)) == set(['parcel.list', 'party.list'])


def test_permitted_actions_no_policies(datadir, setup):  # noqa
    u1, u2, u3, u4, u5, def_pol, org_pol, prj_pol, deny_pol = setup

    def chk(u, obj):
        return get_backends()[0].permitted_actions(u, lambda a: obj)

    other_user = UserFactory.create(username='other_user')
    parcel1 = Object('parcel/Cadasta/TestProj/123')
    proj1 = Object('project/Cadasta/TestProj')
    assert chk(other_user, parcel1) == []
    assert chk(other_user, proj1) == []

from tutelary.models import (assign_user_policies, Role)
from tutelary.engine import Object, Action
from tutelary.exceptions import RoleVariableException
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

    return (user1, user2, user3, user4, user5,
            def_pol, org_pol, prj_pol, deny_pol)


def test_roles_creation(datadir, setup):  # noqa
    u1, u2, u3, u4, u5, def_pol, org_pol, prj_pol, deny_pol = setup

    cadasta_org_role = Role.objects.create(
        name='cadasta_org', policies=[def_pol, org_pol],
        variables={'organisation': 'Cadasta'}
    )
    cadasta_org_role.save()
    assert str(cadasta_org_role) == 'cadasta_org'
    testproj_proj_role = Role.objects.create(
        name='testproj_proj', policies=[def_pol, org_pol, prj_pol],
        variables={'organisation': 'Cadasta', 'project': 'TestProj'}
    )
    testproj_proj_role.save()
    proj2_proj_role = Role.objects.create(
        name='proj2_proj', policies=[def_pol, org_pol, prj_pol],
        variables={'organisation': 'Cadasta', 'project': 'Proj2'}
    )
    proj2_proj_role.save()
    other_org_role = Role.objects.create(
        name='other_org', policies=[def_pol, org_pol],
        variables={'organisation': 'OtherOrg'}
    )
    other_org_role.save()

    assign_user_policies(None, cadasta_org_role)
    u1.assign_policies(def_pol)
    u2.assign_policies(cadasta_org_role)
    u3.assign_policies(testproj_proj_role,
                       (deny_pol, {'organisation': 'Cadasta',
                                   'project': 'Proj2'}))
    u4.assign_policies(other_org_role)
    u5.assign_policies(proj2_proj_role)

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


def test_roles_policies_variables(datadir, setup):  # noqa
    u1, u2, u3, u4, u5, def_pol, org_pol, prj_pol, deny_pol = setup

    assert def_pol.variable_names() == set()
    assert org_pol.variable_names() == {'organisation'}
    assert prj_pol.variable_names() == {'organisation', 'project'}

    org_role = Role.objects.create(
        name='cadasta_org', policies=[def_pol, org_pol],
        variables={'organisation': 'Cadasta'}
    )
    assert org_role.variable_names() == {'organisation'}
    testproj_proj_role = Role.objects.create(
        name='testproj_proj', policies=[def_pol, org_pol, prj_pol],
        variables={'organisation': 'Cadasta', 'project': 'TestProj'}
    )
    testproj_proj_role.save()
    assert testproj_proj_role.variable_names() == {'organisation', 'project'}

    with pytest.raises(RoleVariableException):
        bad_role = Role.objects.create(
            name='cadasta_org', policies=[def_pol, org_pol]
        )
        bad_role.save()

    ok_role = Role.objects.create(
        name='test_org', policies=[def_pol, org_pol],
        variables={'organisation': 'TestOrg', 'project': 'NewProj'}
    )
    ok_role.save()

from tutelary.models import Role, assign_user_policies, user_assigned_policies

from .datadir import datadir  # noqa
from .factories import UserFactory, PolicyFactory, RoleFactory

import pytest


#  - Create 3 policies, 1 without variables, 2 with
#  - Create roles:
#      * 2 from no-var policy
#      * 2 from one var policy
#      * 2 from combinations of policies

@pytest.fixture(scope="function")  # noqa
def setup(datadir, db):
    users = []
    for i in range(1, 11):
        users.append(UserFactory.create(username='user{}'.format(i)))

    PolicyFactory.set_directory(str(datadir))
    sys_admin_p = PolicyFactory.create(name='sys-admin', file='sys-admin.json')
    org_admin_p = PolicyFactory.create(name='org-admin', file='org-admin.json')
    proj_mgr_p = PolicyFactory.create(name='proj-mgr', file='proj-mgr.json')
    pols = [sys_admin_p, org_admin_p, proj_mgr_p]

    roles = []
    sys_admin_r = RoleFactory.create(
        name='sys-admin', policies=[pols[0]],
        variables={}
    )
    org_admin_1_r = RoleFactory.create(
        name='org-admin', policies=[pols[1]],
        variables={'org': 'Org1'}
    )
    org_admin_2_r = RoleFactory.create(
        name='org-admin', policies=[pols[1]],
        variables={'org': 'Org2'}
    )
    proj_mgr_1_r = RoleFactory.create(
        name='proj-mgr', policies=[pols[2]],
        variables={'org': 'Org1', 'proj': 'Proj1'}
    )
    proj_mgr_2_r = RoleFactory.create(
        name='proj-mgr', policies=[pols[2]],
        variables={'org': 'Org2', 'proj': 'Proj2'}
    )
    roles = [sys_admin_r,
             org_admin_1_r, org_admin_2_r,
             proj_mgr_1_r, proj_mgr_2_r]

    users[1].assign_policies(sys_admin_p)
    users[2].assign_policies(sys_admin_r)
    users[3].assign_policies(org_admin_1_r)
    users[4].assign_policies(org_admin_2_r)
    users[5].assign_policies(org_admin_1_r, org_admin_2_r)
    users[6].assign_policies(org_admin_1_r, proj_mgr_2_r)
    users[7].assign_policies(proj_mgr_1_r)
    users[8].assign_policies((org_admin_p, {'org': 'Org3'}))
    users[9].assign_policies((org_admin_p, {'org': 'Org3'}),
                             (proj_mgr_p, {'org': 'Org3', 'proj': 'Proj3'}))
    assign_user_policies(None, (org_admin_p, {'org': 'Sandbox'}))

    return (users, pols, roles)


def test_role_lookup(datadir, setup):  # noqa
    users, pols, roles = setup
    (sys_admin_r,
     org_admin_1_r, org_admin_2_r,
     proj_mgr_1_r, proj_mgr_2_r) = roles

    assert list(Role.objects.filter(name='sys-admin')) == [sys_admin_r]
    assert (list(Role.objects.filter(name='sys-admin')) == [sys_admin_r])
    assert (set(Role.objects.filter(name='org-admin')) ==
            set([org_admin_1_r, org_admin_2_r]))
    assert (list(Role.objects.filter(name='org-admin',
                                     variables={'org': 'Org1'})) ==
            [org_admin_1_r])
    assert (list(Role.objects.filter(name='org-admin',
                                     variables={'org': 'Org2'})) ==
            [org_admin_2_r])
    assert (list(Role.objects.filter(name='org-admin',
                                     variables={'org': 'Org3'})) == [])
    assert (set(Role.objects.filter(name='proj-mgr')) ==
            set([proj_mgr_1_r, proj_mgr_2_r]))
    assert (list(Role.objects.filter(name='proj-mgr',
                                     variables={'org': 'Org1',
                                                'proj': 'Proj1'})) ==
            [proj_mgr_1_r])
    assert (list(Role.objects.filter(name='proj-mgr',
                                     variables={'org': 'Org2',
                                                'proj': 'Proj2'})) ==
            [proj_mgr_2_r])
    assert (list(Role.objects.filter(name='proj-mgr',
                                     variables={'org': 'Org3',
                                                'proj': 'Proj3'})) == [])


def test_lookup_user_policies_and_roles(datadir, setup):  # noqa
    users, pols, roles = setup
    assert user_assigned_policies(None) == []
    assert users[0].assigned_policies() == []
    assert users[1].assigned_policies() == []

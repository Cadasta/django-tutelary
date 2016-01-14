from tutelary.models import (
    PermissionSet, Policy, PolicyInstance, PolicyInstanceAssign
)
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
        body=datadir.join('org-policy.json').read()
    )
    org_pol.save()
    prj_pol = Policy.objects.create(
        name='prj',
        body=datadir.join('project-policy.json').read()
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


@pytest.fixture(scope="function")  # noqa
def debug(db):
    def fn(s):
        print(s)
        psets = PermissionSet.objects.all()
        print('PSets:', list(map(lambda pset:
                                 str(pset.pk) + ': ' + pset.data, psets)))
        pis = PolicyInstance.objects.all()
        print('PolInsts:', list(map(lambda pi:
                                    str(pi.pk) + ': ' + pi.policy.name + ' ' +
                                    str(pi.variables), pis)))
        pas = PolicyInstanceAssign.objects.all()
        print('PolInstAssigns:', list(map(lambda pa:
                                          str(pa.pk) + ': PI ' +
                                          str(pa.policy_instance.pk) +
                                          ' -> PSet ' +
                                          str(pa.permission_set.pk), pas)))
    return fn


@pytest.mark.django_db  # noqa
def test_permission_set_creation(datadir, setup):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    assert User.objects.count() == 3
    assert Policy.objects.count() == 3
    assert PolicyInstance.objects.count() == 3
    assert PermissionSet.objects.count() == 3
    assert PolicyInstanceAssign.objects.count() == 6


@pytest.mark.django_db  # noqa
def test_permission_set_change(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user2.assign_policies(def_pol,
                          (org_pol, {'organisation': 'DummyCorp'}))
    debug('AFTER')

    assert User.objects.count() == 3
    assert Policy.objects.count() == 3
    assert PolicyInstance.objects.count() == 4
    assert PermissionSet.objects.count() == 3
    assert PolicyInstanceAssign.objects.count() == 6


@pytest.mark.django_db  # noqa
def test_permission_set_clear(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.assign_policies()
    user2.assign_policies()
    user3.assign_policies()
    debug('AFTER')

    assert User.objects.count() == 3
    assert Policy.objects.count() == 3
    assert PolicyInstance.objects.count() == 0
    assert PolicyInstanceAssign.objects.count() == 0
    # Remember the empty permission set!
    assert PermissionSet.objects.count() == 1


@pytest.mark.django_db  # noqa
def test_permission_set_clear2(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.assign_policies()
    debug('AFTER')

    assert User.objects.count() == 3
    assert Policy.objects.count() == 3
    assert PolicyInstance.objects.count() == 3
    assert PolicyInstanceAssign.objects.count() == 5
    # Remember the empty permission set!
    assert PermissionSet.objects.count() == 3


@pytest.mark.django_db  # noqa
def test_permission_user_deletion(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user3.delete()
    debug('AFTER')

    assert User.objects.count() == 2
    assert Policy.objects.count() == 3
    assert PolicyInstance.objects.count() == 2
    assert PolicyInstanceAssign.objects.count() == 3
    # No empty permission set here: the user is gone!
    assert PermissionSet.objects.count() == 2


@pytest.mark.django_db  # noqa
def test_permission_user_deletion2(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.delete()
    user2.delete()
    user3.delete()
    debug('AFTER')

    assert User.objects.count() == 0
    assert Policy.objects.count() == 3
    assert PolicyInstance.objects.count() == 0
    assert PolicyInstanceAssign.objects.count() == 0
    # No empty permission set here: the users are gone!
    assert PermissionSet.objects.count() == 0

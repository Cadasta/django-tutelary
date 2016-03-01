from tutelary.models import (
    PermissionSet, Policy, PolicyInstance
)
from django.contrib.auth.models import User
import pytest
from .factories import UserFactory, PolicyFactory
from .datadir import datadir  # noqa


@pytest.fixture(scope="function")  # noqa
def setup(datadir, db):
    user1 = UserFactory.create(username='user1')
    user2 = UserFactory.create(username='user2')
    user3 = UserFactory.create(username='user3')

    PolicyFactory.set_directory(str(datadir))
    def_pol = PolicyFactory.create(name='def', file='default-policy.json')
    org_pol = PolicyFactory.create(name='org', file='org-policy.json')
    prj_pol = PolicyFactory.create(name='prj', file='project-policy.json')

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
        print('PSets:', list(map(
            lambda pset: str(pset.pk) + ': ' + repr(pset.tree()),
            psets)
        ))
        pis = PolicyInstance.objects.all()
        print('PolInsts:', list(map(lambda pi:
                                    str(pi.pk) + ': ' + str(pi.pset.id) + ' ' +
                                    pi.policy.name + ' ' +
                                    str(pi.variables), pis)))
    return fn


def check(nuser=None, npol=None, npolin=None, npset=None):
    if nuser is not None:
        assert User.objects.count() == nuser
    if npol is not None:
        assert Policy.objects.count() == npol
    if npolin is not None:
        assert PolicyInstance.objects.count() == npolin
    if npset is not None:
        assert PermissionSet.objects.count() == npset


@pytest.mark.django_db  # noqa
def test_permission_set_creation(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('CREATION')
    check(nuser=3, npol=3, npolin=6, npset=3)


@pytest.mark.django_db  # noqa
def test_permission_set_change(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user2.assign_policies(def_pol,
                          (org_pol, {'organisation': 'DummyCorp'}))
    debug('AFTER')

    check(nuser=3, npol=3, npolin=6, npset=3)


@pytest.mark.django_db  # noqa
def test_permission_set_clear_all(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.assign_policies()
    user2.assign_policies()
    user3.assign_policies()
    debug('AFTER')

    # Remember the empty permission set!
    check(nuser=3, npol=3, npolin=0, npset=1)


@pytest.mark.django_db  # noqa
def test_permission_set_clear_single(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.assign_policies()
    debug('AFTER')

    # Remember the empty permission set!
    check(nuser=3, npol=3, npolin=5, npset=3)


@pytest.mark.django_db  # noqa
def test_permission_user_deletion_single(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user3.delete()
    debug('AFTER')

    # No empty permission set here: the user is gone!
    check(nuser=2, npol=3, npolin=3, npset=2)


@pytest.mark.django_db  # noqa
def test_permission_user_deletion_all(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.delete()
    user2.delete()
    user3.delete()
    debug('AFTER')

    # No empty permission set here: the users are gone!
    check(nuser=0, npol=3, npolin=0, npset=0)

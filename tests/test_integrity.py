from tutelary.models import (
    PermissionSet, Policy, PolicyInstance
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
def test_permission_set_clear(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.assign_policies()
    user2.assign_policies()
    user3.assign_policies()
    debug('AFTER')

    # Remember the empty permission set!
    check(nuser=3, npol=3, npolin=0, npset=1)


@pytest.mark.django_db  # noqa
def test_permission_set_clear2(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.assign_policies()
    debug('AFTER')

    # Remember the empty permission set!
    check(nuser=3, npol=3, npolin=5, npset=3)


@pytest.mark.django_db  # noqa
def test_permission_user_deletion(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user3.delete()
    debug('AFTER')

    # No empty permission set here: the user is gone!
    check(nuser=2, npol=3, npolin=3, npset=2)


@pytest.mark.django_db  # noqa
def test_permission_user_deletion2(datadir, setup, debug):
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    debug('BEFORE')
    user1.delete()
    user2.delete()
    user3.delete()
    debug('AFTER')

    # No empty permission set here: the users are gone!
    check(nuser=0, npol=3, npolin=0, npset=0)

from tutelary.models import Policy
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


def test_basic(datadir, setup):  # noqa
    user1, user2, user3, def_pol, org_pol, prj_pol = setup

    obj1 = Object('parcel/Cadasta/TestProj/123')
    assert not user1.has_perm('parcel.edit', obj1)
    assert user2.has_perm('parcel.edit', obj1)
    assert not user3.has_perm('parcel.edit', obj1)

    obj2 = Object('parcel/Cadasta/Proj2/114')
    assert not user1.has_perm('parcel.view', obj2)
    assert user2.has_perm('parcel.view', obj2)
    assert user3.has_perm('parcel.view', obj2)

    obj3 = Object('parcel/SkunkWorks/SR-71/Area51')
    assert not user1.has_perm('parcel.view', obj3)
    assert not user2.has_perm('parcel.view', obj3)
    assert not user3.has_perm('parcel.view', obj3)

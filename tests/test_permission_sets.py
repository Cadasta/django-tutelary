from tutelary.base import PermissionSet, Policy, Action, Object
from .datadir import datadir  # noqa


def test_permission_set_creation(datadir):  # noqa
    pol = Policy(json=datadir.join('test-policy-1.json').read())
    pset = PermissionSet()
    pset.add(policy=pol)
    assert pset.allow(Action('parcel.view'),
                      Object('Cadasta/Batangas/parcel/123'))
    assert not pset.allow(Action('parcel.edit'),
                          Object('Cadasta/Batangas/parcel/123'))


def test_permission_set_policies(datadir):  # noqa
    v = {'organisation': 'Cadasta', 'project': 'Test'}
    pnames = ['default-policy.json', 'org-policy.json', 'project-policy.json']

    sapols = map(lambda f: Policy(json=datadir.join(f).read(), variables=v),
                 pnames + ['sys-admin-policy.json'])
    sapset = PermissionSet(policies=sapols)

    oapols = map(lambda f: Policy(json=datadir.join(f).read(), variables=v),
                 pnames + ['org-admin-policy.json'])
    oapset = PermissionSet(policies=oapols)

    dcpols = map(lambda f: Policy(json=datadir.join(f).read(), variables=v),
                 pnames + ['data-collector-policy.json'])
    dcpset = PermissionSet(policies=dcpols)

    parcel_view = Action('parcel.view')
    parcel_edit = Action('parcel.edit')
    party_create = Action('party.create')
    admin_assign = Action('admin.assign-role')
    admin_invite = Action('admin.invite')
    parties = Object('Cadasta/Test/party')
    parcel123 = Object('Cadasta/Test/parcel/123')
    org = Object('org/Cadasta')
    useriross = Object('user/iross')

    assert sapset.allow(parcel_view, parcel123)
    assert sapset.allow(parcel_edit, parcel123)
    assert sapset.allow(party_create, parties)
    assert sapset.allow(admin_assign, useriross)
    assert sapset.allow(admin_invite, useriross)
    assert sapset.allow(admin_invite, org)

    assert oapset.allow(parcel_view, parcel123)
    assert oapset.allow(parcel_edit, parcel123)
    assert oapset.allow(party_create, parties)
    assert not oapset.allow(admin_assign, useriross)
    assert oapset.allow(admin_invite, useriross)
    assert oapset.allow(admin_invite, org)

    assert dcpset.allow(parcel_view, parcel123)
    assert dcpset.allow(parcel_edit, parcel123)
    assert not dcpset.allow(party_create, parties)
    assert not dcpset.allow(admin_assign, useriross)
    assert not dcpset.allow(admin_invite, useriross)
    assert not dcpset.allow(admin_invite, org)

from tutelary.engine import Action, Object


def test_action_creation():
    act1 = Action('parcel.edit')
    assert act1[0] == 'parcel'
    assert act1[1] == 'edit'
    assert str(act1) == 'parcel.edit'


def test_object_creation():
    obj1 = Object('Cadasta/Batangas/parcel/123')
    assert obj1[0] == 'Cadasta'
    assert obj1[1] == 'Batangas'
    assert obj1[2] == 'parcel'
    assert obj1[3] == '123'
    assert str(obj1) == 'Cadasta/Batangas/parcel/123'


def test_object_creation_with_escapes():
    obj1 = Object('Cadasta/X\/Y/parcel/123')
    assert obj1[0] == 'Cadasta'
    assert obj1[1] == 'X/Y'
    assert obj1[2] == 'parcel'
    assert obj1[3] == '123'
    assert str(obj1) == 'Cadasta/X\/Y/parcel/123'


def test_action_wildcards():
    acts = [Action('parcel.edit'),
            Action('parcel.*'),
            Action('*.edit'),
            Action('parcel.view')]
    matches = [[True, True, True, False],
               [True, True, True, True],
               [True, True, True, False],
               [False, True, False, True]]
    for a1, ms in zip(acts, matches):
        for a2, m in zip(acts, ms):
            assert a1.match(a2) == m


def test_object_wildcards():
    objs = [Object('Cadasta/Batangas/parcel/123'),
            Object('Cadasta/X\/Y/parcel/123'),
            Object('Cadasta/*/parcel/*'),
            Object('Cadasta/*/party/*')]
    matches = [[True, False, True, False],
               [False, True, True, False],
               [True, True, True, False],
               [False, False, False, True]]
    for o1, ms in zip(objs, matches):
        for o2, m in zip(objs, ms):
            assert o1.match(o2) == m

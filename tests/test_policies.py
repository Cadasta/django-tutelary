from tutelary.engine import Clause, Policy, Action, Object
from tutelary.exceptions import (EffectException, PatternOverlapException)
import pytest
from .datadir import datadir  # noqa


def test_clause_creation():
    c1 = Clause('allow',
                [Action('parcel.edit')],
                [Object('Cadasta/*/parcel/*')])
    assert c1.effect == 'allow'
    with pytest.raises(PatternOverlapException):
        c2 = Clause('allow',
                    [Action('parcel.edit'), Action('parcel.*')],
                    [Object('Cadasta/*/parcel/*')])
        assert c2.effect == 'allow'
    with pytest.raises(PatternOverlapException):
        c3 = Clause('allow',
                    [Action('parcel.edit')],
                    [Object('Cadasta/*/parcel/*'), Object('*/*/parcel/*')])
        assert c3.effect == 'allow'
    with pytest.raises(EffectException):
        c4 = Clause('allows',
                    [Action('parcel.edit')],
                    [Object('Cadasta/*/parcel/*')])
        assert c4.effect == 'allow'


def test_policy_read(datadir):  # noqa
    """
    Test basic policy construction from a string.
    """
    p = Policy(json=datadir.join('test-policy-1.json').read())
    assert len(p) == 4


def test_policy_elements(datadir):  # noqa
    """
    Check policy element access.
    """
    p = Policy(json=datadir.join('test-policy-1.json').read())
    assert p.nclauses == 2
    assert len(p) == 4
    assert p[0].effect == 'allow'
    assert p[1].effect == 'deny'


def test_policy_serialisation(datadir):  # noqa
    """
    Test round-tripping of normalised serialisation and
    deserialisation.

    """
    p = Policy(json=datadir.join('test-policy-1.json').read())
    pstr = str(p)
    pchk = Policy(pstr)
    assert str(pchk) == pstr


def test_policy_hashing(datadir):  # noqa
    """
    Test hashing of normalised policy representations.
    """
    p1 = Policy(json=datadir.join('test-policy-1.json').read())
    p2 = Policy(json=datadir.join('test-policy-2.json').read())
    assert p1.hash() != p2.hash()


def test_policy_iteration(datadir):  # noqa
    """
    Test iteration over policies.
    """
    p = Policy(json=datadir.join('test-policy-1.json').read())
    i = 0
    for e, a, o in p:
        if i == 0 or i == 1:
            assert e == 'allow'
        else:
            assert e == 'deny'
        if i == 0:
            assert a == Action('*.view')
        else:
            assert a == Action('*.edit')
        i += 1

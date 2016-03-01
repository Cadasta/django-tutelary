from tutelary.engine import Clause, PolicyBody, Action, Object
from tutelary.exceptions import (
    EffectException, PatternOverlapException,
    PolicyBodyException, VariableSubstitutionException
)
import pytest
from .datadir import datadir  # noqa


def test_clause_creation():
    c1 = Clause('allow',
                [Action('parcel.edit')],
                [Object('Cadasta/*/parcel/*')])
    assert c1.effect == 'allow'


def test_clause_creation_pattern_overlaps():
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


def test_clause_creation_effect_exception():
    with pytest.raises(EffectException):
        c4 = Clause('allows',
                    [Action('parcel.edit')],
                    [Object('Cadasta/*/parcel/*')])
        assert c4.effect == 'allow'


def test_policy_read(datadir):  # noqa
    p = PolicyBody(json=datadir.join('test-policy-1.json').read())
    assert len(p) == 4


def test_policy_read_exceptions(datadir):  # noqa
    with pytest.raises(PolicyBodyException):
        PolicyBody(json='blah!')
    with pytest.raises(VariableSubstitutionException):
        PolicyBody(json='{ a: "$xyz" }')
    with pytest.raises(VariableSubstitutionException):
        PolicyBody(json='{ a: "$xyz" }', variables={'xya': 123})
    with pytest.raises(PolicyBodyException):
        PolicyBody(json='{ "version": "2015-12-10" }')
    with pytest.raises(PolicyBodyException):
        PolicyBody(json='{ "version": "2016-03-01", "clause": [] }')


def test_policy_elements(datadir):  # noqa
    p = PolicyBody(json=datadir.join('test-policy-1.json').read())
    assert p.nclauses == 2
    assert len(p) == 4
    assert p[0].effect == 'allow'
    assert p[1].effect == 'deny'


def test_policy_serialisation(datadir):  # noqa
    p = PolicyBody(json=datadir.join('test-policy-1.json').read())
    pstr = str(p)
    pchk = PolicyBody(pstr)
    assert str(pchk) == pstr


def test_policy_hashing(datadir):  # noqa
    p1 = PolicyBody(json=datadir.join('test-policy-1.json').read())
    p2 = PolicyBody(json=datadir.join('test-policy-2.json').read())
    assert p1.hash() != p2.hash()


def test_policy_iteration(datadir):  # noqa
    p = PolicyBody(json=datadir.join('test-policy-1.json').read())
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

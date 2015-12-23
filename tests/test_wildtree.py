import pytest
from tutelary.wildtree import WildTree


def test_wildtree_1():
    t = WildTree()
    t[('a', 'b', 'c')] = 1
    t[('a', 'b', 'd')] = 2
    t[('a', 'b', 'e')] = 3
    assert len(t) == 3
    assert t[('a', 'b', 'c')] == 1
    assert t[('a', 'b', 'd')] == 2
    assert t[('a', 'b', 'e')] == 3
    with pytest.raises(KeyError):
        assert t[('a', 'c', 'e')] == 1
    assert WildTree(json=repr(t)) == t


def test_wildtree_2():
    t = WildTree()
    t[('a', 'b', 'c')] = 1
    t[('a', 'b', 'd')] = 2
    t[('a', 'b', '*')] = 3
    assert len(t) == 1
    assert t[('a', 'b', 'c')] == 3
    assert t[('a', 'b', 'd')] == 3
    assert t[('a', 'b', 'e')] == 3
    assert WildTree(json=repr(t)) == t


def test_wildtree_3():
    t = WildTree()
    t[('a', 'b', 'c')] = 1
    t[('a', 'b', 'd')] = 2
    t[('a', '*', '*')] = 3
    assert len(t) == 1
    assert t[('a', 'b', 'c')] == 3
    assert t[('a', 'b', 'd')] == 3
    assert t[('a', 'b', 'e')] == 3
    assert WildTree(json=repr(t)) == t


def test_wildtree_4():
    t = WildTree()
    t[('a', 'b', 'c')] = 1
    t[('a', 'b', '*')] = 3
    t[('a', 'b', 'd')] = 2
    assert len(t) == 2
    assert t[('a', 'b', 'c')] == 3
    assert t[('a', 'b', 'd')] == 2
    assert t[('a', 'b', 'e')] == 3
    assert WildTree(json=repr(t)) == t


def test_wildtree_5():
    t = WildTree()
    t[('a', 'b', 'c')] = 1
    t[('a', '*', 'e')] = 3
    t[('a', 'b', 'd')] = 2
    assert len(t) == 3
    assert t[('a', 'b', 'c')] == 1
    assert t[('a', 'b', 'd')] == 2
    assert t[('a', 'b', 'e')] == 3
    assert t[('a', 'd', 'e')] == 3
    with pytest.raises(KeyError):
        assert t[('a', 'x', 'f')] == 1
    assert WildTree(json=repr(t)) == t

# coding:utf-8
from collections import MutableMapping
from json import loads, dumps


class WildTree(MutableMapping):
    """
    Data structure for mapping between segmented paths
    (e.g. ``a/b/c/d``) and values, allowing for wildcards
    (e.g. ``a/*/c/*``), where later key path insertions override
    earlier ones.

    Provides JSON serialisation (via repr) and deserialisation (via
    constructor).

    """
    def __init__(self, json=None):
        """
        By default, all new ``WildTree`` objects are empty.  They can also
        be deserialised from a JSON representation.  We store the
        optional value at the endpoint of the path to this node, plus
        a list of subtrees.  Each subtree is a pair whose first
        element is a key value (which may be a ``*`` wildcard) and
        whose second element is a ``WildTree``.

        """
        self._item = None
        self._subtrees = []
        if json is not None:
            self._dict_setup(loads(json))

    def __repr__(self):
        return ('{"item":' + dumps(self._item) +
                ',"subtrees":[' +
                ','.join(['[' + dumps(t[0]) + ',' + repr(t[1]) + ']'
                          for t in self._subtrees]) + ']}')

    def _dict_setup(self, d):
        self._item = d['item']
        for t in d['subtrees']:
            st = WildTree()
            st._dict_setup(t[1])
            self._subtrees.append((t[0], st))

    def __contains__(self, key):
        """
        Exact path membership: wildcards must be matched explicitly.
        """
        if len(key) == 0:
            return self._item is not None
        else:
            head, tail = key[0], key[1:]
            for st in self._subtrees:
                if st[0] == head:
                    return tail in st[1]
            else:
                return False

    def __len__(self):
        """
        Effective number of keys in the tree.  Note that inserting keys
        that override other keys leads to the overridden keys being
        purged from the tree, so the key count does not necessarily
        increase monotonically as keys are inserted.

        """
        n = sum(len(t[1]) for t in self._subtrees)
        return n + 1 if self._item is not None else n

    def __iter__(self):
        """
        Iterate over keys in the tree in "domination order".
        """
        if self._item is not None:
            yield ()
        for head in self._subtrees:
            for tail in head[1]:
                yield (head[0],) + tail

    def __getitem__(self, key):
        """
        Key lookup with wildcards.
        """
        return self.find(key)[0]

    def __setitem__(self, key, value):
        """
        Insert a new key path, potentially overriding and hence purging
        existing key paths.

        """
        self._purge_unreachable(key)
        if len(key) == 0:
            self._item = value
        else:
            head, tail = key[0], key[1:]
            self._setdefault(head)[tail] = value

    def __delitem__(self, key):
        """
        Key deletion: wildcards must be matched explicitly.
        """
        _, idxs = self.find(key, perfect=True)
        self._del_by_idx(idxs)

    def find(self, key, perfect=False):
        """
        Find a key path in the tree, matching wildcards.  Return value for
        key, along with index path through subtree lists to the result.  Throw
        ``KeyError`` if the key path doesn't exist in the tree.

        """
        if len(key) == 0:
            if self._item is not None:
                return self._item, ()
            else:
                raise KeyError(key)
        else:
            head, tail = key[0], key[1:]
            for i in range(len(self._subtrees)):
                if self._subtrees[i][0] == head or \
                   not perfect and self._subtrees[i][0] == '*':
                    try:
                        item, trace = self._subtrees[i][1].find(tail)
                        return item, (i,) + trace
                    except KeyError:
                        pass
            raise KeyError(key)

    def _del_by_idx(self, idxs):
        """
        Delete a key entry based on numerical indexes into subtree lists.

        """
        if len(idxs) == 0:
            self._item = None
            self._subtrees = []
        else:
            hidx, tidxs = idxs[0], idxs[1:]
            self._subtrees[hidx][1]._del_by_idx(tidxs)
            if len(self._subtrees[hidx][1]._subtrees) == 0:
                del self._subtrees[hidx]

    def _purge_unreachable(self, key):
        """
        Purge unreachable dominated key paths before inserting a new key
        path.

        """
        dels = []
        for p in self:
            if dominates(key, p):
                dels.append(p)
        for k in dels:
            _, idxs = self.find(k, perfect=True)
            self._del_by_idx(idxs)

    def _setdefault(self, key):
        """
        Find subtree, inserting a new one by default.
        """
        for st in self._subtrees:
            if st[0] == key:
                return st[1]
            elif st[0] == '*':
                break
        default = self.__class__()
        self._subtrees.insert(0, (key, default))
        return default


def dominates(p, q):
    """
    Test for path domination.  An individual path element *a*
    dominates another path element *b*, written as *a* >= *b* if
    either *a* == *b* or *a* is a wild card.  A path *p* = *p1*, *p2*,
    ..., *pn* dominates another path *q* = *q1*, *q2*, ..., *qm* if
    *n* == *m* and, for all *i*, *pi* >= *qi*.

    """
    return (len(p) == len(q) and
            all(map(lambda es: es[0] == es[1] or es[0] == '*', zip(p, q))))

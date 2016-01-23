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
        if json is None:
            self.root = {'item': None, 'subtrees': []}
        else:
            self.root = loads(json)

    def __repr__(self):
        return dumps(self.root)

    def __contains__(self, key):
        """
        Exact path membership: wildcards must be matched explicitly.
        """
        node = self.root
        while len(key) > 0:
            head, key = key[0], key[1:]
            found = False
            for st in node['subtrees']:
                if st[0] == head:
                    found = True
                    node = st[1]
                    break
            if not found:
                return False
        return node['item'] is not None

    def __len__(self):
        """
        Effective number of keys in the tree.  Note that inserting keys
        that override other keys leads to the overridden keys being
        purged from the tree, so the key count does not necessarily
        increase monotonically as keys are inserted.

        """
        def _len_help(tree):
            n = sum(_len_help(t[1]) for t in tree['subtrees'])
            return n + 1 if tree['item'] is not None else n
        return _len_help(self.root)

    def __iter__(self):
        """
        Iterate over keys in the tree in "domination order".
        """
        def _iter_help(tree):
            if tree['item'] is not None:
                yield ()
            for st in tree['subtrees']:
                for tail in _iter_help(st[1]):
                    yield (st[0],) + tail
        yield from _iter_help(self.root)

    def __getitem__(self, key):
        """
        Key lookup with wildcards.
        """
        return find_in_tree(self.root, key)[0]

    def __setitem__(self, key, value):
        """
        Insert a new key path, potentially overriding and hence purging
        existing key paths.

        """
        self._purge_unreachable(key)
        node = self.root
        while len(key) > 0:
            found = False
            for st in node['subtrees']:
                if st[0] == key[0]:
                    found = True
                    node = st[1]
                    break
                elif st[0] == '*':
                    break
            if not found:
                default = {'item': None, 'subtrees': []}
                node['subtrees'].insert(0, (key[0], default))
                node = default
            key = key[1:]
        node['item'] = value

    def __delitem__(self, key):
        """
        Key deletion: wildcards must be matched explicitly.
        """
        _, idxs = find_in_tree(self.root, key, perfect=True)
        del_by_idx(self.root, idxs)

    def find(self, key, perfect=False):
        """
        Find a key path in the tree, matching wildcards.  Return value for
        key, along with index path through subtree lists to the result.  Throw
        ``KeyError`` if the key path doesn't exist in the tree.

        """
        return find_in_tree(self.root, key, perfect)

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
            _, idxs = find_in_tree(self.root, k, perfect=True)
            del_by_idx(self.root, idxs)


def del_by_idx(tree, idxs):
    """
    Delete a key entry based on numerical indexes into subtree lists.
    """
    if len(idxs) == 0:
        tree['item'] = None
        tree['subtrees'] = []
    else:
        hidx, tidxs = idxs[0], idxs[1:]
        del_by_idx(tree['subtrees'][hidx][1], tidxs)
        if len(tree['subtrees'][hidx][1]['subtrees']) == 0:
            del tree['subtrees'][hidx]


def find_in_tree(tree, key, perfect=False):
    """
    Helper to perform find in dictionary tree.
    """
    if len(key) == 0:
        if tree['item'] is not None:
            return tree['item'], ()
        else:
            for i in range(len(tree['subtrees'])):
                if not perfect and tree['subtrees'][i][0] == '*':
                    item, trace = find_in_tree(tree['subtrees'][i][1],
                                               (), perfect)
                    return item, (i,) + trace
            raise KeyError(key)
    else:
        head, tail = key[0], key[1:]
        for i in range(len(tree['subtrees'])):
            if tree['subtrees'][i][0] == head or \
               not perfect and tree['subtrees'][i][0] == '*':
                try:
                    item, trace = find_in_tree(tree['subtrees'][i][1],
                                               tail, perfect)
                    return item, (i,) + trace
                except KeyError:
                    pass
        raise KeyError(key)


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

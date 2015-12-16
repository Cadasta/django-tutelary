# coding:utf-8

import re
from json import loads, dumps
from string import Template
import hashlib
from collections import Sequence

from .wildtree import WildTree
from .exceptions import IllegalEffectException, IllegalPatternOverlapException


# ------------------------------------------------------------------------------
#
#  Basic action and object representations
#

class SimpleSeparated(Sequence):
    """
    Simple sequences of strings delimited by a separator, with
    wildcarding.

    A wildcard component is represented by a ``*`` string and matches
    any single string component.  Equality comparison between
    sequences is exact comparison of components; matching between
    wildcarded components can be tested using the ``match`` method.

    """
    def __init__(self, s):
        self.components = s.split(self.separator)

    def __len__(self):
        return len(self.components)

    def __getitem__(self, idx):
        return self.components[idx]

    def __str__(self):
        return self.separator.join(self.components)

    def __eq__(self, other):
        return self.components == other.components

    def match(self, other):
        # Two sequences match if they are the same length and
        # corresponding components are either equal, or at least one
        # is a wildcard.
        if len(self) != len(other):
            return False
        for cself, cother in zip(self.components, other.components):
            if not (cself == cother or cself == '*' or cother == '*'):
                return False
        return True


class EscapeSeparated(SimpleSeparated):
    """
    Sequences of strings delimited by a separator that can be
    backslash-escaped.  Backslashes can also be backslash-escaped; no
    other escaping mechanism is supported.

    """
    def __init__(self, s):
        # Generate regexp lazily for each derived class so that we can
        # compile it.
        if not hasattr(self, 'regex'):
            type(self).regex = make_regex(self.separator)
        self.components = self.regex.split(s)[1::2]
        self.components = [unescape(s, self.separator)
                           for s in self.components]

    def __str__(self):
        return self.separator.join([escape(s, self.separator)
                                    for s in self.components])


class Action(SimpleSeparated):
    """
    Actions are represented by period-separated sequences of elements
    (e.g. ``parcel.edit``, ``admin.assign-role``) with wildcard
    elements indicated by ``*`` (e.g. ``party.*``).  A list of
    *registered* actions is maintained to support permissions set
    queries to find the set of actions that are permitted on a
    specified object pattern.

    """
    separator = '.'

    registered = set()

    def register(action):
        """
        Action registration is used to support generating lists of
        permitted actions from a permission set and an object pattern.
        Only registered actions will be returned by such queries.

        """
        if isinstance(action, str):
            Action.register(Action(action))
        elif isinstance(action, Action):
            Action.registered.add(action)
        else:
            map(Action.register, action)


class Object(EscapeSeparated):
    """
    Objects are represented by slash-separated sequences of elements
    (e.g. ``Cadasta/Batangas/parcel/123``, ``H4H/PaP/party/118``) with
    wildcard elements indicated by ``*``
    (e.g. ``Cadasta/*/parcel/*``).  Slashes can be backslash-escaped,
    as can backslashes (e.g. ``Cadasta/Village-X\/Y/parcel/943``).

    """
    separator = '/'


# ------------------------------------------------------------------------------
#
#  Clauses and policies
#

class Clause:
    """
    A clause is a simple container for an effect ("allow" or "deny")
    and a list of non-overlapping action patterns and non-overlapping
    object patterns to which the effect applies.

    """
    def __init__(self, effect=None, action=None, object=None, dict=None):
        """
        A clause can be created either by giving explicit lists of
        ``Action`` and ``Object`` objects or by giving a dictionary
        with ``effect``, ``action`` and ``object`` keys pulled out of
        the JSON representation of a policy.

        """
        if dict is not None:
            effect = dict['effect']
            action = list(map(Action, dict['action']))
            object = list(map(Object, dict['object']))
        if effect not in ['allow', 'deny']:
            raise IllegalEffectException(effect)
        if any(a1.match(a2) for a1 in action for a2 in action if a1 != a2):
            raise IllegalPatternOverlapException('action')
        if any(o1.match(o2) for o1 in object for o2 in object if o1 != o2):
            raise IllegalPatternOverlapException('object')
        self.effect = effect
        self.action = action
        self.object = object


class Policy(Sequence):
    """
    A policy is just a sequence of clauses, possibly with a name.
    Conversion to and from JSON representations (with
    canonicalisation), and hash generation from the canonical
    representation.

    Can be composed into permission sets, so for convenience allow for
    iteration over individual (action, object) pairs (note that each
    clause can have multiple actions and objects).

    """
    def __init__(self, json, vars=None):
        try:
            if vars is not None:
                d = loads(Template(json).substitute(vars))
            else:
                d = loads(json)
            self.version = d['version'] or '2015-12-10'
            self.clauses = d['clause'] or []
            self.clauses = list(map(lambda c: Clause(dict=c), self.clauses))
            self.nitems = sum(map(lambda c: len(c.action) * len(c.object),
                                  self.clauses))
            self.nclauses = len(self.clauses)
            self.valid = self.version in ['2015-12-10']
        except:
            self.valid = False

    def __len__(self):
        return self.nitems

    def __getitem__(self, idx):
        return self.clauses[idx]

    def __str__(self):
        def one_clause(c):
            return {'effect': c.effect,
                    'action': list(map(str, c.action)),
                    'object': list(map(str, c.object))}
        cs = list(map(one_clause, self.clauses))
        return dumps({'version': self.version, 'clause': cs})

    def __iter__(self):
        for c in self.clauses:
            e = c.effect
            for a in c.action:
                for o in c.object:
                    yield e, a, o

    def hash(self):
        return hashlib.md5(str(self).encode()).hexdigest()


# ------------------------------------------------------------------------------
#
#  Permission sets
#

class PermissionSet:
    """
    A permission set records, in a compact way, the permissions
    associated with a sequence of policy clauses.  The construction of
    permission sets handles the overriding of earlier clauses by later
    clauses and the treatment of wildcards in the action and object
    patterns for individual policy clauses.

    Can:
     - Create empty permissions sets.
     - Compose statements and policies into permission set.
     - Test an (action, object) pair against a permission set.
     - Determine the list of allowed actions for an object pattern from
       a permission set.

    Most of the functionality needed here is implemented in the
    ``WildTree`` class.

    """

    def __init__(self, policies=None):
        """
        Permission sets are all created empty, with an optional list of
        policies added.

        """
        self.tree = WildTree()
        if policies is not None:
            self.add(policies=policies)

    def add(self, effect=None, action=None, object=None,
            policy=None, policies=None):
        """
        Insert an individual (effect, action, object) triple or all
        triples for a policy or list of policies.

        """
        if policies is not None:
            for p in policies:
                self.add(policy=p)
        elif policy is not None:
            for e, a, o in policy:
                self.add(e, a, o)
        else:
            self.tree[action.components + object.components] = effect

    def allow(self, action, object):
        """
        Determine where a given action on a given object is allowed.
        """
        try:
            return self.tree[action.components + object.components] == 'allow'
        except KeyError:
            return False

    def permitted_actions(self, object):
        """
        Determine permitted actions for a given object pattern.
        """
        pass


# ------------------------------------------------------------------------------
#
#  Utility functions
#

def make_regex(separator):

    """
    Utility function to create regexp for matching escaped separators
    in strings.

    """
    return re.compile(r'(?:' + re.escape(separator) + r')?((?:[^' +
                      re.escape(separator) + r'\\]|\\.)*)')


def unescape(s, sep):
    """
    Unescape escaped separators and backslashes in strings.
    """
    return s.replace("\\" + sep, sep).replace("\\\\", "\\")


def escape(s, sep):
    """
    Escape unescapes separators and backslashes in strings.
    """
    return s.replace("\\", "\\\\").replace(sep, "\\" + sep)

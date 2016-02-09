.. _guide_policy_definitions:

Policy definitions
==================

Policies in django-tutelary are defined by JSON objects.  These are
used to construct Django ``Policy`` objects (defined in
``tutelary.models``).  A *policy* is a JSON object with optional
``version`` and mandatory ``clause`` fields.  (The ``version`` field
is intended for future development; currently its only valid value is
``"2015-12-10"``.)

Although policy documents are nominally JSON, for convenience they
also allow comments: any text outside of a string from ``//`` or ``#``
to the end of line is ignored.

Clauses
-------

The ``clause`` field gives the content of the policy, and is a JSON
array of *clauses*.

Each individual *clause* is a JSON object with three fields:

``effect``
  Whether the clause *allows* or *denies* the listed actions: valid
  values are ``"allow"`` and ``"deny"``.

``action``
  A JSON array of action patterns (as strings) representing the set of
  actions to which the clause applies.  For example, ``["*.edit",
  "*.delete"]`` refers to all edit and delete actions for any object
  types, and ``["parcel.create", "parcel.delete"]`` refers to the
  create and delete actions for ``parcel`` objects.

``object``
  An optional JSON array of object patterns (as strings) representing
  the set of objects to which the clause applies.  For example, if
  ``parcel`` objects are labelled as
  ``parcel/<org-name>/<project-name>/<id>``, then
  ``["parcel/Cadasta/*/*"]`` refers to all the ``parcel`` objects in
  all projects belonging to the ``Cadasta`` organisation.  The object
  patterns in a clause may contain variables, indicated by a leading
  ``$`` character -- these may be substituted at the point where the
  policy is used, allowing for a limited form of policy templating.
  If the ``object`` field is absent, the clause refers to
  "free-floating" actions, i.e. actions that are closer to Django's
  default idea of "permissions".

Interpretation of policies
--------------------------

Policies are interpreted clause by clause, top to bottom.  (The
initial "default" policy *denies* all actions on all objects.)  Later
clauses override earlier clauses.  This allows you to write general
conditions first, then to override specific instances as needed.  For
example, if ``page`` objects are labelled as
``page/<owner>/<category>/<id>``, the result of the following
clauses::

  [{"effect": "allow",
    "action": ["page.edit"],
    "object": ["page/*/*/*"]},
   {"effect": "deny",
    "action": ["page.edit"],
    "object": ["page/*/Private/*"]}]

is to *allow* editing of all pages for all owners, *except* for those
in the ``Private`` category, to which it *denies* editing permission.

Or alternatively::

  [{"effect": "deny",
    "action": ["page.edit"],
    "object": ["page/*/*/*"]},
   {"effect": "allow",
    "action": ["page.edit"],
    "object": ["page/*/Personal/*"]}]

*denies* editing of all pages for all owners, *except* for those in
the ``Personal`` category, for which it *allows* editing permission.

This clause-wise composition extends beyond individual policies, as
described in the next section.

.. note:: This step-by-step interpretation of clauses in policies is
          an operational definition only.  The mechanism used by
          django-tutelary to interpret composition of policy clauses
          builds a single composite data structure from all the
          involved clauses when the policies are assigned to a user.
          This composite data structure is optimised to efficiently
          answer permissions queries without needing to scan through
          all the involved policy clauses.

Examples
--------

Here's a policy definition using a template variable for the
``organisation`` field in some object patterns.  This variable will be
instantiated when the policy is assigned to a user.  The policy also
contains a clause allowing the "free-floating" ``statistics`` action::

  {
    "version": "2015-12-10",
    "clause": [
      // Allow all editing actions for a single organisation.
      { "effect": "allow", "action": ["*.edit"],
        "object": ["*/$organisation/*/*/*"] },
      // But deny all create actions.
      { "effect": "deny", "action": ["*.create"],
        "object": ["*/$organisation/*"] },
      // Allow the "free-standing" statistics action.
      { "effect": "allow", "action": ["statistics"] }
    ]
  }

And here's a slightly larger example.  This is the default policy from
the example application, which allows viewing of list and detail views
for all object types, but nothing else::

  {
    "version": "2015-12-10",
    "clause": [
      {"effect": "allow", "action": ["party.list"],
       "object": ["party/*/*"]},
      {"effect": "allow", "action": ["party.detail"],
       "object": ["party/*/*/*"]},
      {"effect": "allow", "action": ["parcel.list"],
       "object": ["parcel/*/*"]},
      {"effect": "allow", "action": ["parcel.detail"],
       "object": ["parcel/*/*/*"]},
      {"effect": "allow", "action": ["organisation.list"],
       "object": ["organisation"]},
      {"effect": "allow", "action": ["organisation.detail"],
       "object": ["organisation/*"]},
      {"effect": "allow", "action": ["project.list"],
       "object": ["project/*"]},
      {"effect": "allow", "action": ["project.detail"],
       "object": ["project/*/*"]},
      {"effect": "allow", "action": ["user.list"],
       "object": ["user"]},
      {"effect": "allow", "action": ["user.detail"],
       "object": ["user/*"]},
      {"effect": "allow", "action": ["policy.list"],
       "object": ["policy"]},
      {"effect": "allow", "action": ["policy.detail"],
       "object": ["policy/*"]},
      {"effect": "deny", "action": "statistics"}
    ]
  }

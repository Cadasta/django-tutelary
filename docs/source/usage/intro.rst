.. _usage_intro:

Introduction
============

Permissions management in django-tutelary is based on a few simple
concepts:

Actions
  An *action* is an operation that can be performed on a resource within
  a Django application.  Actions are named using a period-separated
  sequence of names, e.g. ``parcel.create``, ``page.edit``,
  ``board.solder``.

Objects
  An *object* is a resource within a Django application on which
  actions be performed.  Objects are named using a forward
  slash-separated sequence of names,
  e.g. ``parcel/Cadasta/TestProject/123``, ``page/BlogIndex``,
  ``board/IanRoss/LED_Clock/2``.  (If you need to use a component in
  an object name that contains a slash, escape it with a backslash:
  ``page/A\/B Testing``, for example.)

Action and object patterns
  Components of action or object names may be replaced with a wildcard
  (represented by ``*``) to make an action or object *pattern*
  representing a class of resources.  For example, ``parcel.*``
  denotes all possible actions on parcels, ``*.solder`` denotes all
  soldering operations, ``page/*`` represents all page objects,
  ``board/IanRoss/*/*`` represents all boards from all projects
  belonging to customer ``IanRoss``, and so on.

Policies
  A *policy* is a list of clauses describing what actions may be
  performed on what objects.  A single clause in a policy may *allow*
  or *deny* a set of actions on a set of objects.  Concretely,
  policies are stored using JSON syntax.

Permission set
  A *permission set* represents the overall effect of a policy or set
  of policies, which results from composing the clauses of all the
  policies in order, with later clauses overriding earlier ones.  To
  determine whether a set of policies allows an action for an object,
  effectively the latest clause in the sequence of policies matching
  the action/object combination is found and says whether the action
  is *allowed* or *denied*.  In fact, the combination of clauses is
  represented by a distinct permission set data structure that
  supports fast queries for action/object combinations.

The fundamental way of assigning permissions to a user in
django-tutelary is to assign a sequence of policies to the user.  The
clauses in these policies are combined in order to form an overall
permission set for the user, and it is this permission set that is
used to answer permission queries for the user.

Much of the public interface to django-tutelary is concerned with
associating django-tutelary's *actions* and *objects* with Django
models and views.  The machinery of policy composition and permission
sets is hidden from view.

.. _guide_policy_composition:

Policy composition and assignment
=================================

As described in the previous section, policies are effectively
interpreted clause-by-clause, with later clauses overriding earlier
ones.  The same interpretation semantics also holds across multiple
policies: the way that django-tutelary is intended to be used is that
you associate a sequence of policies with each user, with the sequence
usually going from less specific to more specific.

In this section, we'll work through an example, then talk about the
``Policy`` and ``Role`` classes and ``User.assign_policies`` and
``assign_user_policies`` methods defined by django-tutelary to connect
users to the policies that control their permissions.  We'll also look
at some custom query methods for finding roles and retrieving the list
of roles and policies assigned to a user.

A worked example
----------------

Suppose that we have an organisation with "departments", and each
department has "sections".  Departments are labelled as
``dept/<dept-name>`` and sections as ``sect/<dept-name>/<sect-name>``.
The possible actions we'll consider are ``dept.view``,
``dept.create``, ``dept.delete``, ``sect.view``, ``sect.create`` and
``sect.delete``, respectively to view, create or delete departments
and sections within departments.

First, let's think about a default policy that we can apply to all
users.  Let's assume that all users should be able to view all
departments and all sections in all departments.  The policy clauses
in ``default-policy.json`` with then be something like::

  [{"effect": "allow", "action": ["dept.view"],
    "object": ["dept/*"]},
   {"effect": "allow", "action": ["sect.view"],
    "object": ["sect/*/*"]}]

Now consider what additional permissions we might want to allow for
overall administrators of the organisation.  Such users need to be
able to create and delete departments and create and delete sections
within any department, so the policy clauses in
``org-admin-policy.json`` would be::

  [{"effect": "allow", "action": ["dept.create", "dept.delete"],
    "object": ["dept/*"]},
   {"effect": "allow", "action": ["sect.create", "sect.delete"],
    "object": ["sect/*/*"]}]

We may also have departmental administrators, who are able to create
and delete sections within their own department, but not in any other
departments.  In order to represent this, we use the following policy
clauses in ``dept-admin-policy.json``::

  [{"effect": "allow", "action": ["sect.create", "sect.delete"],
    "object": ["sect/$department/*"]}]

Note how we use a policy template variable (``$department``) to stand
in for a *particular* department, rather than a wildcard to refer to
all departments.  A value for the ``$department`` variable must be
supplied when making use of this policy, as we'll see below.

In order to make use of these policies, we first read the policy files
and create and save django-tutelary ``Policy`` objects from them::

  from django.contrib.aith.models import User
  from tutelary.models import Policy

  ...

  default_policy = Policy(
    name='default',
    body=open('default-policy.json').read()
  )
  default_policy.save()
  org_admin_policy = Policy(
    name='org-admin',
    body=open('org-admin-policy.json').read()
  )
  org_admin_policy.save()
  dept_admin_policy = Policy(
    name='dept-admin',
    body=open('dept-admin-policy.json').read()
  )
  dept_admin_policy.save()

We then apply these policies to users::

  user1 = User.objects.get(username='alex')
  user1.assign_policies(
    default_policy,
    org_admin_policy
  )

  user2 = User.objects.get(username='bertie')
  user2.assign_policies(
    default_policy,
    (dept_admin_policy, {'department': 'finance'})
  )

  user3 = User.objects.get(username='charlie')
  user3.assign_policies(default_policy)

When we assign multiple policies to a user, the clauses from each of
the policies are interpreted one by one to construct an overall set of
permissions for the user.  Note how we supply a value for the
``$department`` variable in the department administrator policy when
we assign policies to ``user2`` by providing a dictionary mapping
between policy variable names and values.  The end result of this is
that users ``alex``, ``bertie`` and ``charlie`` end up with the
following sets of permissions:

+-------------+-----------------+----------------------+
| User        | Actions         | Objects              |
+=============+=================+======================+
| ``alex``    | | ``dept.*``    | | ``dept/*``         |
|             | | ``sect.*``    | | ``sect/*/*``       |
+-------------+-----------------+----------------------+
| ``bertie``  | | ``dept.view`` | | ``dept/*``         |
|             | | ``sect.view`` | | ``sect/*/*``       |
|             | | ``sect.*``    | | ``sect/finance/*`` |
+-------------+-----------------+----------------------+
| ``charlie`` | | ``dept.view`` | | ``dept/*``         |
|             | | ``sect.view`` | | ``sect/*/*``       |
+-------------+-----------------+----------------------+

The ``Policy`` model
--------------------

Policies in django-tutelary are represented as JSON objects, but in
order to use them within Django, we need to store them as Django model
instances.  The ``Policy`` model from ``tutelary.models`` is used for
this.  This is a simple model with a ``name`` and a ``body``, which is
used to hold the string representation of the JSON data defining the
policy.  A policy object can thus be created and saved to the database
using code like this::

  default_policy = Policy(
    name='default',
    body=open('default-policy.json').read()
  )
  default_policy.save()

Changes to ``Policy`` objects are audited using the
django-audit-log_ package.

.. _django-audit-log: https://pypi.python.org/pypi/django-audit-log/0.7.0

The ``Role`` model
------------------

As well as treating policies individually, it's possible to bundle a
sequence of policies sharing variable assigments into a *role*.  These
are represented by instances of the Django ``Role`` model in
``tutelary.models``.  If we have policies assigned to variables
``default_pol``, ``org_pol`` and ``project_pol``, we can create and
save a role like this::

  project_role = Role.objects.create(
      name='project_role',
      policies=[default_pol, org_pol, project_pol],
      variables={'organisation': 'Cadasta', 'project': 'TestProj'}
  )

If this role is subsequently assigned to a user, it's precisely
equivalent to assigning the individual policies, all with the same
variable assignments.

As for policy objects, changes to ``Role`` objects are audited using
the django-audit-log_ package.

A common use case for roles is to have a named role
(e.g. ``system-admin``, ``project-manager``, ``process-qa``) using
policies with variables that are filled in for particular assignments
to users.  (For instance, the policies for a ``project-manager`` roles
will probably have a ``$project`` variable that needs to be filled in
to instantiate the role for a particular project -- i.e. to make a
user a project manager for that particular project).  This case is
easy to deal with using the standard ``filter`` query method to find
``Role`` objects by name and variable assignment.  Since role names
are not constrained to be unique, you can give all the role instances
you assign to project managers the same name and can do this to find
the project manager roles for a particular project::

  project_manager_roles = Role.filter(
    name='project-manager',
    variables={'project': 'ExcitingNewProject'}
  )

Assigning policies to users
---------------------------

To associate a sequence of policies with a user, thus assigning a set
of permissions to the user, we use the ``User.assign_policies`` method
(django-tutelary adds this method to whatever user model is set up in
Django's ``settings.AUTH_USER_MODEL`` configuration variable) or the
``assign_user_policies`` function from ``tutelary.models``.  The
latter is usually only needed for assigning policies for
unauthenticated users (see below).

The ``assign_user_policies`` function takes as arguments a user and a
sequence of policies and just calls ``User.assign_policies`` on the
supplied user, except in the case where the supplied user is ``None``.
In that case, the supplied sequence of policies is taken to define
permissions for unauthenticated (i.e. anonymous) users.  By default,
unauthenticated users (like all other users) have no django-tutelary
permissions, but it's often useful to be able to assign a narrow set
of permissions to unauthenticated users (to view all public data on
the site, for example).

The sequence of policies passed to ``User.assign_policies`` (and
``assign_user_policies``) contains either individual ``Policy`` or
``Role`` objects or 2-tuples of a ``Policy`` object and a dictionary
of policy variable assignments.  A typical use looks like this::

  default_policy = Policy.objects.get(name='default')
  editor_policy = Policy.objects.get(name='editor')
  user = User.objects.get(username='iross')
  user.assign_policies(
    default_policy,
    (editor_policy, {'organisation': 'Cadasta',
                     'project': 'Kibera'})
  )

This assumes that the JSON body of the ``Policy`` object named
"``editor``" uses the policy variables ``$organisation`` and
``$project``.  It's important to note that values for *all* policy
variables used within the body of a policy must be provided at the
point of use of the policy -- here, "point of use" means when the
policy is assigned to a user using ``User.assign_policies``.

The list of policies and/or roles assigned to a user can be retrieved
using the ``user_assigned_policies`` function and the
``User.assigned_policies`` method -- passing ``None`` to the former
retrieves the policies assigned to the anonymous user.  The return
value of both of these is a sequence in the same format as the
arguments passed to ``User.assign_policies``, i.e. a sequence of
policy or role values or ``(policy/role, variables)`` pairs.

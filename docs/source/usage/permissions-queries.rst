.. _usage_permissions_queries:

Permissions queries
===================

Most of the time, queries to django-tutelary to find out whether
actions are permitted will happen automatically through the
``PermissionRequiredMixin`` and django-tutelary's custom
authentication backend.  However, there are cases where it can be
useful to make these queries explicitly, and django-tutelary supports
a couple of other query types that are documented here.

Simple permissions queries
--------------------------

The simplest query type involves calling ``User.has_perm`` to
determine whether a particular action is permitted on a particular
object.  For example::

  user = User.objects.get(username='iross')
  page = Page.objects.get(id=1345)
  result = user.has_perm('page.edit', page)

This tests whether user ``iross`` has permissions to perform the
``page.edit`` action on the ``Page`` object with ``id`` 1345.  This of
course requires that the ``Page`` model be enabled for django-tutelary
permissioning (see :ref:`usage_permissioning_models`).

Accessing permission objects
----------------------------

Each instance of a Django model marked up using the
``permissioned_model`` decorator has an associated django-tutelary
object path.  This object path can be retrieved using the
``get_permissions_object`` method added to the model by the
``permissioned_model`` decorator.  The value returned from
``get_permissions_object`` is of type ``tutelary.engine.Object``, a
low-level type used for representing object paths.  Values of this
type can be converted to strings, so, assuming that the ``Page`` model
is set up for django-tutelary versioning (with ``perm_type='page'``
and ``path_fields=['chapter','pageno']``) the following works::

  > page = Page.objects.get(chapter=3, pageno=1345)
  > print('Object path:', str(page.get_permissions_object()))
  Object path: page/3/1345

Permitted actions queries
-------------------------

As well as querying for permissions for individual actions on
individual objects, it can be useful to know what actions are
permitted, either for a single object or a class of objects.  The
django-tutelary authentication backend provides a
``permitted_actions`` method to perform this kind of query.  You can
get hold of the backend using Django's ``get_backends`` function (from
``django.contrib.auth``).  Assuming you only have a single
authentication backend set up, something like this will work::

  > from django.contrib.auth import get_backends
  > from django.contrib.auth.models import User
  > from .models import Page
  > backend = get_backends()[0]
  > user = User.objects.get(username='iross')
  > page = Page.objects.get(pageno=1345)
  > page_obj = page.get_permissions_object()
  > acts = backend.permitted_actions(user, page_obj)
  > print([str(a) for a in acts])
  ['page.edit', 'page.view', 'page.delete']

The ``permitted_actions`` method takes as arguments a user object and
an object or object pattern (as a ``tutelary.engine.Object`` value,
which is why we call ``get_permissions_object`` on the ``Page`` object
here).  It returns a list of permitted actions as
``tutelary.engine.Action`` values.  These are convertible to strings,
which is how we display them here.

The ultimate intention of this kind of query is to implement a sort of
permission-drive HATEOAS within applications: the front-end of a web
application should be able to find out what actions a user is allowed
to perform and modify the user interface that it displays
accordingly.  (Getting a list of the permitted actions for an object
is only a part of that, of course, but it's an important part!)

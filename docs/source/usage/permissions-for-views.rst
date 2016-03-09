.. _usage_permissions_for_views:

Permissions for views
=====================

It's recommended that you use class-based views with django-tutelary.
The permission handling API for class-based views is much more
flexible than for function views.

Class-based views
-----------------

Using django-tutelary for controlling access to Django views is
straightforward.  There is a single ``PermissionRequiredMixin`` mixin
class defined in ``tutelary.mixins``, and in most cases this can
simply by mixed into your view classes without any drama.  The
``PermissionRequiredMixin`` mixin is written to work both with
"normal" Django and with `DRF
<http://www.django-rest-framework.org/>`_.

.. warning:: MAKE THIS TRUE!

For example, suppose that you've defined a ``user.detail`` action for
the ``User`` model (using the ``permissioned_model`` function).  You
can then control access to a detail view for the ``User`` model using
this action as follows::

  import django.views.generic as generic
  from tutelary.mixins import PermissionRequiredMixin
  from django.contrib.auth.models import User

  ...

  class UserDetail(PermissionRequiredMixin, generic.DetailView):
    model = User
    permission_required = 'user.detail'

The only additional element needed to activate django-tutelary
permissions is the ``permission_required`` attribute that should be
added to the view.  There are a number of possibilities for setting
this attribute, but the simplest option is either a single action name
or a sequence of action names.  All of the actions listed in
``permission_required`` must be *allowed* for the user on the model
object for the view to succeed.

The ``permission_required`` attribute
-------------------------------------

As noted above, the simplest value that can be given for the
``permission_required`` attribute in the ``PermissionRequiredMixin``
mixin is a single action name.  A range of other possibilities allow
for more flexible handling of permissions lookup, dependent on
characteristics of the request being processed.

The options for ``permission_required`` are:

Single action
  This is the simplest case -- a single action name is provided as a
  string.  The permissions backend checks that the user making the
  request is allowed to perform the specified action on the object (or
  objects) associated with the view.

Sequence of actions
  If a sequence of action names is provided for
  ``permission_required``, then all of these actions must be permitted
  for the user for the request to be allowed.

Callable
  If the ``permission_required`` value is callable, it is called with
  the view and request as arguments.  If the callable returns ``True``
  or ``False``, the request is permitted or denied immediately.  If
  the callable returns a single string or sequence of strings, these
  are interpreted as action names, and the permissions for the view
  are checked as if these action names had been provided directly as
  the value of ``permission_required``.  Note that if the callable is
  defined as a method, its signature should be ``method_name(self,
  view, request)``, even if it's already defined as a member of a view
  class.

Method dictionary
  The final option for ``permission_required`` is to provide a
  dictionary whose keys are HTTP method names (GET, POST, PUT, etc.).
  The values in the dictionary can be any of the preceding three
  ``permission_required`` options, or ``None``, which indicates that
  requests for the given HTTP method are always permitted.

Some examples should make this clearer.  Suppose that we have a
``ListCreateView`` which provides list of ``Board`` entities via GET
requests, with an attached form to create a new ``Board`` entity, and
processes form uploads on POST requests.  If we want it to always be
possible to access the list and attached form, but to apply the
``board.create`` permission to form submissions, we can do this::

  import views.generic.edit as edit
  from tutelary.mixins import PermissionRequiredMixin
  from manufacturing.models import Board

  ...

  class BoardList(PermissionRequiredMixin, edit.ListCreateView):
    model = Board
    permission_required = {
        'GET': None,
        'POST': 'board.create'
    }

The ``permission_required`` method dictionary says that GET requests
are always permitted (because of the ``None`` value) and POST requests
must have permissions to perform the ``board.create`` action.

Using a callable for ``permission_required`` allows us to make the
permissions required to fulfil a request depend on the state of a
model entity or body data in the request.  Here's an example where the
actions that need to be checked in a DRF ``RetrieveUpdateAPIView``
depend on the state of a model entity (is the entity "archived"?) and
the request body (is the request trying to "archive" or "unarchive"
the entity?)::

  class OrganizationDetail(PermissionRequiredMixin,
                           generics.RetrieveUpdateAPIView):
      def patch_actions(self, request):
          is_archived = self.get_object().archived
          new_archived = request.data.get('archived', is_archived)
          if not is_archived and (is_archived != new_archived):
              return ('org.update', 'org.archive')
          elif is_archived and (is_archived != new_archived):
              return ('org.update', 'org.unarchive')
          else:
              return 'org.update'

      permission_required = {
          'GET': 'org.view',
          'PATCH': patch_actions
      }

Function views
--------------

For function views, there is a ``permission_required`` decorator that
works in a similar way to the ``permission_required`` decorator in
Django's default permissions system -- see the reference documentation
for details.

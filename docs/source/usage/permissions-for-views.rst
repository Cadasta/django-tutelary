.. _usage_permissions_for_views:

Permissions for views
=====================

.. note:: So far, django-tutelary only supports class-based views.

Using django-tutelary for controlling access to Django views is
straightforward.  There is a single ``PermissionRequiredMixin`` mixin
class defined in ``tutelary.mixins``, and in most cases this can
simply by mixed into your view classes without any drama.

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
added to the view.  This is either a single action name or a sequence
of action names.  All of the actions listed in ``permission_required``
must be *allowed* for the user on the model object for the view to
succeed.

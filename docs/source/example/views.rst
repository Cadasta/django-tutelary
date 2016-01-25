.. _example_views:

Views
=====

.. note:: The code described here is in
   `example/exampleapp/views.py`_.

Most of the views in the example application are pretty
straightforward, so we'll concentrate on the oddities and differences
here.  All of the views use Django's class-based views: local classes
are defined deriving from things like
``django.views.generic.ListView`` including some mixins to add extra
functionality:

``UserMixin``
  Because we're interested in demonstrating permissions for different
  users, we want to make it easy to switch back and forth between
  different user accounts to look at what actions are possible for
  different users in different views.  To do this, we use a custom
  authentication backend (defined in `example/exampleapp/views.py`_)
  that bypasses authentication checking, we add ``UserMixin`` to all
  of our view classes to include a list of all available users in the
  view context data, and we include a menu to select the current user
  at the bottom of every view (it's set up in the `base template`_ for
  the application).

``PermissionInfoMixin``
  This mixin just adds a list of available actions to the view context
  data, based on the current user and the object or objects rendered
  in the view.  (Where there's more than one object in the view,
  actions are parenthesised if they're only available for a subset of
  the displayed objects.)  This action list is rendered in the base
  template, just like the user selection menu.

``PermissionRequiredMixin``
  This is the main django-tutelary mixin for handling permissions for
  views, except that we catch permission errors and display them as
  Django messages (well, just a big red "PERMISSION DENIED" message,
  but it's a proof of concept...).  There is one small wrinkle here,
  required because of the user switching menu we have.  It's possible
  to be looking at a view that's permitted for the current user, then
  to switch to a user for whom that view *isn't* permitted.  When that
  happens, we get into a redirect loop because we can't redisplay the
  referring view -- instead, we just drop out to the index page.

The only views that have any level of complexity are the user forms.
That's because they allow you to control the assignment of policies to
a user, and that means a little bit of Django form gymnastics to get
everything working.  Little of that complexity is associated with
using django-tutelary, but it does show how easy it is to do more
complex view management without django-tutelary getting in the way.

.. _example/exampleapp/views.py: https://github.com/Cadasta/django-tutelary/blob/master/example/exampleapp/views.py

.. _example/exampleapp/backends.py: https://github.com/Cadasta/django-tutelary/blob/master/example/exampleapp/backends.py

.. _base template: https://github.com/Cadasta/django-tutelary/blob/master/example/exampleapp/templates/exampleapp/base.html

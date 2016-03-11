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
object for the view to succeed.  (There are some exceptions to this
statement, related to "collective actions" -- see below.)

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
  requests for the given HTTP method are always permitted.  This
  facility be useful for cases where it's desirable for unpermissioned
  users to be able to access the forms to perform particular actions,
  even if the actions then subsequently fail when form data is POSTed.
  For example, you might want to allow any user to access the form for
  creation of new entities, and for permissioning only to be applied
  at the point where the user submits the form and the object is to be
  created.  An example is presented below.

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

Special treatment of collective actions
---------------------------------------

There are a couple of extra features for annotating views that are
intended to make some common use cases with "collective actions" work
more smoothly.  In this context, "collective actions" means actions
that refer to more than one object at a time.  In normal Django
generic views, any views that use the ``SingleObjectMixin`` class
don't refer to collective actions, while those that use the
``MultipleObjectMixin`` class do.  Similary, when using the Django
REST Framework, generic views that use the ``ListModelMixin`` class
are collective actions and most others are not.

The essential issue with collective actions is that a user may have
permission to perform a particular action on only a subset of the
queryset of a view.  Normally, django-tutelary checks that the
requested actions are permitted on *all* the objects in the queryset.
If any of these permission checks fail, then the entire attempt to
render the view will fail and a ``PermissionDenied`` exception will be
raised.  This behaviour is reasonable, but there is an alternative and
equally reasonable option, which is to filter the view's queryset so
that only objects for which the action is permitted remain.

As a concrete example, suppose that we have models representing
organisations and projects in our application.  Each project belongs
to a single organisation.  Our models look like this (all the code
examples shown in this section are just sketches -- you'd obviously
need to add some things to fully functional working models and views,
but we'll show enough to illustrate the permissioning issues)::

  @permissioned_model
  class Organization(models.Model):
      name = models.CharField(max_length=100)

      class TutelaryMeta:
          perm_type = 'org'
          path_fields = ('pk',)
          actions = [('org.list',   {'permissions_object': None}),
                     ('org.create', {'permissions_object': None}),
                     'org.detail',
                     'org.delete']

  @permissioned_model
  class Project(models.Model):
      name = models.CharField(max_length=100)
      organization = models.ForeignKey(Organization)

      class TutelaryMeta:
          perm_type = 'project'
          path_fields = ('organization', 'pk')
          actions = [('project.list',
                      {'permissions_object': 'organization'}),
                     ('project.create',
                      {'permissions_object': 'organization'}),
                     'project.detail',
                     'project.delete']

Suppose that we wish to provide a view to list all projects in the
database.  Using a DRF ``ListAPIView``, our view might look something
like this::

  class ProjectListView(PermissionRequiredMixin, ListAPIView):
      queryset = Project.objects.all()
      serializer_class = ProjectSerializer
      permission_required = 'project.list'

Now, suppose that we process a request to render this view for a user
who has ``project.list`` permissions for the ``Organization`` with
name ``org1``, but not for ``org2``.  As it stands, assuming that
projects exist in both of these organizations, this user's request
will fail with a ``PermissionDenied`` exception, because the
``project.list`` action has to be allowed for all of the objects in
the view's queryset, which includes both projects in ``org1`` (that
the user can list) and projects in ``org2`` (that the user is not
permitted to list).

This is obviously inconvenient.  To make this work, we would have to
override the ``get_queryset`` method on our view and manually filter
out the objects for which the request is not permitted.  Instead of
doing this, django-tutelary allows us to specify that we want the
view's queryset to be filtered.  We do this by adding a
``permission_filter_queryset`` attribute to the view class::

  class ProjectListView(PermissionRequiredMixin, ListAPIView):
      queryset = Project.objects.all()
      serializer_class = ProjectSerializer
      permission_required = 'project.list'
      permission_filter_queryset = True

The ``permission_filter_queryset`` attribute can be set to:

 - ``False``: gives the default ("all fail if one fails") behaviour;
 - ``True``: causes querysets for all collective actions to be
   filtered -- in this case, a ``PermissionDenied`` exception is never
   raised: if the action is denied for *all* objects in the queryset,
   then an empty queryset is used for the view;
 - a sequence of "associated" action names or a dictionary mapping
   from action names to sequences of "associated" action names: in
   this case, the queryset is filtered both on the "main" action and
   the "associated" action -- this capability is intended primarily
   for list views, where it may be desirable to restrict the entities
   rendered to a subset where certain other actions can be performed.

As an example of the last, more complex case, suppose that we want to
display a list of all the projects that a user is allowed to delete.
We can do this with a view like this::

  class ProjectDeleteListView(PermissionRequiredMixin, ListAPIView):
      queryset = Project.objects.all()
      serializer_class = ProjectSerializer
      permission_required = 'project.list'
      permission_filter_queryset = ['project.delete']

This view will return all projects for which the requesting user has
the ``project.list`` permission for the associated organisation, and
for which the user has the ``project.delete`` permission on the
project itself.

Function views
--------------

For function views, there is a ``permission_required`` decorator that
works in a similar way to the ``permission_required`` decorator in
Django's default permissions system -- see the reference documentation
for details.

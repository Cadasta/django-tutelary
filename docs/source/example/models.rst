.. _example_models:

Models
======

.. note:: The code described here is in
   `example/exampleapp/models.py`_.

.. _example/exampleapp/models.py: https://github.com/Cadasta/django-tutelary/blob/master/example/exampleapp/models.py


Model classes
-------------

The example application is a simple CRUD application managing objects
of two types: "parties" and "parcels" (the names are taken from the
land tenure application we're using django-tutelary for).  Parties and
parcels both belong to "projects" and projects belong to
"organizations".  The application also manages user accounts (which
are just ``User`` objects from ``django.contrib.auth.models``) and
django-tutelary policies.  This is simple enough, but has enough
complexity to illustrate how to use django-tutelary.  (The application
was actually used to help in the development of django-tutelary, since
it seems nearly impossible to write something like this without an
example to use it on!)


Registering actions
-------------------

Each of the ``Organization`` and ``Project`` models register
django-tutelary actions for listing entities and creating and deleting
entities.  Organizations are identified as ``organization/<org-name>``
and projects (which belong to organizations) are identified as
``project/<org-name>/<proj-name>``.  This demonstrates a useful
feature of the ``path_fields`` member of the ``TutelaryMeta`` class:
if the model field referred to by an entry in ``path_fields`` is a
foreign key, then the path fields of the model referred to by the
foreign key are inserted into the object components (i.e. the owning
organization's name appears in the object identifier for projects).
The code to do this looks like this (for the ``Project`` model)::

  @permissioned_model
  class Project(models.Model):
      name = models.CharField(max_length=100)
      organization = models.ForeignKey(Organization)

      class Meta:
          ordering = ('organization', 'name')

      class TutelaryMeta:
          perm_type = 'project'
          path_fields = ('organization', 'name')
          actions = [('project.list',
                      {'description': "Can list existing projects",
                       'permissions_object': 'organization'}),
                     ('project.create',
                      {'description': "Can create projects",
                       'permissions_object': 'organization'}),
                     ('project.delete',
                      {'description': "Can delete projects"})]

Each of the ``Party`` and ``Parcel`` models registers actions to list
entities, view details of individual entities, and create, edit and
delete individual entities.  Here, the object identifiers contain the
model primary key (represented by a ``pk`` entry in ``path_fields``).
Here's the definition of the ``Parcel`` model::

  @permissioned_model
  class Parcel(models.Model):
      project = models.ForeignKey(Project)
      address = models.CharField(max_length=200)

      class Meta:
          ordering = ('project', 'address')

      class TutelaryMeta:
          perm_type = 'parcel'
          path_fields = ('project', 'pk')
          actions = [('parcel.list',
                      {'description': "Can list existing parcels",
                       'permissions_object': 'project'}),
                     ('parcel.create',
                      {'description': "Can create parcels",
                       'allow_get': True,
                       'permissions_object': 'project'}),
                     ('parcel.detail',
                      {'description': "Can view parcel details"}),
                     ('parcel.edit',
                      {'description': "Can update existing parcels",
                       'allow_get': True}),
                     ('parcel.delete',
                      {'description': "Can delete parcels",
                       'allow_get': True})]

      def get_absolute_url(self):
          return reverse('parcel-detail', kwargs={'pk': self.pk})


Decorators and metadata
-----------------------

Each of the models defined within the example application are
decorated with the ``permissioned_model`` decorator from
``tutelary.decorators``.  To enable permissions for models defined in
other Django applications, the ``permissioned_model`` function is used
in a different way, calling it directly on the model class to be
modified and passing the ``TutelaryMeta`` metadata as arguments.  This
can be seen in the way that ``tutelary.models.Policy`` and
``django.contrib.auth.models.User`` are both set up for
permissioning.  For example, the ``User`` model is set up for
permissioning like this::

  permissioned_model(
      User, perm_type='user', path_fields=['username'],
      actions=[
          ('user.list',   {'permissions_object': None}),
          ('user.create', {'permissions_object': None}),
          'user.detail',
          'user.edit',
          'user.delete'
      ]
  )


"Free-floating" actions
-----------------------

In addition to the actions associated with models, it's also possible
to have "free-floating" actions that aren't associated with any
particular model or objects.  These can be set up by calling
``Action.register``, as is done for the "statistics" action here
(``Action`` is in ``tutelary.engine``)::

  Action.register('statistics')


User policy assignments
-----------------------

The example application has one additional modelling component, which
is to record the policies that we associate with individual users
(using the ``UserPolicyAssignment`` model).  This is
application-specific, because we allow policies to contain variables
(making them potentially more like policy *templates*) and the
variables and their values are something we'd like to present in the
user interface of the application, so we need to manage them
explicitly.  We also provide a ``set_user_policies`` function to wrap
django-tutelary's ``User.assign_policies`` functionality, making use
of the user/policy assignment information that we're recording.

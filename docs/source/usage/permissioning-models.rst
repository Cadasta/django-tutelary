.. _usage_permissioning_models:

Permissioning models
====================

The primary purpose of the model-related parts of django-tutelary is
to associate django-tutelary actions and objects with Django model
classes.  To do this, we use a metadata class member within our models
called ``TutelaryMeta`` and a class decorator called
``permissioned_model``, which can also be used as a normal function to
retrospectively add django-tutelary metadata to pre-existing Django
models.  As well as actions associated with Django models, it is also
possible to register "free-floating" actions, which are a lot like
normal Django permissions.

Model metadata
--------------

In a similar way to how core Django uses the ``Meta`` class within
model classes to store model metadata, django-tutelary uses a
``TutelaryMeta`` class to hold permissions-related metadata.  The
``TutelaryMeta`` class should have the following attributes:

``perm_type``
  A string giving the type tag to use for building django-tutelary
  object names for instances of the model.  Used in conjunction with
  the ``path_fields`` attribute.

``path_fields``
  A sequence of model field names (as strings) to use for building
  django-tutelary object names for instances of the model.  Used in
  conjunction with the ``perm_type`` attribute: the object name for a
  model instance is a sequence of items separated by forward slashes,
  starting with the ``perm_type`` label, then including the values of
  each of the model fields listed in ``path_fields``.  Any entry in
  ``path_fields`` referring to a foreign key field in the model causes
  the ``path_fields`` of the foreign key's target model to be inserted
  into the object name.  For instance, if we have a ``User`` model
  with ``perm_type = 'user'`` and ``path_fields = ('username',)``,
  then user objects would be represented in JSON policy documents as
  ``user/iross``, ``user/bjenkins``, etc.  (A ``path_fields`` entry of
  ``pk`` can be used to refer to the model's primary key.)

``actions``
  A sequence of *action-label* or (*action-label*, *action-options*)
  pairs, where *action-label* is a string giving the name of an action
  (e.g. ``parcel.list``, ``board.solder``, ``page.create``) and
  *action-options* is a dictionary of action options.  Possible
  options are: ``description``, ``permissions_object`` and
  ``error_message``.  The ``description`` option gives a
  human-readable free-text description of the action.  The
  ``permissions_object`` option is either ``None`` (indicating the the
  action is "free-floating" and not associated with any particular
  object) or is a string giving the name of a foreign key field in the
  model being configured.  The result of setting the
  ``permissions_object`` option is that permissions for the relevant
  action are *not* checked on the object of the class the ``actions``
  list is attached to, but to the alternative object referred to by
  the appropriate foreign key field.  This capability is intended for
  use with "collective" actions.  For example, if all "``board``"
  entities belong to a "``project``" entity, a "``board.create``"
  action should really be referred to the ``project``, not to any
  individual board -- is the user allowed to create new boards for
  this project?  The ``error_message`` option can be used to provide a
  custom error message to be passed in a ``PermissionDenied``
  exception if access to a view fails because of permissioning on an
  action.

Here's an example of a model definition set up for use with
django-tutelary::

  @permissioned_model
  class Party(models.Model):
      project = models.ForeignKey(Project)
      name = models.CharField(max_length=100)

      class Meta:
          ordering = ('project', 'name')

      class TutelaryMeta:
          perm_type = 'party'
          path_fields = ('project', 'pk')
          actions = [
              ('party.list',
               {'description': "List existing parties",
                'permissions_object': 'project'}),
              ('party.create',
               {'description': "Create parties",
                'permissions_object': 'project'}),
              ('party.detail',
               {'description': "View details of a party",
                'error_message': "Detail view is not allowed"}),
              ('party.edit',
               {'description': "Update existing parties"}),
              ('party.delete',
               {'description': "Delete parties"})
          ]

In this case, as well as the normal Django ``Meta`` class member, we
also set up a ``TutelaryMeta`` class member.  This gives the
permission type of the model as ``party`` and the ``path_fields`` as
``project`` and ``name`` -- together these mean that django-tutelary
will refer to objects of class ``Party`` as ``party/.../<pk>``, where
the ``...`` will be filled based on the ``path_fields`` of class
``Project`` (since ``project`` is a foreign key field here).

The ``actions`` list here defines five actions, two of which
(``party.list`` and ``party.create``) are "collective" actions,
meaning that they are permissioned on the ``project`` field of the
``Party`` model.

The ``permissioned_model`` function
-----------------------------------

The ``permissioned_model`` function, defined in
``tutelary.decorators`` can be used either as a class decorator for a
Django model class containing a ``TutelaryMeta`` metadata class, or
can be used as a normal function to add django-tutelary metadata to an
existing model class.

As a class decorator, ``permissioned_model`` is used as follows::

  from tutelary.decorators import permissioned_model
  from django.db import models

  ...

  @permissioned_model
  class AModel(models.Model):
    # Field definitions
    ...

    class TutelaryMeta:
      perm_type = ...
      path_fields = ...
      actions = ...

As a normal function, ``permissioned_model`` must be passed a Django
model class and keyword arguments giving the ``TutelaryMeta``
attributes ``perm_type``, ``path_fields`` and ``actions``::

  permissioned_model(AnExistingModel,
                     perm_type=..., path_fields=..., actions=...)

Action registration
-------------------

Actions listed in the ``TutelaryMeta`` metadata or passed in the
``actions`` argument to the ``permissioned_model`` function are
automatically associated with a Django model.  In some cases, it may
be useful also to have "free-floating actions" that are not associated
with a particular model.  These actions are more like what the default
Django permissioning system called "permissions" and are useful for
controlling access to views for summary pages or other resources that
aren't directly tied to Django models.

To register a free-floating action, use the ``Action.register`` class
method.  For example::

  Action.register('statistics')

After this call, the action name ``statistics`` can be used in
permissions queries and in the ``permission_required`` attribute for
``PermissionsRequiredMixin``.

Examples
--------

Suppose that we have a pair of related models, ``Organization`` and
``Project``, with ``Project`` instances belonging to an
``Organization`` so that ``Project`` has a foreign key to
``Organization``.  We can set up these models with django-tutelary
permissions as follows::

  @permissioned_model
  class Organization(models.Model):
      name = models.CharField(max_length=100)

      class Meta:
          ordering = ('name',)

      class TutelaryMeta:
          perm_type = 'organization'
          path_fields = ('name',)
          actions = [
              ('org.list',   {'permissions_object': None}),
              ('org.create', {'permissions_object': None}),
              'org.delete'
          ]


  @permissioned_model
  class Project(models.Model):
      name = models.CharField(max_length=100)
      organization = models.ForeignKey(Organization)

      class Meta:
          ordering = ('organization', 'name')

      class TutelaryMeta:
          perm_type = 'project'
          path_fields = ('organization', 'name')
          actions = [
              ('project.list',
               {'permissions_object': 'organization'}),
              ('project.create',
               {'permissions_object': 'organization'}),
              'project.delete'
          ]

In policies, ``Organization`` objects are then represented as
``organization/<org-name>`` and projects as
``project/<org-name>/<project-name>``.  Using the ``organization``
foreign key field in the ``path_fields`` metadata attribute of the
``Project`` model causes the ``path_fields`` from the ``Organization``
model to be spliced into the object names used for ``Project``
instances.

To add django-tutelary permissioning metadata to an existing Django
model, such as the ``User`` model, we can do something like this::

  permissioned_model(
      User, perm_type='user', path_fields=['username'],
      actions=[
          ('user.list',
           {'description': "Can list existing users",
            'permissions_object': None}),
          ('user.detail',
           {'description': "Can view details of a user"}),
          ('user.create',
           {'description': "Can create users",
            'permissions_object': None,
            'allow_get': True}),
          ('user.edit',
           {'description': "Can update existing users",
            'allow_get': True}),
          ('user.delete',
           {'description': "Can delete users",
            'allow_get': True})
      ]
  )

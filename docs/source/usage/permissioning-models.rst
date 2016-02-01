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
  A sequence of (*action-label*, *action-description*) pairs, where
  *action-label* is a string giving the name of an action
  (e.g. ``parcel.list``, ``board.solder``, ``page.create``) and
  *action-description* is a human readable free-text description of
  the action.  Each pair may optionally include a third item, listing
  HTTP methods for which permissions should not be applied -- this may
  be useful for cases where it's desirable for unpermissioned users to
  be able to access the forms to perform particular actions, even if
  the actions then subsequently fail when form data is POSTed.  (For
  example, you might want to allow any user to access the form for
  creation of new entities, and for permissioning only to be applied
  at the point where the user submits the form and the object is to be
  created.)

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
    field definitions...

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

Suppose that we have a pair of related models, ``Organisation`` and
``Project``, with ``Project`` instances belonging to an
``Organisation`` so that ``Project`` has a foreign key to
``Organisation``.  We can set up these models with django-tutelary
permissions as follows::

  @permissioned_model
  class Organisation(models.Model):
      name = models.CharField(max_length=100)

      class Meta:
          ordering = ('name',)

      class TutelaryMeta:
          perm_type = 'organisation'
          path_fields = ('name',)
          actions = (('org.list', "List existing organisations"),
                     ('org.create', "Create organisations"),
                     ('org.delete', "Delete organisations"))


  @permissioned_model
  class Project(models.Model):
      name = models.CharField(max_length=100)
      organisation = models.ForeignKey(Organisation)

      class Meta:
          ordering = ('organisation', 'name')

      class TutelaryMeta:
          perm_type = 'project'
          path_fields = ('organisation', 'name')
          actions = (('project.list', "List existing projects"),
                     ('project.create', "Create projects"),
                     ('project.delete', "Delete projects"))

In policies, ``Organisation`` objects are then represented as
``organisation/<org-name>`` and projects as
``project/<org-name>/<project-name>``.  Using the ``organisation``
foreign key field in the ``path_fields`` metadata attribute of the
``Project`` model causes the ``path_fields`` from the ``Organisation``
model to be spliced into the object names used for ``Project``
instances.

To add django-tutelary permissioning metadata to an existing Django
model, such as the ``User`` model, we can do something like this::

  permissioned_model(
    User, perm_type='user', path_fields=['username'],
    actions=(('user.list', "Can list existing users"),
             ('user.detail', "Can view details of a user"),
             ('user.create', "Can create users", ['GET']),
             ('user.edit', "Can update existing users", ['GET']),
             ('user.delete', "Can delete users", ['GET']))
  )

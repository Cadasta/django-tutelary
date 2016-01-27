.. _example_permissions:

Permissions interface
=====================

The surface area of the django-tutelary permissions management part of
the example application is surprisingly small:

Model annotations
-----------------

The ``permissioned_model`` decorator or function is used to register
action names for models and to provide django-tutelary with the
information it needs to derive object paths for model instances.

View permissioning
------------------

We use the ``PermissionRequiredMixin`` in all of our view classes to
enable django-tutelary permission checking for them.  We only need to
derive our own mixin here because we want custom behaviour in "no
permissions" cases.

Policy handling
---------------

Policies are at the heart of django-tutelary, and all applications
using policy-based permissions need to manage them somehow.  I've
tried not to impose any real requirements on this aspect of
applications that use django-tutelary: policies are just normal Django
models, and you can manage them more or less as you want in your
applications.  The example application manages django-tutelary
policies as just another kind of object, using common CRUD operations
(themselves permissioned by django-tutelary).

Custom backend
--------------

We need to enable the django-tutelary permissions backend in our
settings file.  In the example application, we further derive a custom
backend to allow for switching between users without authentication
for the purposes of the example.

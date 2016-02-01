.. _ref_django:

=======================
Public Django interface
=======================

Policies
--------

.. autoclass:: tutelary.models.Policy

   .. py:attribute:: name
      :annotation: = Policy name field.

   .. py:attribute:: body
      :annotation: = Policy body field (JSON).

.. autofunction:: tutelary.models.assign_user_policies


Permissioning models
--------------------

.. autofunction:: tutelary.decorators.permissioned_model


Permissions for views
---------------------

.. autoclass:: tutelary.mixins.PermissionRequiredMixin

.. autofunction:: tutelary.decorators.permission_required


Permissions backend
-------------------

.. autoclass:: tutelary.backends.Backend
   :members:


Exceptions
----------

.. autoexception:: tutelary.exceptions.EffectException

.. autoexception:: tutelary.exceptions.PatternOverlapException

.. autoexception:: tutelary.exceptions.PolicyBodyException

.. autoexception:: tutelary.exceptions.VariableSubstitutionException

.. autoexception:: tutelary.exceptions.DecoratorException

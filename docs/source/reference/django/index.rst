.. _ref_django:

=======================
Public Django interface
=======================

Policies
--------

.. autoclass:: tutelary.models.Policy
   :members:
   :undoc-members:

.. autofunction:: tutelary.models.assign_user_policies


Permissioning models
--------------------

.. autofunction:: tutelary.decorators.permissioned_model


Permissions for views
---------------------

.. autoclass:: tutelary.mixins.PermissionRequiredMixin


Permissions backend
-------------------

.. autoclass:: tutelary.backends.Backend


Exceptions
----------

.. autoexception:: tutelary.exceptions.EffectException

.. autoexception:: tutelary.exceptions.PatternOverlapException

.. autoexception:: tutelary.exceptions.PolicyBodyException

.. autoexception:: tutelary.exceptions.VariableSubstitutionException

.. autoexception:: tutelary.exceptions.DecoratorException

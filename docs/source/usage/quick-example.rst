.. _usage_quick_example:

A quick example
===============

Models
------

Suppose that we have a Django model called ``Organisation`` we want to
manage with django-tutelary.  We mark up the basic model definition
using a decorator (``permissioned_model``) and a metadata class
(``TutelaryMeta``)::

  from django.db import models
  from tutelary.decorators import permissioned_model

  @permissioned_model
  class Organisation(models.Model):
      name = models.CharField(max_length=100)

      class TutelaryMeta:
          perm_type = 'organisation'
          path_fields = ('name',)
          actions = (('org.list', "List existing organisations"),
                     ('org.create', "Create organisations"),
                     ('org.delete', "Delete organisations"))

Here, the ``TutelaryMeta`` class carries metadata describing the
actions that can be performed on an ``Organisation`` object, and how
to represent instances of ``Organisation`` as django-tutelary objects.
Here, an ``Organisation`` with ``name = "Cadasta"`` would be
represented by the django-tutelary object ``organisation/Cadasta``,
based on the ``perm_type`` and ``path_fields`` values.

Views
-----

The link between the view used to perform particular operations on
Django objects and the django-tutelary permissions required to perform
those operations is made in the following way::

  from django.core.urlresolvers import reverse_lazy
  import django.views.generic.edit as edit
  from tutelary.mixins import PermissionRequiredMixin
  from .models import Organisation

  class OrganisationDelete(PermissionRequiredMixin,
                           edit.DeleteView):
      model = Organisation
      success_url = reverse_lazy('organisation-list')
      permission_required = 'org.delete'

Here, we use a normal Django class-based view and mix in
django-tutelary's ``PermissionRequiredMixin``.  This mixin uses the
``permission_required`` attribute on the ``OrganisationDelete`` view
to determine which django-tutelary action this view corresponds to.
If a user attempts to delete an organisation, the user's associated
permission set (generated from the policies assigned to the user) is
used to determine whether the ``org.delete`` action is allowed on the
organisation in question.  If the action is *allowed*, view processing
proceeds as normal.  If the action is *denied*, a ``PermissionDenied``
exception is raised.

Policies
--------

Policies can be read from JSON files or stored in a database.  Here's
a simple example of reading a couple of policy documents from files,
and assigning them to a user::

  from django.contrib.auth.models import User
  from tutelary.models import Policy

  default_p = Policy(name='default',
                     body=open('default-policy.json').read())
  default_p.save()
  sysadmin_p = Policy(name='sys-admin',
                      body=open('sys-admin-policy.json').read())
  sysadmin_p.save()

  sysadmin = User.objects.get(username='admin')
  sysadmin.assign_policies(default_p, sysadmin_p)

After the call to ``User.assign_policies``, any subsequent permissions
queries against the ``admin`` user will be answered according to the
contents of the policies in the ``default-policy.json`` and
``sys-admin-policy.json`` files.

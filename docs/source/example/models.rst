.. _example_models:

Models
======

.. note: The code described here is in
   ``example/exampleapp/models.py``.

The example application is a simple CRUD application managing objects
of two types: "parties" and "parcels" (the names are taken from the
land tenure application we're using django-tutelary for).  Parties and
parcels both belong to "projects" and projects belong to
"organisations".  The application also manages user accounts (which
are just ``User`` objects from ``django.contrib.auth.models``) and
django-tutelary policies.  This is simple enough, but has enough
complexity to illustrate how to use django-tutelary.  (The application
was actually used to help in the development of django-tutelary, since
it seems nearly impossible to write something like this without an
example to use it on!)

Each of the ``Organisation`` and ``Project`` models register
django-tutelary actions for listing entities and creating and deleting
entities.  Organisations are identified as ``organisation/<org-name>``
and projects (which belong to organisations) are identified as
``project/<org-name>/<proj-name>``.  This demonstrates a useful
feature of the ``path_fields`` member of the ``TutelaryMeta`` class:
if the model field referred to by an entry in ``path_fields`` is a
foreign key, then the path fields of the model referred to by the
foreign key are inserted into the object components (i.e. the owning
organisation's name appears in the object identifier for projects).

Each of the ``Party`` and ``Parcel`` models registers actions to list
entities, view details of individual entities, and create, edit and
delete individual entities.  Here, the object identifiers contain the
model primary key (represented by a ``pk`` entry in ``path_fields``).

Each of the models defined within the example application are
decorated with the ``permissioned_model`` decorator from
``tutelary.decorators``.  To enable permissions for models defined in
other Django applications, the ``permissioned_model`` function is used
in a different way, calling it directly on the model class to be
modified and passing the ``TutelaryMeta`` metadata as arguments.  This
can be seen in the way that ``tutelary.models.Policy`` and
``django.contrib.auth.models.User`` are both set up for permissioning.

In addition to the actions associated with models, it's also possible
to have "free-floating" actions that aren't associated with any
particular model or objects.  These can be set up by calling
``Action.register``, as is done for the "statistics" action here.
(``Action`` is in ``tutelary.base``.)

The example application has one additional modelling component, which
is to record the policies that we associate with individual users
(using the ``UserPolicyAssignment`` model).  This is
application-specific, because we allow policies to contain variables
(making them potentially more like policy templates) and the variables
and their values are something we'd like to present in the user
interface of the application, so we need to manage them explicitly.
We also provide a ``set_user_policies`` function to wrap
django-tutelary's ``User.assign_policies`` functionality, making use
of the user/policy assignment information that we're recording.

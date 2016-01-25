.. _example_setup:

Set up and run
==============

Assuming that you have all the dependencies of django-tutelary
installed, you can set up the example application by doing the
following::

  $ cd example
  $ ./manage.py migrate
  $ ./manage.py loaddata test-data.json
  $ ./manage.py runserver

After this, the example application should be listening on port 8000
with some sample data in its database.  (The sample data is created by
the ``db-setup.py`` script in the ``example`` directory, the written
to a JSON file using Django's ``./manage.py dumpdata`` command.)

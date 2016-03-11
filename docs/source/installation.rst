.. _installation:

============
Installation
============

You can install either the latest stable or development versions of
django-tutelary.

Requirements
============

The django-tutelary package works with the following Python and Django
versions:

- Python (3.5)
- Django (1.9)

The latest stable version
=========================

The latest, stable version is always available via the `Python package
index_` (PyPI).  You can download the latest version on `the site`_
but most users will probably prefer either ``pip`` or
``easy_install``::

    pip install django-tutelary

or with easy_install::

    easy_install django-tutelary

.. _the site: http://pypi.python.org/pypi/django-tutelary/
.. _Python package index: http://pypi.python.org/pypi

Development version
===================

The latest development version can be found in its `Github
account`_. You can check the package out using::

    git clone https://github.com/Cadasta/django-tutelary.git

Then install it manually::

    cd django-tutelary
    python setup.py install

.. _Github account: https://github.com/Cadasta/django-tutelary/


Configuration
=============

To enable django-tutelary you need to add the package to your
``INSTALLED_APPS`` setting within your ``settings.py``::

    INSTALLED_APPS = (
        ...
        'tutelary',
    )

You also need to add the ``audit_log`` middleware to your
``MIDDLEWARE_CLASSES``::

    MIDDLEWARE_CLASSES = [
        ...
        'audit_log.middleware.UserLoggingMiddleware',
    ]

(This is used for tracking edits to permissions policies in the
database.)

Finally, you need to enable the django-tutelary authentication backend
by adding the following to ``settings.py``::

    AUTHENTICATION_BACKENDS = ['tutelary.backends.Backend']

(You may want to derive a custom authentication backend from
``tutelary.backends.Backend``.  The example application demonstrates
how to do this, and why you might want to do it.)

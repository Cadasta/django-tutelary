.. _usage_developers:

Information for developers
==========================

Testing
-------

Install testing requirements::

  $ pip install -r requirements.txt

Run tests with ``py.test``::

  $ py.test

You can also use the `tox <http://tox.readthedocs.org/en/latest/>`_
testing tool to run the tests against all supported versions of Python
and Django. Install tox globally, and then simply run::

  $ tox


Documentation
-------------

To build the documentation, you'll need to install `Sphinx
<http://sphinx-doc.org>`_::

  $ pip install Sphinx

To build the documentation::

  $ cd docs
  $ make html

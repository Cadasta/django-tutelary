.. django-tutelary documentation master file, created by
   sphinx-quickstart on Sun Dec 20 17:43:05 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-tutelary's documentation!
===========================================

The django-tutelary package is a policy-based permission plugin for
Django, loosely inspired by the way that permissions policies work in
Amazon's `Identity and Access Management`_ (IAM) system.

.. warning:: This is a work in progress.  Use at your own risk.  In
   particular, django-tutelary currently has no caching, so
   performance won't be stellar.  There are places where there are
   opportunities for caching both database query results and
   permissions query results, but I've yet to take advantage of them.


Documentation
=============

.. toctree::
   :maxdepth: 2

   installation
   usage/index
   example/index
   reference/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _Identity and Access Management: https://aws.amazon.com/documentation/iam/

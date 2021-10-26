.. This Software (Dioptra) is being made available as a public service by the
.. National Institute of Standards and Technology (NIST), an Agency of the United
.. States Department of Commerce. This software was developed in part by employees of
.. NIST and in part by NIST contractors. Copyright in portions of this software that
.. were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
.. to Title 17 United States Code Section 105, works of NIST employees are not
.. subject to copyright protection in the United States. However, NIST may hold
.. international copyright in software created by its employees and domestic
.. copyright (or licensing rights) in portions of software that were assigned or
.. licensed to NIST. To the extent that NIST holds copyright in this software, it is
.. being made available under the Creative Commons Attribution 4.0 International
.. license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
.. of the software developed or licensed by NIST.
..
.. ACCESS THE FULL CC BY 4.0 LICENSE HERE:
.. https://creativecommons.org/licenses/by/4.0/legalcode

.. _dev-guide-restapi:

REST API Developer's Guide
==========================

.. include:: /_glossary_note.rst

This document is for developers that plan to contribute to the Dioptra :term:`REST` :term:`API`.
Its goal is to establish guidelines for developing new endpoints and maintaining existing ones by explaining the design decisions underpinning the :term:`REST` :term:`API` code.

Overview
--------

The project's :term:`REST` :term:`API` code is located in the project's |restapi_folder|_ folder and follows an organizational scheme adapted from a blog post titled *Flask Best Practices* [pryor2019]_.
At a high level, this scheme organizes code into folders according to the endpoint it implements as opposed to grouping code by its purpose and functionality.
In other words,

   This means you should have a folder for ``widgets/`` that contains the services, type-definitions, etc for ``widgets/``, and you should NOT have a ``services/`` folder where you keep all of your services.

   -- *from* `Flask Best Practices <https://web.archive.org/web/20200729100645/http://alanpryorjr.com/2019-05-20-flask-api-example/#high-level-overview>`__

.. code-block::  none

   # restapi/ subfolders

   .
   ├── cli
   ├── experiment
   ├── job
   ├── queue
   ├── shared
   │   ├── io_file
   │   ├── mlflow_tracking
   │   ├── rq
   │   └── s3
   └── task_plugin

Implementing an Endpoint
------------------------

.. code-block:: none

   # endpoint structure

   .
   ├── __init__.py
   ├── controller.py
   ├── dependencies.py
   ├── errors.py
   ├── interface.py
   ├── model.py
   ├── routes.py
   ├── schema.py
   └── service.py

Model
~~~~~

Schema
~~~~~~

Service
~~~~~~~

Controller
~~~~~~~~~~

Dependencies, Errors, and Routes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

References
----------

.. [pryor2019] A. J. Pryor, *Flask Best Practices*, A Portfolio by AJ Pryor - A
   Collection of Data Science and High-performance Computing Projects. Sep. 2019.
   Accessed on: Oct. 19, 2021. [Online]. Available:
   `http://alanpryorjr.com/2019-05-20-flask-api-example/ <https://web.archive.org/web/20200729100645/http://alanpryorjr.com/2019-05-20-flask-api-example/>`_.

.. Links

.. _FlaskApiExample: https://github.com/apryor6/flask_api_example
.. _restapi_folder: https://github.com/usnistgov/dioptra/tree/main/src/mitre/securingai/restapi

.. Replacements

.. |restapi_folder| replace:: ``src/mitre/securingai/restapi``

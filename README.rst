Muffin-Prometheus
#################

.. _description:

**Muffin-Prometheus** -- Prometheus_ metrics exporter for Muffin_ framework

.. _badges:

.. image:: https://github.com/klen/muffin-prometheus/workflows/tests/badge.svg
    :target: https://github.com/klen/muffin-prometheus/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/muffin-prometheus
    :target: https://pypi.org/project/muffin-prometheus/
    :alt: PYPI Version

.. image:: https://img.shields.io/pypi/pyversions/muffin-prometheus
    :target: https://pypi.org/project/muffin-prometheus/
    :alt: Python Versions

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.7

.. _installation:

Installation
=============

**Muffin-prometheus** should be installed using pip: ::

    pip install muffin-prometheus

.. _usage:

Usage
=====


Initialize and setup the plugin:

.. code-block:: python

    import muffin
    import muffin_babel

    # Create Muffin Application
    app = muffin.Application('example')

    # Initialize the plugin
    # As alternative: babel = muffin_prometheus.Plugin(app, **options)
    prometheus = muffin_prometheus.Plugin()
    prometheus.setup(app, group_paths=['/api'])


Options
-------

=========================== =========================== =========================== 
Name                        Default value               Desctiption
--------------------------- --------------------------- ---------------------------
**metrics_url**             ``"/dev/prometheus"``       HTTP Path to export metrics for Prometheus_
**group_paths**             ``[]``                      List of path's prefixes to group. A path which starts from the prefix will be grouped
=========================== =========================== =========================== 


You are able to provide the options when you are initiliazing the plugin:

.. code-block:: python

    session.setup(app, metrics_url='/metrics', group_paths=['/views', '/api/v1', '/api/v2'])


Or setup it inside ``Muffin.Application`` config using the ``PROMETHEUS_`` prefix:

.. code-block:: python

   PROMETHEUS_METRICS_URL = '/metrics'

   PROMETHEUS_GROUP_PATHS = ['/views', '/api/v1', '/api/v2']

``Muffin.Application`` configuration options are case insensitive


.. _bugtracker:

Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/muffin-session/issues

.. _contributing:

Contributing
============

Development of Muffin-Session happens at: https://github.com/klen/muffin-session


Contributors
=============

* klen_ (Kirill Klenov)

.. _license:

License
========

Licensed under a `MIT license`_.

.. _links:


.. _klen: https://github.com/klen
.. _Muffin: https://github.com/klen/muffin
.. _Prometheus: https://prometheus.io

.. _MIT license: http://opensource.org/licenses/MIT

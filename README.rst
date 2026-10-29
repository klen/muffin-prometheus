Muffin-Prometheus
#################

.. _description:

**Muffin-Prometheus** -- Prometheus_ metrics exporter for Muffin_ framework

The plugin adds an ASGI middleware which counts requests, response times, response
codes and exceptions, and serves the exposition text on a configured URL.

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

- python >= 3.11

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
    import muffin_prometheus

    # Create Muffin Application
    app = muffin.Application("example")

    # Initialize the plugin
    # As alternative: prometheus = muffin_prometheus.Plugin(app, **options)
    prometheus = muffin_prometheus.Plugin()
    prometheus.setup(app, group_paths=["/api"])

The plugin registers a middleware (there is no route to add manually), so metrics are
collected from the moment the plugin is set up.

.. _metrics:

Metrics
=======

The names and labels come from `asgi-prometheus`_, which is the middleware this plugin
drives:

======================== ============ ==================================================
Metric                   Type         Labels
======================== ============ ==================================================
``requests_count``       counter      ``method``, ``path``
``requests_time``        histogram    ``method``, ``path`` (seconds)
``requests_in_progress`` gauge        ``method``, ``path``
``responses_count``      counter      ``method``, ``path``, ``status``
``exceptions_count``     counter      ``method``, ``path``, ``exception``
======================== ============ ==================================================

The names above are the client-side metric names. In the exposition text they get the
usual suffixes: ``requests_count_total``, ``responses_count_total``,
``exceptions_count_total``, and ``requests_time_bucket`` / ``_count`` / ``_sum`` for the
histogram. ``requests_in_progress`` has no suffix. Prometheus will store them under the
same names, so this is what you query:

.. code-block:: text

    requests_count_total{method="GET",path="/api*"} 42.0
    requests_time_bucket{le="0.1",method="GET",path="/api*"} 40.0
    requests_time_count{method="GET",path="/api*"} 42.0
    requests_time_sum{method="GET",path="/api*"} 1.734
    requests_in_progress{method="GET",path="/api*"} 1.0
    responses_count_total{method="GET",path="/api*",status="200"} 41.0
    exceptions_count_total{method="GET",path="/api*",exception="ValueError"} 1.0

The client also exports ``*_created`` samples (a Unix timestamp of the metric creation
time). They are not counters; ignore them in queries.

Label values
------------

``method`` is the HTTP method of the request. ``status`` is the response status code as
a string. ``exception`` is the class name of the raised exception
(``ValueError``, ``ZeroDivisionError``, …).

``path`` is the request path reduced by the ``group_paths`` option (see below). It is
never the raw path: labels only carry the prefixes you have configured, which is what
keeps the number of series bounded on routes with IDs. The trade-off is that an
unmatched path is not described by its own label value at all; see the next section.

``path`` labels and ``group_paths``
-----------------------------------

Before the metrics are updated, the request path goes through ``process_path()`` from
`asgi-prometheus`_. It walks the path from the full value upwards, cutting one segment
at a time, and stops at the first segment which is present in ``group_paths``. That
prefix gets a ``*`` appended. If nothing matches, the label is empty.

.. code-block:: python

    process_path("/api/v1/users/42", {"/api"})           # "/api*"
    process_path("/api/v1/users/42", {"/api/v1/users"})  # "/api/v1/users*"
    process_path("/apiary", {"/api"})                    # ""
    process_path("/api/v1/users/42", set())              # ""

Prefixes are matched per whole path segment, so ``/api`` covers ``/api/v1/users/42``
but not ``/apiary``.

Without ``group_paths`` every request ends up in a single ``path=""`` series, whatever
the URL was: ``/``, ``/unknown`` and ``/api/v1/users/42`` are indistinguishable. So set
the prefixes you actually want to query. Group them coarsely: ``["/api"]`` gives one
series per method, while ``["/api/v1/users", "/api/v1/orders", …]`` gives one series per
listed route, which is the point where the number of series starts to matter again.

.. _endpoint:

Metrics endpoint
================

``metrics_url`` is served by the plugin's middleware itself
(``return ResponseText(get_metrics())``), not by a route. Consequences:

- No route registration is needed, and a route on the same path is never reached.
- The endpoint only exists while the plugin is enabled; without the plugin the path is
  a normal 404 (or a normal route).
- Requests to ``metrics_url`` are answered before the request counters are touched, so
  they do not appear in the metrics themselves.
- Muffin builds the middleware chain in registration order: the first registered
  middleware is the outermost one. If the plugin is set up right after the application
  is created, ``/metrics`` is answered before any middleware registered later, which
  includes your own auth, logging and CORS middlewares. A middleware registered
  *before* the plugin still runs first and can block the endpoint.

The endpoint has no authentication: anyone who can reach the application can read all
the metrics, including route prefixes and exception class names. Keep it on an internal
port or filter it in your reverse proxy.

.. _queries:

PromQL examples
===============

.. code-block:: text

    # requests per second, grouped by path label
    sum by (path) (rate(requests_count_total[5m]))

    # p95 response time per path
    histogram_quantile(
      0.95,
      sum by (le, path) (rate(requests_time_bucket[5m]))
    )

    # average response time per path (same as the histogram average)
    sum by (path) (rate(requests_time_sum[5m]))
      / sum by (path) (rate(requests_time_count[5m]))

    # exceptions per minute by exception type
    sum by (exception) (rate(exceptions_count_total[1m])) * 60

    # responses per second by status code
    sum by (status) (rate(responses_count_total[5m]))

    # requests currently being processed
    sum(requests_in_progress)

.. _options:

Options
=======

=========================== =========================== ===========================
Name                        Default value               Description
--------------------------- --------------------------- ---------------------------
**metrics_url**             ``"/dev/prometheus"``       HTTP Path to export metrics for Prometheus_
**group_paths**             ``[]``                      Path prefixes to group. The first prefix matching the path becomes the ``path`` label with a ``*`` suffix, everything else gets an empty label
**disabled**                ``False``                   Don't register the plugin (no middleware, no metrics)
=========================== =========================== ===========================

You are able to provide the options when you initialize the plugin:

.. code-block:: python

    prometheus.setup(app, metrics_url="/metrics", group_paths=["/views", "/api/v1", "/api/v2"])

Or set them in the ``Muffin.Application`` config using the ``PROMETHEUS_`` prefix
(the options are case insensitive):

.. code-block:: python

   app = muffin.Application(
       PROMETHEUS_METRICS_URL="/metrics",
       PROMETHEUS_GROUP_PATHS=["/views", "/api/v1", "/api/v2"],
   )

The same options can be passed as environment variables with the
``MUFFIN_PROMETHEUS_`` prefix (``MUFFIN_`` is the default application name), and the
values are parsed as JSON: ``MUFFIN_PROMETHEUS_METRICS_URL=/metrics``,
``MUFFIN_PROMETHEUS_GROUP_PATHS='["/api"]'``.

Unknown options are ignored silently; a typo in an option name is not reported.

.. _limitations:

Known limitations
=================

- Only responses returned by the request handler are counted in ``responses_count``.
  HTTP errors (404, 405, …) are exceptions of the form ``ResponseError`` in
  `asgi-tools`_, and they are not ``Exception`` subclasses, so they land neither in
  ``responses_count`` nor in ``exceptions_count``; they only show up in
  ``requests_count``. ``exceptions_count`` collects real exceptions raised from the
  handler, before the framework converts them into a 500 response.
- Multiprocess mode is supported: when ``PROMETHEUS_MULTIPROC_DIR`` is set, the
  exposition is built from the per-worker files (counters and histograms are summed
  across workers, as usual for ``prometheus_client``). The gauge keeps its default
  ``all`` mode, so ``requests_in_progress`` is exported once per worker with an extra
  ``pid`` label; aggregate it with ``sum()`` or alert on the individual workers.

.. _bugtracker:

Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at https://github.com/klen/muffin-prometheus/issues

.. _contributing:

Contributing
============

Development of the plugin happens at: https://github.com/klen/muffin-prometheus

.. code-block:: shell

    uv sync --all-extras --dev
    uv run pytest
    uv run ruff check
    uv run pyrefly check

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
.. _asgi-prometheus: https://github.com/klen/asgi-prometheus
.. _asgi-tools: https://github.com/klen/asgi-tools

.. _MIT license: http://opensource.org/licenses/MIT

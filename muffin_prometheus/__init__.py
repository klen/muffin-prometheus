"""Provide prometheus metrics for Muffin framework."""

import time

from asgi_prometheus import (EXCEPTIONS, REQUESTS, REQUESTS_IN_PROGRESS, REQUESTS_TIME, RESPONSES,
                             get_metrics, process_path)
from asgi_tools.types import TASGIApp, TASGIReceive, TASGISend
from muffin import Request, Response, ResponseText
from muffin.plugins import BasePlugin

__version__ = "1.2.0"
__project__ = "muffin-prometheus"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


class Plugin(BasePlugin):

    """Support prometheus metrics."""

    name = "prometheus"
    defaults = {
        "group_paths": [],
        "metrics_url": "/dev/prometheus",
    }

    async def middleware(  # type: ignore
        self,
        handler: TASGIApp,
        request: Request,
        receive: TASGIReceive,
        send: TASGISend,
    ):
        """Collect the metrics."""
        path, method = request.path, request.method
        if path == self.cfg.metrics_url:
            return ResponseText(get_metrics())

        path = process_path(path, self.cfg.group_paths)

        REQUESTS.labels(method=method, path=path).inc()
        REQUESTS_IN_PROGRESS.labels(method=method, path=path).inc()

        try:
            before_time = time.perf_counter()
            res = await handler(request, receive, send)
            after_time = time.perf_counter()
            REQUESTS_TIME.labels(method=method, path=path).observe(
                after_time - before_time
            )
            if isinstance(res, Response):
                RESPONSES.labels(method=method, path=path, status=res.status_code)

            return res

        except Exception as exc:
            EXCEPTIONS.labels(
                method=method, path=path, exception=type(exc).__name__
            ).inc()
            raise exc from None

        finally:
            REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()

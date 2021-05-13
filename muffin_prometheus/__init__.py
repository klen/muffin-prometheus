"""Provide prometheus metrics for Muffin framework."""

import time
import typing as t

from muffin import Request, Response, ResponseText
from muffin.typing import Receive, Send, ASGIApp
from muffin.plugins import BasePlugin
from asgi_prometheus import (
    get_metrics, process_path, REQUESTS, REQUESTS_TIME, REQUESTS_IN_PROGRESS, RESPONSES, EXCEPTIONS
)


__version__ = "1.0.3"
__project__ = "muffin-prometheus"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


class Plugin(BasePlugin):

    """Support prometheus metrics."""

    name = 'prometheus'
    defaults: t.Dict = {
        'group_paths': [],
        'metrics_url': '/dev/prometheus',
    }

    async def middleware(self, handler: ASGIApp, request: Request, receive: Receive, send: Send):  # type: ignore  # noqa
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
            REQUESTS_TIME.labels(method=method, path=path).observe(after_time - before_time)
            if isinstance(res, Response):
                RESPONSES.labels(method=method, path=path, status=res.status_code)

            return res

        except Exception as exc:
            EXCEPTIONS.labels(method=method, path=path, exception=type(exc).__name__).inc()
            raise exc from None

        finally:
            REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()

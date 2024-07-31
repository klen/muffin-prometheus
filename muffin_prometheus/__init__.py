"""Provide prometheus metrics for Muffin framework."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar

from asgi_prometheus import (
    EXCEPTIONS,
    REQUESTS,
    REQUESTS_IN_PROGRESS,
    REQUESTS_TIME,
    RESPONSES,
    get_metrics,
    process_path,
)
from muffin import Request, Response, ResponseText
from muffin.plugins import BasePlugin

if TYPE_CHECKING:
    from asgi_tools.types import TASGIApp, TASGIReceive, TASGISend


class Plugin(BasePlugin):

    """Support prometheus metrics."""

    name = "prometheus"
    defaults: ClassVar = {
        "group_paths": [],
        "metrics_url": "/dev/prometheus",
    }

    async def middleware(  # type: ignore[override]
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
                after_time - before_time,
            )
            if isinstance(res, Response):
                RESPONSES.labels(method=method, path=path, status=res.status_code)

        except Exception as exc:  # noqa: BLE001
            EXCEPTIONS.labels(
                method=method,
                path=path,
                exception=type(exc).__name__,
            ).inc()
            raise exc from None

        else:
            return res

        finally:
            REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()

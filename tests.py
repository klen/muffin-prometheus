import muffin
import pytest

RES_200 = 'responses_count_total{method="GET",path="",status="200"}'


@pytest.fixture
def app():
    return muffin.Application(DEBUG=True, PROMETHEUS_METRICS_URL="/metrics")


async def test_base(app, client):
    from muffin_prometheus import Plugin

    metrics = Plugin(app)
    assert metrics.cfg.metrics_url == "/metrics"

    res = await client.get("/")
    assert res.status_code == 404

    res = await client.get("/metrics")
    assert res.status_code == 200
    text = await res.text()
    assert text
    assert "requests_count_total" in text
    assert "requests_time" in text


def sample(text: str, prefix: str) -> float:
    """Read a metric value from the exposition text (0 when the sample is missing)."""
    for line in text.splitlines():
        if line.startswith(prefix):
            return float(line.rsplit(" ", 1)[-1])
    return 0.0


async def test_responses(app, client):
    from muffin_prometheus import Plugin

    Plugin(app)
    app.route("/")(lambda request: "OK")

    before = sample(await (await client.get("/metrics")).text(), RES_200)
    assert (await client.get("/")).status_code == 200
    after = sample(await (await client.get("/metrics")).text(), RES_200)

    assert after == before + 1


async def test_group_path(app, client):
    from muffin_prometheus import Plugin

    Plugin(app, group_paths=["/api", "/api/v1/users"])

    async def send_ok(request):
        return "OK"

    app.route("/")(send_ok)
    app.route("/api")(send_ok)
    app.route("/api/v1/messages")(send_ok)
    app.route("/api/v1/users/{id}")(send_ok)

    res = await client.get("/")
    assert res.status_code == 200
    assert await res.text() == "OK"

    res = await client.get("/api/v1/users/2")
    assert res.status_code == 200

    res = await client.get("/api/v1/messages")
    assert res.status_code == 200

    res = await client.get("/unknown")
    assert res.status_code == 404

    res = await client.get("/metrics")
    assert res.status_code == 200
    text = await res.text()
    assert 'requests_count_total{method="GET",path="/api*"}' in text
    assert 'requests_count_total{method="GET",path="/api/v1/users*"}' in text

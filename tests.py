import muffin
import pytest


@pytest.fixture
def app():
    return muffin.Application(DEBUG=True, PROMETHEUS_METRICS_URL='/metrics')


async def test_base(app, client):
    from muffin_prometheus import Plugin

    metrics = Plugin(app)
    assert metrics.cfg.metrics_url == '/metrics'

    res = await client.get('/')
    assert res.status_code == 404

    res = await client.get('/metrics')
    assert res.status_code == 200
    text = await res.text()
    assert text
    assert 'requests_count_total' in text
    assert 'requests_time' in text


async def test_group_path(app, client):
    from muffin_prometheus import Plugin

    Plugin(app, group_paths=['/api', '/api/v1/users'])

    async def send_ok(request):
        return 'OK'

    app.route('/')(send_ok)
    app.route('/api')(send_ok)
    app.route('/api/v1/messages')(send_ok)
    app.route('/api/v1/users/{id}')(send_ok)

    res = await client.get('/')
    assert res.status_code == 200
    assert await res.text() == 'OK'

    res = await client.get('/api/v1/users/2')
    assert res.status_code == 200

    res = await client.get('/api/v1/messages')
    assert res.status_code == 200

    res = await client.get('/unknown')
    assert res.status_code == 404

    res = await client.get('/metrics')
    assert res.status_code == 200
    text = await res.text()
    assert 'requests_count_total{method="GET",path="/api*"}' in text
    assert 'requests_count_total{method="GET",path="/api/v1/users*"}' in text

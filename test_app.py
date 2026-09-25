import fakeredis
import redis

import app as app_module
from app import alert_threshold, sanitize_input, app


def test_alert_threshold():
    assert alert_threshold() == 25


def test_sanitize_input_escapes_html():
    assert sanitize_input("<script>") == "&lt;script&gt;"


class BrokenRedis:
    def ping(self):
        raise redis.exceptions.ConnectionError("redis injoignable")


def test_health_ok_quand_redis_repond(monkeypatch):
    fake_client = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(app_module, "get_redis_client", lambda: fake_client)

    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_health_503_quand_redis_down(monkeypatch):
    monkeypatch.setattr(app_module, "get_redis_client", lambda: BrokenRedis())

    response = app.test_client().get("/health")
    assert response.status_code == 503
    assert response.get_json()["status"] == "error"


def test_status_endpoint():
    client = app.test_client()
    response = client.get("/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "projet-devops-groupe-demo"
    assert data["version"] == "1.0"


def test_visits_endpoint(monkeypatch):
    fake_client = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(app_module, "get_redis_client", lambda: fake_client)

    client = app.test_client()
    first = client.get("/visits").get_json()["visits"]
    second = client.get("/visits").get_json()["visits"]

    assert second == first + 1

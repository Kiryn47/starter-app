import fakeredis
import redis
from prometheus_client import REGISTRY

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


def test_status_expose_couleur_et_sha(monkeypatch):
    monkeypatch.setenv("DEPLOY_COLOR", "green")
    monkeypatch.setenv("GIT_SHA", "abc123")

    data = app.test_client().get("/status").get_json()
    assert data["deploy_color"] == "green"
    assert data["version_sha"] == "abc123"


def requests_count(endpoint, status="200"):
    value = REGISTRY.get_sample_value(
        "http_requests_total",
        {"method": "GET", "endpoint": endpoint, "status": status},
    )
    return value or 0


def test_compteur_incremente_a_chaque_requete():
    client = app.test_client()
    avant = requests_count("/status")
    client.get("/status")
    client.get("/status")
    assert requests_count("/status") == avant + 2


def test_metrics_ne_se_compte_pas_lui_meme():
    client = app.test_client()
    client.get("/metrics")
    client.get("/metrics")
    assert requests_count("/metrics") == 0


def test_metrics_format_prometheus():
    app.test_client().get("/status")
    response = app.test_client().get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.content_type
    assert b'http_requests_total{endpoint="/status",method="GET",status="200"}' in response.data


def test_route_inconnue_regroupee():
    app.test_client().get("/nimporte/quoi/123")
    assert requests_count("unmatched", "404") >= 1


def test_simulate_error_renvoie_500():
    avant = requests_count("/simulate-error", "500")
    response = app.test_client().get("/simulate-error")
    assert response.status_code == 500
    assert requests_count("/simulate-error", "500") == avant + 1


def test_histogramme_latence():
    labels = {"method": "GET", "endpoint": "/status"}
    avant = REGISTRY.get_sample_value("http_request_duration_seconds_count", labels) or 0
    app.test_client().get("/status")
    assert REGISTRY.get_sample_value("http_request_duration_seconds_count", labels) == avant + 1

    data = app.test_client().get("/metrics").data
    assert b"http_request_duration_seconds_bucket" in data
    assert b"http_request_duration_seconds_sum" in data
    assert b"http_request_duration_seconds_count" in data

import os
import time

import redis
from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Temps de traitement des requetes HTTP",
    ["method", "endpoint"],
)

ALERT_THRESHOLD = 25


def get_redis_client():
    """Cree un client Redis a partir des variables d'environnement REDIS_HOST/REDIS_PORT."""
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", 6379))
    return redis.Redis(
        host=host, port=port, decode_responses=True,
        socket_connect_timeout=2, socket_timeout=2,
    )


def alert_threshold():
    """Seuil d'alerte au-dessus duquel une notification est declenchee."""
    return ALERT_THRESHOLD


def sanitize_input(value):
    """Echappe les caracteres dangereux d'une entree utilisateur."""
    return value.replace("<", "&lt;").replace(">", "&gt;")


def endpoint_label():
    if request.url_rule is None:
        return "unmatched"
    return request.url_rule.rule


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def record_request(response):
    if request.path != "/metrics":
        endpoint = endpoint_label()
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()
        start = g.get("start_time")
        if start is not None:
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(time.perf_counter() - start)
    return response


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/health")
def health():
    try:
        get_redis_client().ping()
    except redis.exceptions.RedisError as exc:
        return jsonify(status="error", redis="down", detail=str(exc)), 503
    return jsonify(status="ok", redis="up"), 200


@app.route("/status")
def status():
    return jsonify(
        service="projet-devops-groupe-demo",
        version="1.0",
        deploy_color=os.environ.get("DEPLOY_COLOR", "unknown"),
        version_sha=os.environ.get("GIT_SHA", "unknown"),
    ), 200


@app.route("/simulate-error")
def simulate_error():
    return jsonify(status="error", message="erreur simulee"), 500


@app.route("/visits")
def visits():
    client = get_redis_client()
    count = client.incr("visits")
    return jsonify(visits=count), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

import os

import redis
from flask import Flask, jsonify

app = Flask(__name__)

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


@app.route("/visits")
def visits():
    client = get_redis_client()
    count = client.incr("visits")
    return jsonify(visits=count), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

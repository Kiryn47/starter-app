# starter-app

![CI](https://github.com/Kiryn47/starter-app/actions/workflows/ci.yml/badge.svg)

Petite app Flask fournie pour l'atelier CI/CD (séance 2, bloc DevOps). Deux endpoints (`/health`, `/status`) et quelques fonctions utilitaires, avec des tests pytest et du lint flake8.

## Endpoints

- `GET /health` -> `{"status": "ok"}`
- `GET /status` -> infos sur le service (nom + version)

## Installation

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

## Lancer l'app

```bash
python app.py
```

## Tests + lint

```bash
flake8 .
pytest -v --cov=app
```

## CI

Le workflow GitHub Actions (`.github/workflows/ci.yml`) tourne sur chaque push sur `main` et sur chaque pull request. Deux jobs : `lint` (flake8) d'abord, puis `test` (pytest, matrice Python 3.10/3.11/3.12) seulement si le lint passe. Les dépendances sont mises en cache et le rapport de couverture est gardé en artefact même si les tests échouent.

La branche `main` est protégée : impossible de merger une PR si un des checks CI est rouge.

## Docker

Build de l'image :

```bash
docker build -t starter-app .
```

Lancer un conteneur :

```bash
docker run -p 5000:5000 starter-app
```

Le Dockerfile est en multi-stage (un stage `builder` qui installe les dépendances dans un venv, puis un stage final sur `python:3.12-slim` qui ne récupère que ce venv). Le conteneur tourne en utilisateur non-root (`appuser`) et sert l'app avec `gunicorn` (pas le serveur de dev Flask).

Gain mesuré sur cette machine (18/09/2026) entre la version naïve (une seule étape, `python:3.12` complet, root) et la version multi-stage actuelle :

| Version | Taille |
|---|---|
| Naïve (étape 1-2) | 1.64 GB |
| Multi-stage (étape 3) | 225 MB |

Soit environ **-86%**. La quasi-totalité du gain vient du stage final basé sur `slim` : les outils de compilation et le cache pip restent dans le stage `builder`, jamais copiés dans l'image finale.

## Observabilité (Prometheus & Grafana)

### Lancer toute la stack

```bash
bash deploy/deploy.sh && docker compose up -d
```

La première commande déploie l'application (blue/green, redis, nginx). La seconde démarre les services sans profil, dont Prometheus et Grafana. Tout est provisionné au démarrage, rien n'est à configurer à la main, même après un `docker compose down -v`.

Identifiants Grafana : `admin` / `admin` par défaut. Pour les changer, copier `.env.example` en `.env` et modifier `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`.

### Où regarder

| Interface | URL | Contenu |
|---|---|---|
| Application (via nginx) | http://localhost:8080 | `/status`, `/health`, `/metrics`, `/simulate-error` |
| Prometheus | http://localhost:9090 | `/targets` (scrape de l'app), Graph (PromQL), `/alerts` |
| Grafana | http://localhost:3000 | Dashboard **Starter App - Observabilite** |

Prometheus scrape l'application à travers nginx (`nginx:80/metrics`) : il voit donc toujours la couleur active, quelle que soit la bascule blue/green.

### Métriques exposées par l'application

- `http_requests_total` (Counter) : nombre de requêtes, par `method`, `endpoint` (route Flask, `unmatched` pour les 404) et `status`. `/metrics` lui-même n'est pas compté.
- `http_request_duration_seconds` (Histogram) : temps de traitement, par `method` et `endpoint`. Permet de calculer des percentiles (p95, p99), là où une moyenne masquerait les requêtes lentes occasionnelles.

### Dashboard

Fichier : `monitoring/grafana/dashboards/starter-app.json`, rafraîchi toutes les 5 s.

- **Débit par endpoint** : requêtes par seconde pour chaque route.
- **Taux d'erreur global** : part des réponses 5xx sur l'ensemble du trafic, avec une ligne rouge à 5 %.
- **Latence p95 par endpoint** : 95 % des requêtes sont plus rapides que cette valeur.

Pour modifier le dashboard, on modifie le JSON dans le dépôt : il est en lecture seule dans l'interface.

### Alerte

Règle `TauxErreurEleve` (`monitoring/prometheus/alerts.yml`) : se déclenche si le taux d'erreur 5xx dépasse **5 % pendant au moins 30 secondes**. L'état est visible dans Prometheus → **Alerts** (`inactive` → `pending` → `firing`).

Pour la tester, envoyer du trafic mélangé pendant plus d'une minute :

```bash
for i in $(seq 1 300); do curl -s localhost:8080/status >/dev/null; curl -s localhost:8080/simulate-error >/dev/null; sleep 0.2; done
```

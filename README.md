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

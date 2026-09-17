# starter-app

![CI](https://github.com/Kiryn47/starter-app/actions/workflows/ci.yml/badge.svg)

Petite API Flask (`projet-devops-groupe-demo`) utilisée comme TP CI/CD : lint (flake8) + tests (pytest) exécutés automatiquement via GitHub Actions à chaque push/PR.

## Endpoints

- `GET /health` — vérifie que le service répond (`{"status": "ok"}`)
- `GET /status` — infos sur le service (nom, version)

## Installation locale

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

## Lancer l'application

```bash
python app.py
```

## Lancer les tests et le lint

```bash
flake8 .
pytest -v --cov=app
```

## Intégration continue

Le pipeline (`.github/workflows/ci.yml`) se déclenche sur chaque push vers `main` et sur chaque pull request. Il enchaîne un job `lint` (flake8) puis, s'il réussit, un job `test` (pytest + couverture) exécuté en matrice sur Python 3.10, 3.11 et 3.12, avec cache des dépendances pip et rapport de couverture HTML conservé en artefact téléchargeable (y compris en cas d'échec). Les checks `lint` et `test (3.10/3.11/3.12)` sont obligatoires avant tout merge sur `main`.

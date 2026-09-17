# starter-app

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

Le workflow `.github/workflows/ci.yml` exécute automatiquement `flake8` et `pytest` (avec couverture) sur chaque push et pull request vers `main`.

<!-- test étape 3 : vérification du déclenchement sur pull request -->

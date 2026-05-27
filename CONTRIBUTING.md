# Guide de contribution — E-DÉFENCE Analyse Financière IA

## Workflow

1. Créer une branche depuis `dev` : `git checkout -b feature/ma-fonctionnalite`
2. Développer et committer avec des messages clairs
3. Ouvrir une Pull Request vers `dev`
4. Attendre la revue de code de l'expert référent
5. Après approbation, merger dans `dev`

## Conventions de commit

```
type(scope): description courte

Types : feat | fix | docs | test | refactor | style | chore | ci
Exemples :
  feat(benford): ajouter visualisation distribution
  fix(auth): corriger expiration token MFA
  test(fec-parser): couvrir cas encodage ISO-8859
```

## Branches de travail

| Stagiaire | Branche |
|-----------|---------|
| MoussaNEYA | `feature/frontend-neya` |
| burkinabe | `feature/security-zombre` |

## Revue de code

- Toute PR doit être approuvée par l'expert Full Stack (frontend) ou l'expert Cybersécurité (sécurité)
- Les tests unitaires doivent passer avant merge
- Le linter (ruff / eslint) ne doit signaler aucune erreur

## Architecture à respecter

- **Backend** : FastAPI + SQLAlchemy async, pas d'ORM synchrone
- **Multi-tenancy** : toujours filtrer par `tenant_id` dans les requêtes
- **Sécurité** : jamais de données sensibles dans les logs
- **Frontend** : composants dans `components/`, pages dans `app/`

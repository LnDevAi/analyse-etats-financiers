# Changelog — E-DÉFENCE Analyse Financière IA

Toutes les modifications notables sont documentées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/) · Versioning : [SemVer](https://semver.org/lang/fr/)

---

## [Unreleased] — dev

### Ajouté
- **Anonymiseur NLP** : masquage automatique emails, tél. UEMOA, SIRET/IFU/RCCM avant traitement IA
- **Cross-checking FEC×FEC** : comparaison cellulaire de deux documents (INVERSION_SIGNE, ECART_MAJEUR…)
- **Revue analytique N vs N-1** : upload FEC exercice précédent, déviations par compte avec sévérité
- **Réinitialisation mot de passe** : flux complet forgot-password/reset-password, email SMTP brandé, token Redis 30 min
- **Contrôle cohérence SYSCOHADA** (`coherence_checker`) :
  - Soldes normaux par préfixe de compte (Cl.1–7)
  - Cohérence résultat net : (Cl.7 − Cl.6) vs compte 13x
  - Équilibre Actif/Passif reconstruit depuis le FEC
  - Détection doublons d'écritures exacts et probables
  - Détection montants répétés suspects (schéma fraude fictif)
- **Réconciliation Balance Générale ↔ FEC** (`balance_reconciliation`) :
  - Parse CSV/TSV (séparateur auto, encodage auto)
  - Comparaison solde par solde avec flags : ABSENT_FEC, ABSENT_BALANCE, INVERSION_DEBIT_CREDIT
  - Détecte manipulation post-clôture entre FEC et états déposés
- **Score de risque rebalancé** : `coherence_check` intégré à 20 % du score global
- **Migration Alembic 002** : colonnes `coherence_check_result` + `balance_reconciliation_result`
- **Tests unitaires** : 7 suites (benford, fec_parser, anonymizer, risk_scorer, cycle_audit, analytical_review, coherence_checker, balance_reconciliation) — 80+ assertions
- **Frontend** :
  - Pages `/auth/forgot-password` et `/auth/reset-password` (indicateur force mdp)
  - Modal analyse avec sélecteur FEC N-1 + balance générale
  - Type document `BALANCE_GENERALE` dans l'upload
  - Page résultats : 6 nouvelles cartes (bilan, résultat, doublons, réconciliation…)
- **Logs d'audit** : endpoint GET `/audit-logs/` (Chef mission+)
- **CI GitHub Actions** : matrix Python 3.11/3.12 + Node 18/20, ruff + mypy + pytest + eslint + next build

---

## [0.1.0] — 2026-05-27

### Ajouté
- Structure complète du projet (backend FastAPI + frontend Next.js)
- Parseur FEC SYSCOHADA multi-format (encodage auto-détecté, CSV/TSV)
- Vérification intrinsèque : équilibre Débit = Crédit par écriture
- Moteur Loi de Benford avec test Chi-square et score de conformité
- Détection anomalies Isolation Forest (Scikit-learn)
- Revue analytique N vs N-1 par classes SYSCOHADA 1-9
- Audit Cycle Ventes/Clients : détection anomalies cut-off
- Audit Cycle Trésorerie : flux suspects (week-end, sans libellé, montants ronds)
- Score de risque global 0-100 (VERT / ORANGE / ROUGE)
- Génération rapports Word (.docx) et Excel (.xlsx)
- Synthèse IA via Claude (Anthropic)
- Authentification JWT + TOTP MFA (QR code)
- RBAC : Associé / Chef de mission / Auditeur junior
- Chiffrement AES-256 au repos
- Logs d'audit immuables
- Multi-tenancy PostgreSQL strict
- Cache Redis (sessions, blacklist tokens)
- Docker Compose (PostgreSQL + Redis + Backend + Frontend)
- Interface utilisateur Next.js/Tailwind CSS (charte FinTech Corporate)
  - Dashboard KPIs + graphiques Recharts
  - Upload FEC drag-and-drop
  - Visualisation résultats analyse
  - Téléchargement rapports
  - Gestion équipe RBAC

---

*[0.1.0]: https://github.com/LnDevAi/analyse-etats-financiers/releases/tag/v0.1.0*

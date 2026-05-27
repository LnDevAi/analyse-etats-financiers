# Changelog — E-DÉFENCE Analyse Financière IA

Toutes les modifications notables sont documentées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/) · Versioning : [SemVer](https://semver.org/lang/fr/)

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

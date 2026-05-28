# Changelog — E-DÉFENCE Analyse Financière IA

Toutes les modifications notables sont documentées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/) · Versioning : [SemVer](https://semver.org/lang/fr/)

---

## [Unreleased] — dev

---

## [1.0.1] — 2026-05-28

### Corrigé
- **`fec_parser`** : colonnes Débit/Crédit forcées en `float` (évitait un dtype `int64` cassant les tests)
- **`fec_parser`** : `validate_partie_double` retourne un `bool` Python natif au lieu de `numpy.bool_` (incompatible avec `is True`)
- **`anonymizer`** : SIRET déplacé avant TEL dans la liste des patterns — les 14 chiffres d'un SIRET n'étaient plus masqués à tort comme numéro de téléphone
- **`anonymizer`** : NOM_PROPRE compilé sans `re.IGNORECASE` — le flag causait des faux positifs sur le texte courant en minuscules
- **`ag_document_analyzer`** : champs renommés pour respecter la spec API partenaires :
  - `comparisons` → `comparaison_par_classe`
  - `discrepancies` → `ecarts_significatifs`
  - `masse_salariale_doc` → `masse_salariale_document`
  - `marches_sample` → `marches_compares`
- **`ag_document_analyzer`** : clé `coherence_score` (0.0 – 1.0) ajoutée à chaque module AG
- **`ag_document_analyzer`** : score global corrigé — était exprimé sur une échelle 0–100, désormais 0.0–1.0 conforme à l'API
- **`ag_document_analyzer`** : gardes `None` ajoutées dans les 4 fonctions — plus de crash si un document optionnel est absent
- **`ag_document_analyzer`** : `run_marches_check` utilise le côté Crédit des comptes 40x (norme SYSCOHADA correcte : Crédit 401 = facture fournisseur reçue)
- **`ag_document_analyzer`** : l'orchestrateur `run_ag_comparative_analysis` exécute désormais toujours les 4 modules ; chaque fonction gère elle-même le cas `content=None`
- **`requirements.txt`** : contraintes `>=` au lieu de `==` pour éviter les conflits avec les packages déjà installés
- **Tests** : 163 tests unitaires, tous verts (8 suites : fec_parser, anonymizer, benford, cycle_audit, analytical_review, ag_document_analyzer, billing, risk_scorer)

---

## [1.0.0] — 2026-05-27

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
- **Tests unitaires** : 8 suites — 163 assertions (benford, fec_parser, anonymizer, risk_scorer, cycle_audit, analytical_review, coherence_checker, balance_reconciliation, ag_document_analyzer, billing)
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

*[1.0.1]: https://github.com/LnDevAi/analyse-etats-financiers/compare/v1.0.0...HEAD*
*[1.0.0]: https://github.com/LnDevAi/analyse-etats-financiers/releases/tag/v1.0.0*
*[0.1.0]: https://github.com/LnDevAi/analyse-etats-financiers/releases/tag/v0.1.0*

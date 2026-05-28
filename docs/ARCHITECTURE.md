# Architecture technique — E-DÉFENCE V4

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet / HTTPS                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Nginx (TLS)   │
                    └────┬───────┬───┘
                         │       │
              ┌──────────▼──┐ ┌──▼──────────┐
              │  Next.js 14 │ │  FastAPI     │
              │  :3000      │ │  :8000       │
              └─────────────┘ └──┬──────┬───┘
                                 │      │
                    ┌────────────▼──┐ ┌─▼──────────────┐
                    │ PostgreSQL 16 │ │   Redis 7        │
                    │ (multi-tenant)│ │ (tokens, cache)  │
                    └───────────────┘ └────────────────┘
```

---

## Multi-tenancy

Chaque organisation (cabinet, banque, administration) est un **tenant** isolé. L'isolation est assurée au niveau applicatif par un filtre systématique sur `tenant_id` dans toutes les requêtes SQL.

```python
# Exemple — toute requête filtre sur tenant_id
select(Document).where(Document.tenant_id == current_user.tenant_id)
```

**Données partagées entre tenants** : plans d'abonnement, référentiel SYSCOHADA.  
**Données strictement isolées** : utilisateurs, documents, analyses, factures, clients CRM.

---

## Sécurité

### Authentification

```
POST /api/v1/auth/login
  → Vérifie email + bcrypt hash
  → Si MFA activé → renvoie temp_token (Redis, 5 min)
  → POST /api/v1/auth/mfa/verify (TOTP 6 chiffres)
  → Retourne access_token (JWT, 30 min) + refresh_token (JWT, 7 jours)
```

- **JWT** — HS256, `jti` (JWT ID) stocké en Redis pour révocation
- **TOTP MFA** — PyOTP, QR code via `qrcode`, secret chiffré AES-256-GCM en base
- **Révocation** — blacklist Redis ; déconnexion invalide immédiatement le token

### RBAC (Rôles)

| Rôle | Niveau | Accès |
|------|--------|-------|
| `ASSOCIE` | 3 | Tout (admin, CRM, billing, configuration) |
| `CHEF_MISSION` | 2 | Analyses, documents, cross-check, rapport |
| `AUDITEUR_JUNIOR` | 1 | Lecture seule, upload, consultation analyses |

### Chiffrement des données sensibles

Les clés TOTP MFA sont chiffrées **AES-256-GCM** avant stockage :

```python
# Chiffrement
encrypted = encrypt_aes(totp_secret)   # → base64 nonce + ciphertext
# Déchiffrement
plain = decrypt_aes(encrypted)
```

### Logs d'audit immuables

Toute action sensible génère une entrée `audit_logs` horodatée, signée, non modifiable :

```
login · logout · upload · analyse_created · report_downloaded
crm_client_created · subscription_upgraded · payment_initiated
```

---

## Pipeline d'analyse FEC

```
Upload FEC (multipart)
        │
        ▼
parse_fec()          ← détection encodage (chardet) + séparateur
        │
        ▼
anonymize_fec()      ← suppression SIRET, NOM, ADRESSE (NLP regex)
        │
        ▼
Background task (FastAPI)
        │
   ┌────┴────────────────────────────────────────────────────┐
   │  Module 1  : check_intrinsic()      → Débit = Crédit    │
   │  Module 2  : run_benford()          → Chi-square        │
   │  Module 3  : run_isolation_forest() → ML anomalies      │
   │  Module 4  : run_analytical_review()→ N vs N-1          │
   │  Module 5  : run_cycle_ventes()     → cut-off           │
   │  Module 6  : run_cycle_tresorerie() → flux suspects     │
   │  Module 7  : run_coherence_check()  → SYSCOHADA         │
   │  Module 8  : run_balance_recon()    → Balance ↔ FEC     │
   └────┬────────────────────────────────────────────────────┘
        │
        ▼
compute_risk_score()  ← moyenne pondérée 8 modules
        │
        ▼
generate_ai_synthesis() ← Claude Sonnet (Anthropic)
        │
        ▼
_create_anomalies()   ← insertion en base
        │
        ▼
status = COMPLETED → notify frontend via polling
```

---

## Pipeline AG (Assemblée Générale)

```
Upload FEC + documents AG (budget CSV, bilan Excel, marchés Excel, rapport PDF)
        │
        ▼
extract_document()    ← PDF (pdfplumber) / Excel / CSV / DOCX
        │
        ▼
Background task
        │
   ┌────┴────────────────────────────────────────┐
   │  run_budget_execution_analysis()            │
   │  run_masse_salariale_check()                │
   │  run_marches_check()                        │
   │  run_activites_check()                      │
   └────┬────────────────────────────────────────┘
        │
        ▼
Score global de cohérence + interprétation IA
```

---

## Pipeline Paiement CinetPay

```
Client clique "Payer"
        │
        ▼
POST /api/v1/billing/payments/initiate
  → Crée Payment(status=PENDING) en base
  → Appel CinetPay API → retourne payment_url
        │
        ▼
Redirect client → page CinetPay (Orange Money / Wave / Moov / CB)
        │
        ▼
Client paie → CinetPay notifie :
POST /api/v1/billing/payments/webhook
  → check_payment_status(transaction_id)
  → Payment.status = COMPLETED
  → Invoice.status = PAID
  → Subscription.status = ACTIVE
```

---

## Structure de la base de données

```
tenants ──────────────────────────────────────────────────────┐
    │                                                          │
    ├── users (RBAC, MFA, tenant_id FK)                       │
    ├── documents (FEC, PDF, Excel — storage_path)            │
    ├── analyses (8 modules JSON, risk_score, anomalies)      │
    │       └── anomalies (type, severity, account, amount)   │
    ├── cross_checks (comparaison multi-entités)              │
    ├── ag_analyses (4 documents AG, coherence_score)         │
    ├── audit_logs (immuable, horodaté)                       │
    │                                                          │
    ├── crm_clients (pipeline, lifecycle, deal_value)         │
    │       ├── crm_contacts (email, phone, role)             │
    │       └── activity_logs (CALL, EMAIL, MEETING...)       │
    │                                                          │
    └── subscriptions ──────── subscription_plans             │
            └── invoices                                      │
                    └── payments (CinetPay, statut)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Gestion des fichiers

Les documents uploadés sont stockés sur disque local (ou volume Docker monté) :

```
UPLOAD_DIR/
    {tenant_id}/
        {uuid}_{original_filename}
```

Le chemin `storage_path` est enregistré en base. En production, remplacer par un stockage objet (S3/MinIO) en modifiant `document_service.py`.

---

## Polling Frontend

Les analyses longues (30–120 s) utilisent le polling HTTP côté frontend :

```typescript
useEffect(() => {
  if (analysis.status === "RUNNING") {
    const interval = setInterval(() => fetchAnalysis(), 5000);
    return () => clearInterval(interval);
  }
}, [analysis.status]);
```

Pas de WebSocket — le polling à 5 secondes est suffisant pour l'UX cible.

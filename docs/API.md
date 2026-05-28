# Référence API — E-DÉFENCE V4

Base URL : `https://api.edefence.tech/api/v1`  
Documentation interactive : `https://api.edefence.tech/api/docs` (Swagger UI)

Toutes les requêtes authentifiées requièrent l'en-tête :
```
Authorization: Bearer <access_token>
```

---

## Authentification

### POST `/auth/login`
Connexion avec email et mot de passe.

**Corps** :
```json
{ "email": "user@cabinet.bf", "password": "MotDePasse123!" }
```

**Réponse (sans MFA)** :
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "...", "role": "CHEF_MISSION" }
}
```

**Réponse (avec MFA activé)** :
```json
{ "mfa_required": true, "temp_token": "eyJ..." }
```

---

### POST `/auth/mfa/verify`
Vérification du code TOTP 6 chiffres.

```json
{ "email": "user@cabinet.bf", "totp_code": "123456", "temp_token": "eyJ..." }
```

---

### POST `/auth/forgot-password`
Envoie un email de réinitialisation. Répond toujours `200` (pas d'énumération d'emails).

```json
{ "email": "user@cabinet.bf" }
```

---

### POST `/auth/reset-password`
Réinitialise le mot de passe avec le token reçu par email.

```json
{ "token": "abc123...", "new_password": "NouveauMotDePasse!" }
```

---

### POST `/auth/logout`
Révoque le token actuel (ajout en blacklist Redis).

---

## Documents

### POST `/documents/upload`
Upload d'un document (FEC, PDF, Excel, CSV, DOCX).

```
Content-Type: multipart/form-data
Champs: file (binary), document_type (FEC | BALANCE_GENERALE | RAPPORT_AG | AUTRE)
```

**Réponse** :
```json
{
  "id": "uuid",
  "original_filename": "FEC_2024.txt",
  "document_type": "FEC",
  "file_size": 2456789,
  "created_at": "2026-05-27T10:00:00Z"
}
```

---

### GET `/documents/`
Liste les documents du tenant courant (20 derniers).

---

### DELETE `/documents/{id}`
Supprime un document (fichier + entrée base).

---

## Analyses FEC

### POST `/analyses/`
Lance une analyse complète en arrière-plan.

```json
{
  "document_id": "uuid-du-fec",
  "previous_document_id": "uuid-fec-n1",   // optionnel — FEC N-1
  "balance_document_id": "uuid-balance"    // optionnel — balance générale
}
```

**Réponse immédiate** : objet analyse avec `status: "PENDING"`.  
Interroger `GET /analyses/{id}` (polling) jusqu'à `status: "COMPLETED"`.

---

### GET `/analyses/`
Liste les analyses du tenant (20 dernières).

---

### GET `/analyses/{id}`
Détail d'une analyse avec tous les résultats modules.

**Réponse** :
```json
{
  "id": "uuid",
  "status": "COMPLETED",
  "risk_score": 72.4,
  "risk_level": "ORANGE",
  "intrinsic_check": { "valid": true, ... },
  "benford_result": { "conformity_score": 87.4, "risk_level": "VERT", ... },
  "isolation_forest_result": { "anomalies_detected": 3, ... },
  "analytical_review": { ... },
  "cycle_ventes_result": { ... },
  "cycle_tresorerie_result": { ... },
  "coherence_check_result": { ... },
  "balance_reconciliation_result": { ... },
  "ai_synthesis": "L'analyse révèle...",
  "anomalies": [...],
  "created_at": "2026-05-27T10:00:00Z"
}
```

---

### GET `/analyses/{id}/report/docx`
Télécharge le rapport Word (.docx).

### GET `/analyses/{id}/report/xlsx`
Télécharge le rapport Excel (.xlsx).

### GET `/analyses/dashboard`
Statistiques globales du tenant : nombre d'analyses, distribution des risques, tendances.

---

## Analyse AG

### POST `/ag-analyses/`
Lance une analyse comparative FEC ↔ documents AG.

```json
{
  "fec_document_id": "uuid",              // obligatoire
  "budget_document_id": "uuid",           // optionnel
  "social_document_id": "uuid",           // optionnel
  "marches_document_id": "uuid",          // optionnel
  "activites_document_id": "uuid"         // optionnel
}
```

---

### GET `/ag-analyses/`
Liste les analyses AG du tenant.

### GET `/ag-analyses/{id}`
Détail d'une analyse AG.

**Réponse** :
```json
{
  "id": "uuid",
  "status": "COMPLETED",
  "coherence_score": 0.82,
  "risk_level": "VERT",
  "budget_comparison": {
    "coherence_score": 0.91,
    "risk_level": "VERT",
    "comparaison_par_classe": { "6": { "budget_prevu": 5000000, "realise_fec": 4875000 } },
    "ecarts_significatifs": []
  },
  "masse_salariale_check": { "masse_salariale_fec": 2400000, "ecart_pct": 1.2, ... },
  "marches_check": { "marches_compares": [...] },
  "activites_check": { "montants_trouves_fec": [...] },
  "ai_synthesis": "..."
}
```

---

## Cross-Checking

### POST `/cross-checks/`
Comparaison de FEC entre plusieurs entités.

```json
{ "document_ids": ["uuid1", "uuid2", "uuid3"] }
```

### GET `/cross-checks/`
Liste les cross-checks du tenant.

### GET `/cross-checks/{id}`
Détail d'un cross-check.

---

## CRM

### GET `/crm/clients`
Liste les clients CRM.

Query params : `stage`, `lifecycle`, `search`, `limit` (max 200), `offset`.

---

### POST `/crm/clients`
Crée un nouveau client/prospect.

```json
{
  "company_name": "Mairie de Ouagadougou",
  "sector": "Collectivité",
  "city": "Ouagadougou",
  "pipeline_stage": "PROSPECT",
  "lifecycle_status": "PROSPECT",
  "deal_value": 150000,
  "source": "Démarchage"
}
```

---

### GET `/crm/clients/{id}`
Fiche client complète avec contacts.

### PATCH `/crm/clients/{id}`
Mise à jour partielle d'un client.

```json
{ "pipeline_stage": "DÉMO", "health_score": 75 }
```

### DELETE `/crm/clients/{id}`
Supprime un client et toutes ses données.

---

### GET `/crm/pipeline/stats`
Statistiques du pipeline par stade.

**Réponse** :
```json
{
  "PROSPECT": { "count": 12, "deal_value": 1800000 },
  "QUALIFIÉ": { "count": 5, "deal_value": 750000 },
  "DÉMO": { "count": 3, "deal_value": 450000 },
  "NÉGOCIATION": { "count": 2, "deal_value": 300000 },
  "GAGNÉ": { "count": 8, "deal_value": 1200000 },
  "PERDU": { "count": 4, "deal_value": 0 }
}
```

---

### POST `/crm/clients/{id}/contacts`
Ajoute un contact à un client.

```json
{
  "full_name": "Moussa Kaboré",
  "role": "Directeur Financier",
  "email": "m.kabore@mairie-ouaga.bf",
  "phone": "+226 70 00 00 00",
  "is_primary": true
}
```

### DELETE `/crm/contacts/{contact_id}`
Supprime un contact.

---

### GET `/crm/clients/{id}/activities`
Journal d'activités d'un client (100 dernières).

### POST `/crm/clients/{id}/activities`
Enregistre une interaction.

```json
{
  "activity_type": "CALL",
  "subject": "Appel de qualification",
  "body": "Intéressé par le plan Pro. Budget validé.",
  "outcome": "Positif",
  "next_action": "Envoyer offre commerciale",
  "next_action_date": "2026-06-01",
  "duration_minutes": 25
}
```

Types d'activité : `CALL` · `EMAIL` · `MEETING` · `DEMO` · `NOTE` · `RELANCE`

---

## Billing & Paiements

### GET `/billing/plans`
Liste les plans d'abonnement actifs.

**Réponse** :
```json
[
  {
    "id": "uuid",
    "name": "STARTER",
    "display_name": "Starter",
    "price_monthly": "25000.00",
    "price_yearly": "255000.00",
    "max_analyses": 10,
    "max_users": 3,
    "max_documents": 50,
    "trial_days": 14,
    "features": ["Analyses FEC complètes", "Loi de Benford", ...]
  }
]
```

---

### GET `/billing/subscription`
Abonnement actuel du tenant authentifié.

### POST `/billing/subscription`
Crée un abonnement (admin ASSOCIE uniquement).

```json
{ "plan_id": "uuid", "billing_cycle": "MONTHLY" }
```

### PATCH `/billing/subscription/upgrade`
Change de plan.

```json
{ "plan_id": "uuid-plan-pro", "billing_cycle": "YEARLY" }
```

---

### GET `/billing/invoices`
Liste les factures du tenant (50 dernières).

### GET `/billing/invoices/{id}/pdf`
Télécharge la facture au format PDF.

---

### POST `/billing/payments/initiate`
Initie un paiement CinetPay.

```json
{
  "invoice_id": "uuid",
  "payment_method": "ORANGE_MONEY",
  "return_url": "https://app.edefence.tech/account/billing",
  "notify_url": "https://api.edefence.tech/api/v1/billing/payments/webhook"
}
```

**Réponse** :
```json
{
  "payment_id": "uuid",
  "payment_url": "https://checkout.cinetpay.com/payment?token=...",
  "transaction_id": "TXN20260527ABC123"
}
```

Méthodes de paiement : `ORANGE_MONEY` · `WAVE` · `MOOV_MONEY` · `CARD` · `BANK_TRANSFER`

---

### POST `/billing/payments/webhook`
Webhook CinetPay (usage interne, appelé par CinetPay uniquement).

### GET `/billing/payments`
Historique des paiements du tenant.

---

### GET `/billing/dashboard`
Dashboard financier (ASSOCIE uniquement).

**Réponse** :
```json
{
  "mrr": 375000,
  "arr": 4500000,
  "active_subscriptions": 5,
  "trial_subscriptions": 2,
  "overdue_invoices": 1,
  "overdue_amount": 75000,
  "revenue_by_month": [
    { "month": "Avr 2026", "revenue": 300000, "invoices_count": 4, "paid_count": 4 }
  ],
  "subscriptions_by_plan": { "Starter": 2, "Pro": 3 }
}
```

---

## Codes d'erreur

| Code HTTP | Signification |
|-----------|--------------|
| `400` | Requête invalide (champ manquant, format incorrect) |
| `401` | Token absent, invalide ou révoqué |
| `403` | Rôle insuffisant pour cette action |
| `404` | Ressource introuvable (ou non autorisée pour ce tenant) |
| `422` | Erreur de validation Pydantic |
| `500` | Erreur interne serveur |
| `502` | Erreur communication service tiers (CinetPay, Anthropic) |

**Format d'erreur standard** :
```json
{ "detail": "Message d'erreur explicite" }
```

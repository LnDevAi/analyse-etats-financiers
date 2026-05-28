# CRM & Facturation — Guide technique

## Module CRM

### Cycle de vie d'un client

```
PROSPECT → QUALIFIÉ → DÉMO → NÉGOCIATION → GAGNÉ
                                         ↘ PERDU
```

Indépendamment du stade pipeline, chaque client a un statut de cycle de vie :

```
PROSPECT → TRIAL → ACTIF → SUSPENDU → CHURNED
```

### Score de santé (health_score)

Score manuel de 0 à 100 indiquant la qualité de la relation client :

| Score | Interprétation |
|-------|---------------|
| 80–100 | Client satisfait, renouvellement probable |
| 50–79 | Relation correcte, à surveiller |
| 0–49 | Risque de churn, action commerciale requise |

### Types d'activités

| Type | Usage |
|------|-------|
| `CALL` | Appel téléphonique |
| `EMAIL` | Échange email |
| `MEETING` | Réunion physique ou visio |
| `DEMO` | Démonstration produit |
| `NOTE` | Note interne libre |
| `RELANCE` | Relance commerciale ou de paiement |

---

## Module Paiements

### Plans d'abonnement

| Plan | Prix/mois | Analyses | Utilisateurs | Documents |
|------|-----------|----------|--------------|-----------|
| Starter | 25 000 FCFA | 10 | 3 | 50 |
| Pro | 75 000 FCFA | 50 | 10 | 500 |
| Enterprise | Sur devis | Illimité | Illimité | Illimité |

Remise annuelle : −15% sur le tarif mensuel × 12.

### Cycle de facturation

```
Abonnement créé (TRIAL)
    │ 14 ou 30 jours
    ▼
Facture générée automatiquement
    │ CinetPay initié par le client
    ▼
Webhook CinetPay → Payment COMPLETED
    ▼
Invoice.status = PAID → Subscription.status = ACTIVE
    │ 30 ou 365 jours plus tard
    ▼
Nouvelle facture → cycle recommence
```

### Statuts des factures

| Statut | Description |
|--------|-------------|
| `DRAFT` | Créée, pas encore envoyée |
| `SENT` | Envoyée au client par email |
| `PAID` | Paiement confirmé |
| `OVERDUE` | Échéance dépassée |
| `CANCELLED` | Annulée |
| `REFUNDED` | Remboursée |

### Statuts des paiements

| Statut | Description |
|--------|-------------|
| `PENDING` | Initié, en attente confirmation CinetPay |
| `COMPLETED` | Paiement confirmé par webhook |
| `FAILED` | Refusé par l'opérateur |
| `CANCELLED` | Annulé par le client |
| `REFUNDED` | Remboursé |

### Intégration CinetPay

**Mode sandbox** (tests) :
```env
CINETPAY_API_KEY=<clé sandbox>
CINETPAY_SITE_ID=<site ID sandbox>
```

**Workflow de test** :
1. Initier un paiement via `POST /billing/payments/initiate`
2. Ouvrir `payment_url` retourné dans un navigateur
3. Utiliser les numéros de test CinetPay (voir [docs CinetPay](https://docs.cinetpay.com))
4. Vérifier que le webhook est reçu sur `POST /billing/payments/webhook`
5. Vérifier `Invoice.status = PAID` en base

**Numéros de test Orange Money (sandbox)** :
- `+22670000001` → paiement accepté
- `+22670000002` → paiement refusé

### TVA UEMOA

Taux standard : **18%**

```
Montant HT + TVA 18% = Total TTC
Exemple : 63 559 FCFA HT + 11 441 FCFA TVA = 75 000 FCFA TTC
```

La facture PDF mentionne :
- Raison sociale E-DÉFENCE + RCCM + IFU
- Raison sociale client + NIF/IFU
- Détail HT + TVA 18% + TTC
- Période de facturation
- Mentions légales UEMOA obligatoires

### Initialisation des plans

À exécuter une seule fois après la migration 005 :

```bash
python -m app.services.seed_plans
```

Pour personnaliser les plans (prix, quotas), modifier directement `seed_plans.py` puis relancer. Les plans existants ne sont pas écrasés (idempotent).

Pour modifier un plan existant via SQL :
```sql
UPDATE subscription_plans
SET price_monthly = 30000, max_analyses = 15
WHERE name = 'STARTER';
```

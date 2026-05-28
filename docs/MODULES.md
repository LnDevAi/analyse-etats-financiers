# Modules d'analyse — E-DÉFENCE V4

## Module 1 — Vérification Intrinsèque (20%)

**Objectif** : S'assurer que chaque écriture du FEC respecte l'équilibre Débit = Crédit.

**Algorithme** :
1. Groupement des écritures par `EcritureNum`
2. Pour chaque groupe : `|sum(Débit) - sum(Crédit)| < 0.01`
3. Comptage des écritures déséquilibrées

**Résultat** :
```json
{
  "valid": true,
  "total_debit": 125000000,
  "total_credit": 125000000,
  "difference": 0,
  "unbalanced_entries_count": 0,
  "risk_level": "VERT"
}
```

**Niveaux de risque** :
- VERT : 0 écriture déséquilibrée
- ORANGE : 1–5 écritures déséquilibrées
- ROUGE : > 5 écritures déséquilibrées

---

## Module 2 — Loi de Benford (17%)

**Objectif** : Détecter des manipulations de montants par test statistique sur la distribution des premiers chiffres significatifs.

**Algorithme** :
1. Extraction du premier chiffre de chaque montant (Débit + Crédit non nul)
2. Calcul de la distribution observée vs distribution théorique de Benford
   - Digit 1 attendu : 30,1% ; Digit 2 : 17,6% ; ... Digit 9 : 4,6%
3. Test Chi-square avec ddl=8
4. Score de conformité = 100 - Σ|observé - attendu| / 2 * 100

**Résultat** :
```json
{
  "sufficient_data": true,
  "conformity_score": 87.4,
  "p_value": 0.123,
  "chi_square": 12.4,
  "risk_level": "VERT",
  "distribution": {
    "1": {"expected_pct": 30.1, "observed_pct": 29.8},
    ...
  }
}
```

**Niveaux de risque** :
- VERT : conformité ≥ 80% et p-value ≥ 0,05
- ORANGE : conformité 60–80% ou p-value 0,01–0,05
- ROUGE : conformité < 60% ou p-value < 0,01

> ⚠️ Requiert au moins 50 écritures pour être significatif.

---

## Module 3 — Isolation Forest ML (15%)

**Objectif** : Détecter les écritures statistiquement anormales par apprentissage non supervisé.

**Features utilisées** :
- Montant (Débit - Crédit)
- Jour de la semaine de l'écriture
- Numérique du compte (préfixe 2-4 chiffres)

**Algorithme** :
1. Entraînement Isolation Forest (Scikit-learn, contamination=0,05)
2. Prédiction : score d'anomalie [-1;+1] pour chaque écriture
3. Écritures avec score < -0,1 → anomalies candidates
4. Tri par score décroissant, top-20 retournés

**Résultat** :
```json
{
  "anomalies_detected": 7,
  "anomaly_rate_pct": 1.4,
  "risk_level": "ORANGE",
  "top_anomalies": [
    {"account": "521000", "label": "...", "amount": 4875000, "date": "2024-03-15", "score": -0.45}
  ]
}
```

**Niveaux de risque** :
- VERT : taux < 2%
- ORANGE : taux 2–5%
- ROUGE : taux > 5%

---

## Module 4 — Revue Analytique N vs N-1 (12%)

**Objectif** : Identifier les variations inhabituelles de soldes entre l'exercice N et l'exercice précédent N-1.

**Algorithme** :
1. Calcul du solde net par compte pour chaque exercice : `sum(Débit) - sum(Crédit)`
2. Pour chaque compte présent dans les deux exercices :
   - Variation absolue et en pourcentage
   - Déviation significative si |variation%| > seuil (défaut 25%)
3. Comptes nouveaux (présents uniquement en N) → signalés séparément

**Résultat** :
```json
{
  "risk_level": "ORANGE",
  "comparison_n_vs_n1": {
    "threshold_pct": 25,
    "deviations_count": 4,
    "deviations": [
      {"account": "601000", "solde_n": 12500000, "solde_n1": 8200000, "variation_pct": 52.4, "severity": "ROUGE"}
    ]
  },
  "new_accounts_n": ["603000", "625000"]
}
```

---

## Module 5 — Cycle Ventes/Clients (8%)

**Objectif** : Détecter les anomalies de cut-off (écritures de produits à cheval sur deux exercices).

**Algorithme** :
1. Filtrage des comptes de classe 7 (produits)
2. Détection des écritures dans les 15 derniers jours de l'exercice
3. Analyse de la concentration : si > 10% des produits annuels dans les 15 derniers jours → suspect
4. Ventilation mensuelle des produits

**Résultat** :
```json
{
  "risk_level": "VERT",
  "fiscal_year": 2024,
  "total_revenue_class7": 45000000,
  "cutoff_amount": 1250000,
  "cutoff_rate_pct": 2.8,
  "monthly_breakdown": {"01": 3200000, "02": 3800000, ...}
}
```

---

## Module 6 — Cycle Trésorerie (8%)

**Objectif** : Détecter les mouvements de trésorerie suspects.

**Indicateurs analysés** :

| Indicateur | Logique | Seuil ROUGE |
|-----------|---------|-------------|
| Écritures week-end | Mouvements samedi/dimanche sur comptes 51x | > 5% du total |
| Sans libellé | `EcritureLib` vide ou générique | > 10% du total |
| Montants ronds | Multiples de 100 000 FCFA | > 15% du total |

**Résultat** :
```json
{
  "risk_level": "ORANGE",
  "breakdown": {
    "weekend": 12,
    "sans_libelle": 8,
    "montants_ronds": 45
  },
  "total_tresorerie_entries": 312
}
```

---

## Module 7 — Cohérence SYSCOHADA (20%)

**Objectif** : Valider la cohérence des états financiers selon les normes SYSCOHADA UEMOA.

### Sous-module 7a — Soldes normaux

Chaque classe de comptes SYSCOHADA a un sens de solde normal :

| Comptes | Solde normal attendu |
|---------|---------------------|
| 10, 11, 14–19, 28, 29, 40, 42, 43, 7x | Créditeur |
| 2x, 3x, 41x, 51–57, 6x | Débiteur |
| 12, 13, 44–48, 8x, 9x | Non vérifié (mixte) |

Un compte avec un solde de signe inverse est signalé comme anomalie.

### Sous-module 7b — Cohérence du résultat net

```
Résultat FEC = Σ Classe 7 (Crédit - Débit) - Σ Classe 6 (Débit - Crédit)
Résultat enregistré = solde compte 13x
Écart acceptable : < 1%
```

### Sous-module 7c — Équilibre du bilan

```
Actif  = Σ soldes débiteurs classes 1–5 (comptes Débit normal)
Passif = Σ soldes créditeurs classes 1–5 (comptes Crédit normal)
Déséquilibre acceptable : < 5%
```

### Sous-module 7d — Doublons d'écritures

- **Doublons exacts** : même date, même compte, même montant, même libellé
- **Doublons probables** : même date, même compte, même montant (libellé différent)

---

## Module 8 — Réconciliation Balance Générale ↔ FEC (bonus)

**Objectif** : Vérifier que la balance générale fournie correspond exactement aux soldes calculés depuis le FEC.

**Types d'écarts détectés** :

| Flag | Description |
|------|-------------|
| `ABSENT_FEC` | Compte présent dans la balance mais absent du FEC |
| `ABSENT_BALANCE` | Compte présent dans le FEC mais absent de la balance |
| `INVERSION_DEBIT_CREDIT` | Débit et crédit sont inversés |
| `ECART_DEBIT_UNIQUEMENT` | Écart sur le débit uniquement |
| `ECART_CREDIT_UNIQUEMENT` | Écart sur le crédit uniquement |
| `ECART_SOLDE` | Écart sur le solde net (> tolérance 0,1%) |

---

## Calcul du Score de Risque Global

```python
WEIGHTS = {
    "intrinsic_check":    0.20,
    "coherence_check":    0.20,
    "benford":            0.17,
    "isolation_forest":   0.15,
    "analytical_review":  0.12,
    "cycle_ventes":       0.08,
    "cycle_tresorerie":   0.08,
}

MODULE_SCORES = {"VERT": 100, "ORANGE": 50, "ROUGE": 0}

score = Σ (weight × MODULE_SCORES[module.risk_level])
```

| Score global | Niveau | Interprétation |
|-------------|--------|---------------|
| 75–100 | 🟢 VERT | Aucune anomalie significative détectée |
| 45–74 | 🟠 ORANGE | Anomalies modérées, investigation recommandée |
| 0–44 | 🔴 ROUGE | Anomalies graves, diligences approfondies requises |

---

## Synthèse IA (Claude Sonnet)

Après l'exécution des 7–8 modules, un prompt structuré est envoyé à Claude Anthropic avec :
- Le score de risque global et par module
- Les 5 anomalies les plus sévères
- Le secteur d'activité et l'exercice fiscal
- La norme SYSCOHADA applicable

Claude génère une note de synthèse de 200–400 mots, structurée en :
1. Évaluation générale
2. Points de vigilance prioritaires
3. Recommandations de diligences

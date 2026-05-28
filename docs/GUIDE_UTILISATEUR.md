# Guide Utilisateur — E-DÉFENCE V4

## Bienvenue sur E-DÉFENCE

E-DÉFENCE est une plateforme d'analyse automatisée des états financiers. Elle vous permet d'analyser un Fichier des Écritures Comptables (FEC) en quelques minutes et d'obtenir un rapport d'audit structuré, conforme aux normes **SYSCOHADA UEMOA**.

---

## 1. Première connexion

### Accéder à la plateforme

Ouvrir votre navigateur et accéder à : **https://app.edefence.tech**

> Compatible : Chrome 100+, Firefox 100+, Edge 100+, Safari 15+

### Se connecter

1. Saisir votre **adresse email** et votre **mot de passe**
2. Si votre compte a l'authentification à deux facteurs (MFA) activée, ouvrez votre application d'authentification (Google Authenticator, Authy...) et saisissez le code à 6 chiffres

### Mot de passe oublié

1. Cliquer sur **"Mot de passe oublié"** sur la page de connexion
2. Saisir votre adresse email
3. Consulter votre boîte mail et cliquer sur le lien reçu (valable 30 minutes)
4. Définir un nouveau mot de passe (8 caractères minimum, majuscule, chiffre)

---

## 2. Tableau de bord

Le tableau de bord affiche :
- **Nombre d'analyses réalisées** ce mois
- **Distribution des risques** (VERT / ORANGE / ROUGE) sous forme de graphique
- **Dernières analyses** avec accès rapide aux rapports
- **Quota utilisé** par rapport à votre plan d'abonnement

---

## 3. Analyser un FEC

### Qu'est-ce qu'un FEC ?

Le **Fichier des Écritures Comptables** est un export standardisé de votre logiciel de comptabilité contenant toutes les écritures de l'exercice. Il doit respecter le format SYSCOHADA (colonnes : JournalCode, EcritureDate, CompteNum, CompteLib, Debit, Credit, EcritureLib, etc.).

### Préparer votre FEC

Votre FEC doit être exporté depuis votre logiciel de comptabilité :
- **Sage** : Fichier → Exporter → FEC
- **EBP** : Gestion → Export FEC
- **Ciel** : Outils → Export FEC légal
- Formats acceptés : `.txt`, `.csv` (séparateur tabulation, pipe `|` ou point-virgule)
- Encodage : UTF-8, ISO-8859-1, Latin-1 (détection automatique)
- Taille maximale : 50 Mo

### Étapes d'analyse

**Étape 1 — Uploader le FEC**

1. Cliquer sur **"Documents"** dans le menu
2. Cliquer sur **"Uploader un document"**
3. Sélectionner votre fichier FEC
4. Type de document : choisir **"FEC"**
5. Cliquer sur **"Uploader"**

**Étape 2 — Lancer l'analyse**

1. Dans la liste des documents, cliquer sur l'icône **"Analyser"** à côté de votre FEC
2. Options disponibles :
   - **FEC N-1** (optionnel) : sélectionner le FEC de l'exercice précédent pour la revue analytique comparative
   - **Balance générale** (optionnel) : uploader la balance pour la réconciliation
3. Cliquer sur **"Lancer l'analyse"**

**Étape 3 — Attendre les résultats**

L'analyse dure entre 30 secondes et 3 minutes selon la taille du FEC. La page se met à jour automatiquement.

> ✅ Vous recevez une notification quand l'analyse est terminée.

---

## 4. Lire le rapport d'analyse

### Score de confiance global

Le score global va de **0 à 100** :

| Score | Niveau | Que faire ? |
|-------|--------|-------------|
| 75 – 100 | 🟢 **VERT** | Aucune anomalie significative. Le FEC est cohérent. |
| 45 – 74 | 🟠 **ORANGE** | Des anomalies modérées ont été détectées. Une investigation ciblée est recommandée. |
| 0 – 44 | 🔴 **ROUGE** | Des anomalies graves ont été détectées. Des diligences approfondies sont requises. |

### Les modules d'analyse

Chaque module affiche son propre niveau de risque (VERT / ORANGE / ROUGE) :

**Vérification intrinsèque**  
Vérifie que chaque écriture est équilibrée (Débit = Crédit). Un déséquilibre indique une erreur de saisie ou une manipulation.

**Loi de Benford**  
Teste si la distribution des premiers chiffres des montants suit la loi naturelle de Benford. Une déviation significative peut indiquer des montants fabriqués.

**Anomalies ML (Isolation Forest)**  
Détecte automatiquement les écritures statistiquement anormales par rapport au reste du FEC. La liste des anomalies les plus suspectes est affichée.

**Revue analytique N vs N-1** *(si FEC N-1 fourni)*  
Compare les soldes par compte entre les deux exercices. Les variations supérieures à 25% sont signalées.

**Cycle Ventes**  
Analyse les produits (classe 7) en fin d'exercice pour détecter des décalages de cut-off.

**Cycle Trésorerie**  
Examine les mouvements de trésorerie suspects : écritures le week-end, sans libellé, montants ronds répétés.

**Cohérence SYSCOHADA**  
Vérifie que les soldes de chaque compte respectent les normes SYSCOHADA : soldes normaux, cohérence du résultat net (Cl.7 - Cl.6 vs compte 13x), équilibre Actif = Passif, doublons d'écritures.

**Réconciliation Balance ↔ FEC** *(si balance fournie)*  
Compare les soldes de la balance générale avec les soldes calculés depuis le FEC et identifie les écarts.

### Note de synthèse IA

En bas du rapport, une note rédigée par l'IA (Claude Anthropic) résume les conclusions et propose des recommandations de diligences adaptées au secteur et à l'exercice.

### Graphique des scores par module

Un graphique horizontal affiche le score de chaque module, permettant d'identifier rapidement les zones de risque prioritaires.

---

## 5. Télécharger les rapports

Depuis la page d'une analyse terminée :

- **Rapport Word (.docx)** — rapport complet formaté, prêt pour partage client
- **Rapport Excel (.xlsx)** — tableaux détaillés par module, anomalies listées

> Les rapports sont générés à la demande et disponibles immédiatement.

---

## 6. Analyse AG (Assemblée Générale)

Cette fonctionnalité permet de comparer le FEC avec les documents soumis en Assemblée Générale.

### Documents acceptés

| Document | Formats |
|----------|---------|
| Rapport d'exécution budgétaire | CSV, Excel (.xlsx, .xls) |
| Bilan social | CSV, Excel |
| Plan de passation des marchés | CSV, Excel |
| Rapport d'activités | PDF, Word (.docx), CSV |

### Comment lancer une analyse AG

1. Cliquer sur **"Analyse AG"** dans le menu
2. Cliquer sur **"Nouvelle analyse"**
3. Sélectionner votre FEC (obligatoire)
4. Sélectionner les documents AG disponibles (au moins un)
5. Cliquer sur **"Lancer l'analyse"**

### Lire les résultats AG

Les résultats sont organisés en 4 onglets :

**Budget** — Graphique comparant le budget prévu, le réalisé selon le document et le réalisé selon le FEC, par classe SYSCOHADA.

**Bilan social** — Comparaison de la masse salariale entre le bilan social et les comptes 66x du FEC.

**Marchés** — Comparaison des montants des marchés avec les paiements enregistrés dans le FEC (comptes 40x).

**Activités** — Corrélation entre les montants mentionnés dans le rapport d'activités et les écritures du FEC.

---

## 7. Cross-Checking multi-entités

Le cross-checking permet de comparer plusieurs FEC d'entités différentes (filiales d'un groupe, entités liées).

1. Cliquer sur **"Cross-Checking"** dans le menu
2. Sélectionner 2 à 5 FEC à comparer
3. Lancer l'analyse
4. Le rapport identifie les comptes inter-entités incohérents et les transactions croisées suspectes

---

## 8. Gérer les documents

### Types de documents

| Type | Description |
|------|-------------|
| `FEC` | Fichier des Écritures Comptables |
| `BALANCE_GENERALE` | Balance générale pour réconciliation |
| `RAPPORT_AG` | Documents d'Assemblée Générale |
| `AUTRE` | Tout autre document |

### Supprimer un document

Cliquer sur l'icône corbeille dans la liste des documents. Attention : la suppression est irréversible et annule les analyses associées.

---

## 9. Mon compte & Abonnement

### Voir mon abonnement

Cliquer sur **"Mon abonnement"** (bas du menu) pour consulter :
- Votre plan actuel et ses limites
- Le nombre d'analyses utilisées sur la période
- La date de prochain renouvellement
- L'historique de vos factures

### Changer de plan

1. Dans **"Mon abonnement"**, consulter les plans disponibles
2. Cliquer sur **"Choisir ce plan"** pour upgrader
3. La modification est effective immédiatement

### Payer une facture

1. Dans **"Mon abonnement"**, section **"Historique des factures"**
2. Cliquer sur **"Payer"** à côté de la facture à régler
3. Choisir votre mode de paiement :
   - 🟠 Orange Money
   - 🔵 Wave
   - 🟣 Moov Money
   - 💳 Carte bancaire Visa/Mastercard
4. Cliquer sur **"Payer maintenant"** → vous êtes redirigé vers la page de paiement sécurisée CinetPay
5. Suivre les instructions de votre opérateur (code OTP par SMS)

### Télécharger une facture PDF

Cliquer sur l'icône téléchargement ↓ à côté de chaque facture.

---

## 10. Résolution des problèmes courants

**Mon analyse est bloquée en "En cours" depuis longtemps**  
Attendre 5 minutes. Si l'état reste "En cours", recharger la page. Si l'analyse passe en "Échouée", vérifier que votre FEC est au bon format et relancer.

**Mon FEC n'est pas reconnu**  
Vérifier que le fichier contient bien les colonnes obligatoires : `JournalCode`, `EcritureDate`, `CompteNum`, `Debit`, `Credit`. Exporter à nouveau depuis votre logiciel de comptabilité.

**Je ne reçois pas l'email de réinitialisation**  
Vérifier vos spams. L'email est envoyé depuis `noreply@edefence.tech`. Si toujours absent après 5 minutes, contacter votre administrateur.

**Le paiement CinetPay échoue**  
Vérifier que votre compte mobile money dispose du solde suffisant. Pour Orange Money, vérifier que vous avez activé le service en composant #150*4#. Contacter le support si le problème persiste.

---

## Support

- **Email** : support@edefence.tech
- **Téléphone** : +226 XX XX XX XX
- **Heures d'ouverture** : Lundi–Vendredi, 8h–18h (GMT)

# Politique de sécurité — E-DÉFENCE Analyse Financière IA

## Signalement d'une vulnérabilité

**NE PAS** ouvrir d'issue publique pour signaler une faille de sécurité.

Envoyer un email à : **lassane.nacoulma@edefence.tech**

Inclure :
- Description de la vulnérabilité
- Étapes pour la reproduire
- Impact potentiel estimé
- Votre contact pour le suivi

Délai de réponse : 48h ouvrées.

## Mesures de sécurité en place

- Authentification JWT + TOTP MFA obligatoire
- Chiffrement AES-256 des données au repos
- Transport TLS 1.3 uniquement
- Multi-tenancy avec isolation stricte PostgreSQL
- RBAC granulaire (Associé / Chef de mission / Auditeur junior)
- Logs d'audit immuables (INSERT only)
- Analyse SAST automatique sur chaque PR
- Dépendances auditées via Dependabot

## Données traitées

Cette plateforme traite des données financières confidentielles (FEC, liasses fiscales).
Toute contribution doit respecter les exigences de confidentialité décrites dans le CDCD V4.

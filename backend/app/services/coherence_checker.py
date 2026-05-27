"""
Contrôle de cohérence des états financiers SYSCOHADA.

Vérifications effectuées :
1. Soldes normaux SYSCOHADA (signe attendu par classe/préfixe de compte)
2. Cohérence du résultat : (Cl.7 − Cl.6) vs compte 13x
3. Équilibre approximatif Actif / Passif depuis le FEC
4. Doublons d'écritures (même EcritureNum + même CompteNum + même montant)
5. Montants répétés de façon suspecte (même montant ≥ N fois, compte différent)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


# Préfixes dont le solde NET ATTENDU est créditeur (total_crédit > total_débit → solde_net < 0)
# Solde net = total_débit − total_crédit
CREDIT_NORMAL = {
    "10", "11", "14", "15", "16", "17", "18", "19",  # Classe 1 (passif durable)
    "28", "29",  # Amortissements et provisions actif immobilisé
    "39",        # Provisions stocks
    "40",        # Fournisseurs
    "42",        # Personnel (dettes)
    "43",        # Organismes sociaux
    "49",        # Provisions clients
    "59",        # Provisions trésorerie
    "7",         # Classe 7 Produits (solde net négatif = plus de crédits que de débits)
}

# Préfixes dont le solde NET ATTENDU est débiteur (total_débit > total_crédit → solde_net > 0)
DEBIT_NORMAL = {
    "2",         # Actif immobilisé brut (hors 28x, 29x)
    "3",         # Stocks (hors 39x)
    "41",        # Clients
    "51", "52", "53", "57",  # Trésorerie active
    "6",         # Classe 6 Charges
}

# Préfixes ambigus / mixtes → pas de contrôle de signe
SKIP_PREFIXES = {"12", "13", "44", "45", "46", "47", "48", "58", "8", "9"}


def _get_expected_sign(compte_num: str) -> Optional[str]:
    """
    Retourne 'credit' | 'debit' | None selon le préfixe SYSCOHADA.
    La correspondance est testée du plus spécifique au plus général.
    """
    for length in (3, 2, 1):
        prefix = compte_num[:length]
        if prefix in SKIP_PREFIXES:
            return None
        if prefix in CREDIT_NORMAL:
            return "credit"
        if prefix in DEBIT_NORMAL:
            return "debit"
    return None


def check_soldes_normaux(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Vérifie que chaque compte a un solde du signe attendu par SYSCOHADA.
    Un compte 701 avec un solde débiteur (trop de débits) est anormal.
    """
    if "CompteNum" not in df.columns:
        return {"error": "Colonne CompteNum absente"}

    grouped = df.groupby("CompteNum").agg(
        total_debit=("Debit", "sum"),
        total_credit=("Credit", "sum"),
    ).reset_index()
    grouped["solde_net"] = grouped["total_debit"] - grouped["total_credit"]

    anomalies = []
    for _, row in grouped.iterrows():
        compte = str(row["CompteNum"])
        solde = float(row["solde_net"])
        expected = _get_expected_sign(compte)

        if expected is None:
            continue

        if expected == "credit" and solde > 0.01:
            anomalies.append({
                "account": compte,
                "expected_sign": "créditeur",
                "actual_solde_net": round(solde, 2),
                "total_debit": round(float(row["total_debit"]), 2),
                "total_credit": round(float(row["total_credit"]), 2),
                "severity": "ROUGE" if abs(solde) > 1_000_000 else "ORANGE",
                "description": f"Compte {compte} créditeur normal — solde débiteur de {solde:,.0f}",
            })
        elif expected == "debit" and solde < -0.01:
            anomalies.append({
                "account": compte,
                "expected_sign": "débiteur",
                "actual_solde_net": round(solde, 2),
                "total_debit": round(float(row["total_debit"]), 2),
                "total_credit": round(float(row["total_credit"]), 2),
                "severity": "ROUGE" if abs(solde) > 1_000_000 else "ORANGE",
                "description": f"Compte {compte} débiteur normal — solde créditeur de {abs(solde):,.0f}",
            })

    anomalies.sort(key=lambda x: -abs(x["actual_solde_net"]))

    rouge_count = sum(1 for a in anomalies if a["severity"] == "ROUGE")
    risk_level = "VERT"
    if rouge_count > 0:
        risk_level = "ROUGE"
    elif len(anomalies) > 2:
        risk_level = "ORANGE"

    return {
        "accounts_checked": len(grouped),
        "anomalies_count": len(anomalies),
        "anomalies": anomalies[:30],
        "risk_level": risk_level,
        "interpretation": (
            f"{len(anomalies)} compte(s) avec un solde de signe anormal selon SYSCOHADA."
            if anomalies else
            "Tous les soldes ont le signe attendu par le plan comptable SYSCOHADA."
        ),
    }


def check_resultat_coherence(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Cohérence du résultat net :
    Résultat FEC = Σ(Cl.7 Crédit − Cl.7 Débit) − Σ(Cl.6 Débit − Cl.6 Crédit)
    Résultat enregistré = solde créditeur des comptes 13x

    Les deux doivent se rapprocher si les écritures de clôture sont présentes.
    """
    if "CompteNum" not in df.columns:
        return {"error": "Colonne CompteNum absente"}

    grouped = df.groupby("CompteNum").agg(
        total_debit=("Debit", "sum"),
        total_credit=("Credit", "sum"),
    ).reset_index()

    cl7 = grouped[grouped["CompteNum"].str.startswith("7")]
    cl6 = grouped[grouped["CompteNum"].str.startswith("6")]
    cl13 = grouped[grouped["CompteNum"].str.startswith("13")]

    produits = float((cl7["total_credit"] - cl7["total_debit"]).sum())
    charges = float((cl6["total_debit"] - cl6["total_credit"]).sum())
    resultat_fec = round(produits - charges, 2)

    # Compte 13x : résultat enregistré (crédit − débit)
    resultat_enregistre = round(
        float((cl13["total_credit"] - cl13["total_debit"]).sum()), 2
    )

    has_closing = not cl13.empty and abs(resultat_enregistre) > 0.01
    ecart = round(abs(resultat_fec - resultat_enregistre), 2)

    risk_level = "VERT"
    coherent = True
    interpretation = ""

    if not has_closing:
        interpretation = (
            f"Résultat calculé depuis le FEC : {resultat_fec:,.0f} FCFA. "
            "Aucune écriture de clôture (compte 13x vide) — l'exercice n'est pas clôturé "
            "ou les écritures d'inventaire sont absentes."
        )
        risk_level = "ORANGE"
    elif ecart > 100:
        coherent = False
        risk_level = "ROUGE" if ecart > 10_000 else "ORANGE"
        interpretation = (
            f"INCOHÉRENCE : Résultat FEC = {resultat_fec:,.0f} vs "
            f"Compte 13x = {resultat_enregistre:,.0f} — écart de {ecart:,.0f} FCFA."
        )
    else:
        interpretation = (
            f"Résultat cohérent : {resultat_fec:,.0f} FCFA. "
            "Le compte 13x confirme le résultat issu des comptes de charges et produits."
        )

    return {
        "produits_cl7": round(produits, 2),
        "charges_cl6": round(charges, 2),
        "resultat_fec": resultat_fec,
        "resultat_enregistre_13x": resultat_enregistre,
        "has_closing_entries": has_closing,
        "ecart": ecart,
        "coherent": coherent,
        "risk_level": risk_level,
        "interpretation": interpretation,
    }


def check_equilibre_bilan(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Vérifie l'équilibre approximatif Actif = Passif depuis le FEC.

    Actif = Σ(solde débiteur des comptes Cl.2, Cl.3, Cl.41x, Cl.51-57)
    Passif = Σ(solde créditeur des comptes Cl.1, Cl.40x, Cl.42x, Cl.43x, Cl.49x)
    Résultat contribue au Passif via les comptes d'attente ou est calculé séparément.

    Note : un FEC non clôturé aura Cl.6/Cl.7 ouverts — l'équilibre tient via la partie double.
    """
    if "CompteNum" not in df.columns:
        return {"error": "Colonne CompteNum absente"}

    grouped = df.groupby("CompteNum").agg(
        total_debit=("Debit", "sum"),
        total_credit=("Credit", "sum"),
    ).reset_index()
    grouped["solde_net"] = grouped["total_debit"] - grouped["total_credit"]

    def sum_debit_balances(prefix_list):
        mask = grouped["CompteNum"].apply(
            lambda c: any(c.startswith(p) for p in prefix_list)
        )
        return float(grouped.loc[mask, "solde_net"].clip(lower=0).sum())

    def sum_credit_balances(prefix_list):
        mask = grouped["CompteNum"].apply(
            lambda c: any(c.startswith(p) for p in prefix_list)
        )
        return float((-grouped.loc[mask, "solde_net"]).clip(lower=0).sum())

    # Actif : immobilisations nettes + stocks + créances clients + trésorerie active
    actif_immob = sum_debit_balances(["2"]) - sum_credit_balances(["28", "29"])
    actif_stocks = sum_debit_balances(["3"]) - sum_credit_balances(["39"])
    actif_clients = sum_debit_balances(["41"])
    actif_tresorerie = sum_debit_balances(["51", "52", "53", "57"])
    total_actif = round(actif_immob + actif_stocks + actif_clients + actif_tresorerie, 2)

    # Passif : capitaux permanents + dettes fournisseurs + dettes sociales + provisions
    passif_capitaux = sum_credit_balances(["10", "11", "14", "15", "16", "17", "18", "19"])
    passif_fournisseurs = sum_credit_balances(["40"])
    passif_social = sum_credit_balances(["42", "43"])
    passif_provisions = sum_credit_balances(["49", "59"])
    # Résultat en cours (non clôturé) : produits - charges
    cl7 = grouped[grouped["CompteNum"].str.startswith("7")]
    cl6 = grouped[grouped["CompteNum"].str.startswith("6")]
    resultat_fec = float((cl7["total_credit"] - cl7["total_debit"]).sum()) - \
                   float((cl6["total_debit"] - cl6["total_credit"]).sum())
    # Compte 13x déjà enregistré
    cl13_balance = sum_credit_balances(["13"])

    total_passif = round(
        passif_capitaux + passif_fournisseurs + passif_social + passif_provisions
        + cl13_balance + max(0, resultat_fec),
        2
    )

    ecart = round(abs(total_actif - total_passif), 2)
    ecart_pct = round(ecart / max(total_actif, 1) * 100, 2)

    risk_level = "VERT"
    if ecart_pct > 5:
        risk_level = "ROUGE"
    elif ecart_pct > 1:
        risk_level = "ORANGE"

    return {
        "total_actif": total_actif,
        "detail_actif": {
            "immobilisations_nettes": round(actif_immob, 2),
            "stocks_nets": round(actif_stocks, 2),
            "creances_clients": round(actif_clients, 2),
            "tresorerie_active": round(actif_tresorerie, 2),
        },
        "total_passif": total_passif,
        "detail_passif": {
            "capitaux_permanents": round(passif_capitaux, 2),
            "dettes_fournisseurs": round(passif_fournisseurs, 2),
            "dettes_sociales": round(passif_social, 2),
            "provisions": round(passif_provisions, 2),
            "resultat_net": round(resultat_fec, 2),
        },
        "ecart": ecart,
        "ecart_pct": ecart_pct,
        "risk_level": risk_level,
        "interpretation": (
            f"Bilan équilibré : Actif ≈ Passif ({total_actif:,.0f} FCFA, écart {ecart_pct}%)."
            if risk_level == "VERT" else
            f"DÉSÉQUILIBRE BILAN : Actif {total_actif:,.0f} ≠ Passif {total_passif:,.0f} "
            f"(écart {ecart:,.0f} FCFA soit {ecart_pct}%)."
        ),
    }


def detect_doublons_ecritures(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Détecte les doublons exacts :
    - Même EcritureNum + même CompteNum + même Débit + même Crédit
    - Même date + même CompteNum + même montant (doublon probable sans même numéro)
    """
    duplicates = []

    if "EcritureNum" in df.columns and "CompteNum" in df.columns:
        cols = ["EcritureNum", "CompteNum", "Debit", "Credit"]
        existing_cols = [c for c in cols if c in df.columns]
        dupes = df[df.duplicated(subset=existing_cols, keep=False)]
        if not dupes.empty:
            for _, row in dupes.head(20).iterrows():
                entry = {
                    "type": "DOUBLON_EXACT",
                    "ecriture_num": str(row.get("EcritureNum", "")),
                    "account": str(row.get("CompteNum", "")),
                    "debit": float(row.get("Debit", 0)),
                    "credit": float(row.get("Credit", 0)),
                    "severity": "ROUGE",
                }
                if "EcritureDate" in df.columns:
                    entry["date"] = str(row.get("EcritureDate", ""))
                if "EcritureLib" in df.columns:
                    entry["label"] = str(row.get("EcritureLib", ""))[:80]
                duplicates.append(entry)

    # Doublons probables : même date + même compte + même montant (Débit ou Crédit)
    if "EcritureDate" in df.columns and "CompteNum" in df.columns:
        for col in ["Debit", "Credit"]:
            if col not in df.columns:
                continue
            mask = df[col] > 0
            sub = df[mask].copy()
            grp_cols = ["EcritureDate", "CompteNum", col]
            probable = sub[sub.duplicated(subset=grp_cols, keep=False)]
            for _, row in probable.head(10).iterrows():
                amount = float(row.get(col, 0))
                if amount > 10_000:  # Seuil minimal pour éviter le bruit
                    duplicates.append({
                        "type": "DOUBLON_PROBABLE",
                        "account": str(row.get("CompteNum", "")),
                        "date": str(row.get("EcritureDate", "")),
                        col.lower(): amount,
                        "severity": "ORANGE",
                        "label": str(row.get("EcritureLib", ""))[:80],
                    })

    rouge_count = sum(1 for d in duplicates if d["severity"] == "ROUGE")
    risk_level = "VERT"
    if rouge_count > 0:
        risk_level = "ROUGE"
    elif len(duplicates) > 0:
        risk_level = "ORANGE"

    return {
        "duplicates_count": len(duplicates),
        "exact_duplicates": rouge_count,
        "duplicates": duplicates[:30],
        "risk_level": risk_level,
        "interpretation": (
            f"{len(duplicates)} doublon(s) détecté(s) dont {rouge_count} exact(s)."
            if duplicates else
            "Aucun doublon d'écriture détecté."
        ),
    }


def detect_montants_repetes(df: pd.DataFrame, min_occurrences: int = 5) -> Dict[str, Any]:
    """
    Détecte les montants qui apparaissent un nombre suspicieux de fois
    sur des comptes/écritures différents — potentiel schéma de fraude par montants fictifs.
    """
    suspects = []

    for col in ["Debit", "Credit"]:
        if col not in df.columns:
            continue
        mask = df[col] > 0
        value_counts = df.loc[mask, col].value_counts()
        repeated = value_counts[value_counts >= min_occurrences]

        for amount, count in repeated.head(10).items():
            if float(amount) > 100_000:
                unique_accounts = df.loc[df[col] == amount, "CompteNum"].nunique() if "CompteNum" in df.columns else 0
                severity = "ROUGE" if unique_accounts >= 3 and count >= 10 else "ORANGE"
                suspects.append({
                    "amount": round(float(amount), 2),
                    "column": col,
                    "occurrences": int(count),
                    "unique_accounts": unique_accounts,
                    "severity": severity,
                })

    suspects.sort(key=lambda x: -x["occurrences"])

    rouge_count = sum(1 for s in suspects if s["severity"] == "ROUGE")
    risk_level = "VERT"
    if rouge_count > 0:
        risk_level = "ROUGE"
    elif suspects:
        risk_level = "ORANGE"

    return {
        "suspicious_amounts_count": len(suspects),
        "suspicious_amounts": suspects[:20],
        "risk_level": risk_level,
        "interpretation": (
            f"{len(suspects)} montant(s) répété(s) de façon suspecte ({rouge_count} ROUGE)."
            if suspects else
            "Aucun montant répété de façon anormale."
        ),
    }


def run_coherence_check(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Orchestrateur — exécute tous les contrôles de cohérence.
    Retourne un résultat consolidé avec risk_level global.
    """
    soldes = check_soldes_normaux(df)
    resultat = check_resultat_coherence(df)
    bilan = check_equilibre_bilan(df)
    doublons = detect_doublons_ecritures(df)
    montants = detect_montants_repetes(df)

    levels = [
        soldes.get("risk_level", "VERT"),
        resultat.get("risk_level", "VERT"),
        bilan.get("risk_level", "VERT"),
        doublons.get("risk_level", "VERT"),
        montants.get("risk_level", "VERT"),
    ]
    if "ROUGE" in levels:
        global_level = "ROUGE"
    elif "ORANGE" in levels:
        global_level = "ORANGE"
    else:
        global_level = "VERT"

    total_anomalies = (
        soldes.get("anomalies_count", 0)
        + doublons.get("duplicates_count", 0)
        + montants.get("suspicious_amounts_count", 0)
        + (0 if resultat.get("coherent", True) else 1)
        + (0 if bilan.get("risk_level", "VERT") == "VERT" else 1)
    )

    return {
        "risk_level": global_level,
        "total_anomalies": total_anomalies,
        "soldes_normaux": soldes,
        "resultat_coherence": resultat,
        "equilibre_bilan": bilan,
        "doublons": doublons,
        "montants_repetes": montants,
        "interpretation": _global_interpretation(global_level, total_anomalies),
    }


def _global_interpretation(level: str, total: int) -> str:
    if level == "VERT":
        return (
            "Contrôles de cohérence SYSCOHADA réussis. "
            "Les états financiers présentent une structure cohérente."
        )
    elif level == "ORANGE":
        return (
            f"{total} anomalie(s) de cohérence détectée(s) — niveau modéré. "
            "Revue manuelle recommandée avant certification."
        )
    else:
        return (
            f"{total} anomalie(s) CRITIQUES de cohérence — "
            "incohérences majeures dans les états financiers. "
            "Investigation immédiate requise avant toute opinion d'audit."
        )

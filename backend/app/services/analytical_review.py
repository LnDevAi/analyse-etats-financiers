"""
Revue analytique SYSCOHADA — comparaison N vs N-1 par compte, détection des déviations.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


SYSCOHADA_CLASSES = {
    "1": "Comptes de ressources durables",
    "2": "Comptes d'actif immobilisé",
    "3": "Comptes de stocks",
    "4": "Comptes de tiers",
    "5": "Comptes de trésorerie",
    "6": "Comptes de charges",
    "7": "Comptes de produits",
    "8": "Comptes des autres charges et produits",
    "9": "Comptes des engagements hors bilan",
}


def compute_account_balances(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les soldes par compte (Débit - Crédit)."""
    if "CompteNum" not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby("CompteNum").agg(
        total_debit=("Debit", "sum"),
        total_credit=("Credit", "sum"),
        nb_ecritures=("Debit", "count"),
    ).reset_index()

    grouped["solde_net"] = grouped["total_debit"] - grouped["total_credit"]
    grouped["classe"] = grouped["CompteNum"].str[:1]
    grouped["classe_lib"] = grouped["classe"].map(SYSCOHADA_CLASSES).fillna("Inconnu")

    if "CompteLib" in df.columns:
        lib_map = df.groupby("CompteNum")["CompteLib"].first()
        grouped["compte_lib"] = grouped["CompteNum"].map(lib_map)

    return grouped


def run_analytical_review(
    df_current: pd.DataFrame,
    df_previous: Optional[pd.DataFrame] = None,
    threshold_pct: float = 20.0,
) -> Dict[str, Any]:
    """
    Revue analytique N vs N-1.
    Si df_previous est None, analyse uniquement N.
    """
    balances_n = compute_account_balances(df_current)

    if balances_n.empty:
        return {"error": "Colonne CompteNum absente dans le FEC."}

    summary_by_class = (
        balances_n.groupby("classe_lib")
        .agg(solde=("solde_net", "sum"), nb_comptes=("CompteNum", "count"))
        .round(2)
        .to_dict("index")
    )

    result = {
        "fiscal_year_n": {
            "total_accounts": len(balances_n),
            "total_debit": round(float(balances_n["total_debit"].sum()), 2),
            "total_credit": round(float(balances_n["total_credit"].sum()), 2),
            "by_class": summary_by_class,
        }
    }

    if df_previous is not None and not df_previous.empty:
        balances_n1 = compute_account_balances(df_previous)
        comparison = _compare_balances(balances_n, balances_n1, threshold_pct)
        result["comparison_n_vs_n1"] = comparison

    high_volume_accounts = (
        balances_n.nlargest(10, "nb_ecritures")[
            ["CompteNum", "classe_lib", "total_debit", "total_credit", "nb_ecritures"]
        ]
        .round(2)
        .to_dict("records")
    )
    result["high_volume_accounts"] = high_volume_accounts

    result["risk_level"] = "VERT"
    if df_previous is not None and "deviations" in result.get("comparison_n_vs_n1", {}):
        devs = result["comparison_n_vs_n1"]["deviations"]
        rouge_count = sum(1 for d in devs if d.get("severity") == "ROUGE")
        orange_count = sum(1 for d in devs if d.get("severity") == "ORANGE")
        if rouge_count > 0:
            result["risk_level"] = "ROUGE"
        elif orange_count > 2:
            result["risk_level"] = "ORANGE"

    return result


def _compare_balances(
    n: pd.DataFrame, n1: pd.DataFrame, threshold_pct: float
) -> Dict[str, Any]:
    merged = n.merge(
        n1[["CompteNum", "solde_net", "nb_ecritures"]],
        on="CompteNum",
        how="outer",
        suffixes=("_n", "_n1"),
    ).fillna(0)

    deviations = []
    for _, row in merged.iterrows():
        solde_n = float(row.get("solde_net_n", 0) or 0)
        solde_n1 = float(row.get("solde_net_n1", 0) or 0)
        if solde_n1 == 0:
            if solde_n != 0:
                variation_pct = 100.0
            else:
                continue
        else:
            variation_pct = abs((solde_n - solde_n1) / abs(solde_n1)) * 100

        if variation_pct >= threshold_pct or (solde_n1 == 0 and solde_n != 0):
            severity = "ROUGE" if variation_pct > 50 or (solde_n1 == 0 and abs(solde_n) > 1000) else "ORANGE"
            deviations.append({
                "account": str(row["CompteNum"]),
                "solde_n": round(solde_n, 2),
                "solde_n1": round(solde_n1, 2),
                "variation_pct": round(variation_pct, 1),
                "severity": severity,
            })

    deviations.sort(key=lambda x: -x["variation_pct"])

    return {
        "total_accounts_compared": len(merged),
        "deviations_count": len(deviations),
        "threshold_pct": threshold_pct,
        "deviations": deviations[:30],
    }

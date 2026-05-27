"""
Cross-checking : comparaison cellulaire entre deux versions d'un même document.
Détecte les falsifications, altérations de chiffres entre bilan déposé aux impôts
et bilan présenté à la banque (cas typique zone UEMOA).
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.services.fec_parser import parse_fec, validate_partie_double


def run_cross_check(
    content_a: bytes,
    content_b: bytes,
    label_a: str = "Document A",
    label_b: str = "Document B",
    tolerance_pct: float = 0.01,
) -> Dict[str, Any]:
    """
    Compare deux FEC/documents de la même entité.
    Identifie les comptes dont les soldes divergent au-delà de la tolérance.

    tolerance_pct : écart relatif acceptable (0.01 = 1%)
    """
    df_a, meta_a = parse_fec(content_a)
    df_b, meta_b = parse_fec(content_b)

    if "CompteNum" not in df_a.columns or "CompteNum" not in df_b.columns:
        return {"error": "Colonne CompteNum absente dans l'un des documents."}

    balances_a = _compute_balances(df_a, label_a)
    balances_b = _compute_balances(df_b, label_b)

    merged = balances_a.merge(balances_b, on="CompteNum", how="outer", suffixes=("_a", "_b")).fillna(0)

    discrepancies = []
    for _, row in merged.iterrows():
        sol_a = float(row.get("solde_a", 0))
        sol_b = float(row.get("solde_b", 0))
        ref = max(abs(sol_a), abs(sol_b))
        if ref == 0:
            continue
        diff_abs = abs(sol_a - sol_b)
        diff_pct = diff_abs / ref * 100

        if diff_pct > tolerance_pct * 100:
            severity = "ROUGE" if diff_pct > 10 or diff_abs > 5_000_000 else "ORANGE"
            discrepancies.append({
                "account": str(row["CompteNum"]),
                f"solde_{label_a}": round(sol_a, 2),
                f"solde_{label_b}": round(sol_b, 2),
                "difference_abs": round(diff_abs, 2),
                "difference_pct": round(diff_pct, 2),
                "severity": severity,
                "flag": _flag_type(sol_a, sol_b),
            })

    discrepancies.sort(key=lambda x: -x["difference_abs"])

    rouge_count = sum(1 for d in discrepancies if d["severity"] == "ROUGE")
    risk_level = "VERT"
    if rouge_count > 0:
        risk_level = "ROUGE"
    elif len(discrepancies) > 3:
        risk_level = "ORANGE"

    return {
        "document_a": {"label": label_a, "rows": meta_a["rows"], "total_debit": meta_a["total_debit"]},
        "document_b": {"label": label_b, "rows": meta_b["rows"], "total_debit": meta_b["total_debit"]},
        "accounts_compared": len(merged),
        "discrepancies_count": len(discrepancies),
        "rouge_discrepancies": rouge_count,
        "risk_level": risk_level,
        "discrepancies": discrepancies[:30],
        "interpretation": _interpret_cross_check(discrepancies, rouge_count),
    }


def _compute_balances(df: pd.DataFrame, label: str) -> pd.DataFrame:
    grouped = df.groupby("CompteNum").agg(
        debit=("Debit", "sum"),
        credit=("Credit", "sum"),
    ).reset_index()
    grouped["solde"] = grouped["debit"] - grouped["credit"]
    return grouped[["CompteNum", "solde"]]


def _flag_type(a: float, b: float) -> str:
    if a == 0 and b != 0:
        return "COMPTE_ABSENT_DOC_A"
    if b == 0 and a != 0:
        return "COMPTE_ABSENT_DOC_B"
    if (a > 0) != (b > 0):
        return "INVERSION_SIGNE"
    if abs(a - b) / max(abs(a), abs(b)) > 0.5:
        return "ECART_MAJEUR"
    return "ECART_MINEUR"


def _interpret_cross_check(discrepancies: List[Dict], rouge: int) -> str:
    total = len(discrepancies)
    if total == 0:
        return "Aucune divergence détectée entre les deux documents. Cohérence validée."
    if rouge > 0:
        return (
            f"{rouge} divergence(s) majeure(s) détectée(s) sur {total} compte(s) analysés. "
            "Risque élevé de falsification ou d'altération délibérée des chiffres. "
            "Investigations approfondies requises."
        )
    return (
        f"{total} écart(s) mineurs détectés. "
        "Vérifier les différences de présentation comptable entre les deux versions."
    )

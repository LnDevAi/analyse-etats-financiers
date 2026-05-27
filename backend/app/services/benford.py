"""
Loi de Benford — détection de manipulations comptables.
Distribution théorique du premier chiffre significatif dans les données naturelles.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy import stats


BENFORD_DISTRIBUTION = {
    1: 0.30103,
    2: 0.17609,
    3: 0.12494,
    4: 0.09691,
    5: 0.07918,
    6: 0.06695,
    7: 0.05799,
    8: 0.05115,
    9: 0.04576,
}


def get_first_digit(amount: float) -> int | None:
    if amount <= 0:
        return None
    s = str(abs(amount)).replace(".", "").lstrip("0")
    return int(s[0]) if s else None


def run_benford_analysis(df: pd.DataFrame, amount_col: str = "Debit") -> Dict[str, Any]:
    amounts = df[amount_col].dropna()
    amounts = amounts[amounts > 0]

    if len(amounts) < 100:
        return {
            "sufficient_data": False,
            "message": f"Données insuffisantes ({len(amounts)} lignes > 0). Minimum recommandé : 100.",
        }

    first_digits = amounts.apply(get_first_digit).dropna().astype(int)
    observed_counts = first_digits.value_counts().sort_index()
    total = len(first_digits)

    result = {}
    for digit in range(1, 10):
        observed = observed_counts.get(digit, 0)
        expected = BENFORD_DISTRIBUTION[digit]
        observed_freq = observed / total
        deviation_pct = abs(observed_freq - expected) / expected * 100
        result[digit] = {
            "expected_pct": round(expected * 100, 2),
            "observed_pct": round(observed_freq * 100, 2),
            "deviation_pct": round(deviation_pct, 2),
            "count": int(observed),
        }

    # Chi-square test
    expected_counts = [BENFORD_DISTRIBUTION[d] * total for d in range(1, 10)]
    observed_list = [observed_counts.get(d, 0) for d in range(1, 10)]
    chi2, p_value = stats.chisquare(observed_list, f_exp=expected_counts)

    suspicious_digits = [d for d, v in result.items() if v["deviation_pct"] > 20]
    conformity_score = max(0, 100 - sum(v["deviation_pct"] for v in result.values()) / 9)

    risk_level = "VERT"
    if p_value < 0.05 or conformity_score < 70:
        risk_level = "ROUGE"
    elif p_value < 0.10 or conformity_score < 85:
        risk_level = "ORANGE"

    return {
        "sufficient_data": True,
        "total_amounts_analyzed": int(total),
        "distribution": result,
        "chi2_statistic": round(float(chi2), 4),
        "p_value": round(float(p_value), 6),
        "conformity_score": round(conformity_score, 1),
        "suspicious_digits": suspicious_digits,
        "risk_level": risk_level,
        "interpretation": _interpret_benford(p_value, conformity_score, suspicious_digits),
    }


def _interpret_benford(p_value: float, score: float, suspicious: list) -> str:
    if p_value >= 0.10 and score >= 85:
        return "Distribution conforme à la loi de Benford. Aucune anomalie statistique détectée."
    elif p_value < 0.05 or score < 70:
        digits_str = ", ".join(str(d) for d in suspicious)
        return (
            f"Distribution significativement non conforme (p={p_value:.4f}). "
            f"Chiffres suspects : {digits_str}. "
            "Risque élevé de manipulation ou d'écritures fictives."
        )
    else:
        return (
            f"Légère déviation détectée (p={p_value:.4f}, score={score:.1f}). "
            "Surveillance recommandée."
        )

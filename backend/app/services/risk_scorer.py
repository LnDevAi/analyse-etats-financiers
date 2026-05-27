"""
Calcul du score de risque global 0-100 et niveau (VERT/ORANGE/ROUGE).
"""
from typing import Dict, Any, Optional


RISK_WEIGHTS = {
    "intrinsic_check": 0.20,    # Partie double
    "coherence_check": 0.20,    # Cohérence SYSCOHADA (soldes normaux, bilan, résultat, doublons)
    "benford": 0.17,            # Fraude statistique
    "isolation_forest": 0.15,   # Anomalies ML
    "analytical_review": 0.12,  # Revue N vs N-1
    "cycle_ventes": 0.08,       # Cut-off ventes
    "cycle_tresorerie": 0.08,   # Flux trésorerie suspects
}

LEVEL_SCORES = {"VERT": 100, "ORANGE": 50, "ROUGE": 0}


def _module_score(result: Optional[Dict[str, Any]], key: str = "risk_level") -> float:
    if not result:
        return 100.0
    level = result.get(key, "VERT")
    if isinstance(level, str):
        return float(LEVEL_SCORES.get(level.upper(), 75))
    return 75.0


def compute_risk_score(
    intrinsic_check: Optional[Dict] = None,
    benford_result: Optional[Dict] = None,
    isolation_forest_result: Optional[Dict] = None,
    analytical_review: Optional[Dict] = None,
    cycle_ventes_result: Optional[Dict] = None,
    cycle_tresorerie_result: Optional[Dict] = None,
    coherence_check_result: Optional[Dict] = None,
) -> Dict[str, Any]:
    scores = {
        "intrinsic_check": _compute_intrinsic_score(intrinsic_check),
        "coherence_check": _module_score(coherence_check_result),
        "benford": _module_score(benford_result),
        "isolation_forest": _module_score(isolation_forest_result),
        "analytical_review": _module_score(analytical_review),
        "cycle_ventes": _module_score(cycle_ventes_result),
        "cycle_tresorerie": _module_score(cycle_tresorerie_result),
    }

    global_score = sum(
        scores[mod] * RISK_WEIGHTS[mod] for mod in RISK_WEIGHTS
    )
    global_score = round(global_score, 1)

    if global_score >= 75:
        risk_level = "VERT"
    elif global_score >= 45:
        risk_level = "ORANGE"
    else:
        risk_level = "ROUGE"

    return {
        "global_score": global_score,
        "risk_level": risk_level,
        "module_scores": scores,
        "interpretation": _interpret_score(global_score, risk_level),
    }


def _compute_intrinsic_score(result: Optional[Dict]) -> float:
    if not result:
        return 100.0
    if not result.get("valid", True):
        return 0.0
    diff = result.get("difference", 0)
    if diff == 0:
        return 100.0
    elif diff < 100:
        return 80.0
    elif diff < 10000:
        return 50.0
    else:
        return 10.0


def _interpret_score(score: float, level: str) -> str:
    if level == "VERT":
        return (
            f"Score de confiance : {score}/100. "
            "Les états financiers analysés présentent un niveau de risque faible. "
            "Aucune anomalie majeure détectée par les algorithmes d'analyse."
        )
    elif level == "ORANGE":
        return (
            f"Score de confiance : {score}/100. "
            "Des anomalies statistiques modérées ont été détectées. "
            "Une revue approfondie par un auditeur est recommandée avant certification."
        )
    else:
        return (
            f"Score de confiance : {score}/100. "
            "ALERTE : Les algorithmes ont détecté des anomalies significatives susceptibles "
            "d'indiquer des fraudes, incohérences bloquantes ou falsifications. "
            "Une investigation immédiate est requise."
        )

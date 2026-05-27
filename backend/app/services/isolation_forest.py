"""
Isolation Forest — détection d'écritures comptables atypiques (anomalie ML non supervisée).
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List


def run_isolation_forest(df: pd.DataFrame, contamination: float = 0.05) -> Dict[str, Any]:
    """
    Détecte les écritures anormales via Isolation Forest.
    contamination: proportion attendue d'anomalies (par défaut 5%).
    """
    features_cols = []
    feature_df = pd.DataFrame()

    if "Debit" in df.columns:
        feature_df["Debit"] = df["Debit"].fillna(0)
        features_cols.append("Debit")
    if "Credit" in df.columns:
        feature_df["Credit"] = df["Credit"].fillna(0)
        features_cols.append("Credit")

    if "EcritureDate" in df.columns:
        feature_df["day_of_week"] = pd.to_datetime(df["EcritureDate"], errors="coerce").dt.dayofweek.fillna(0)
        feature_df["day_of_month"] = pd.to_datetime(df["EcritureDate"], errors="coerce").dt.day.fillna(0)
        feature_df["month"] = pd.to_datetime(df["EcritureDate"], errors="coerce").dt.month.fillna(0)
        features_cols += ["day_of_week", "day_of_month", "month"]

    if feature_df.shape[0] < 20 or not features_cols:
        return {
            "sufficient_data": False,
            "message": "Données insuffisantes pour Isolation Forest (minimum 20 écritures).",
        }

    scaler = StandardScaler()
    X = scaler.fit_transform(feature_df[features_cols])

    model = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    predictions = model.fit_predict(X)
    scores = model.score_samples(X)

    anomaly_mask = predictions == -1
    anomaly_indices = np.where(anomaly_mask)[0]

    anomalies = []
    for idx in anomaly_indices[:50]:
        row = df.iloc[idx]
        entry = {
            "row_index": int(idx),
            "anomaly_score": round(float(scores[idx]), 4),
            "debit": float(row.get("Debit", 0) or 0),
            "credit": float(row.get("Credit", 0) or 0),
        }
        if "CompteNum" in df.columns:
            entry["account"] = str(row.get("CompteNum", ""))
        if "EcritureLib" in df.columns:
            entry["label"] = str(row.get("EcritureLib", ""))[:100]
        if "EcritureDate" in df.columns:
            entry["date"] = str(row.get("EcritureDate", ""))
        anomalies.append(entry)

    anomalies.sort(key=lambda x: x["anomaly_score"])

    total_anomalies = int(anomaly_mask.sum())
    risk_level = "VERT"
    if total_anomalies > len(df) * 0.10:
        risk_level = "ROUGE"
    elif total_anomalies > len(df) * 0.05:
        risk_level = "ORANGE"

    return {
        "sufficient_data": True,
        "total_entries": len(df),
        "anomalies_detected": total_anomalies,
        "anomaly_rate_pct": round(total_anomalies / len(df) * 100, 2),
        "risk_level": risk_level,
        "top_anomalies": anomalies,
        "features_used": features_cols,
        "interpretation": _interpret_if(total_anomalies, len(df)),
    }


def _interpret_if(anomalies: int, total: int) -> str:
    rate = anomalies / total * 100
    if rate < 3:
        return f"{anomalies} écritures atypiques ({rate:.1f}%). Volume normal — faible risque."
    elif rate < 8:
        return f"{anomalies} écritures atypiques ({rate:.1f}%). Taux modéré — revue recommandée."
    else:
        return (
            f"{anomalies} écritures atypiques ({rate:.1f}%). "
            "Taux élevé — suspicion d'anomalies systémiques ou de fraude."
        )

"""
Audit des cycles critiques SYSCOHADA :
- Cycle Ventes/Clients : détection cut-off
- Cycle Trésorerie : rapprochement bancaire + flux suspects
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime


# Comptes Clients SYSCOHADA : classe 41x
CLIENT_ACCOUNTS = ["411", "412", "413", "414", "416", "417", "418", "419"]
# Comptes Ventes : classe 70x, 71x
VENTES_ACCOUNTS = ["701", "702", "703", "704", "705", "706", "707", "708", "709"]
# Comptes Trésorerie : classe 51x, 52x, 57x
TRESORERIE_ACCOUNTS = ["511", "512", "514", "515", "516", "521", "571", "572"]


def run_cycle_ventes(df: pd.DataFrame, fiscal_year: int = None) -> Dict[str, Any]:
    """
    Détecte les anomalies de cut-off : ventes enregistrées hors période fiscale.
    """
    if "CompteNum" not in df.columns or "EcritureDate" not in df.columns:
        return {"error": "Colonnes CompteNum ou EcritureDate absentes."}

    df = df.copy()
    df["EcritureDate"] = pd.to_datetime(df["EcritureDate"], errors="coerce")

    if fiscal_year is None and not df["EcritureDate"].isna().all():
        fiscal_year = df["EcritureDate"].dropna().dt.year.mode().iloc[0]

    ventes_mask = df["CompteNum"].str[:3].isin(VENTES_ACCOUNTS)
    clients_mask = df["CompteNum"].str[:3].isin(CLIENT_ACCOUNTS)

    df_ventes = df[ventes_mask].copy()
    df_clients = df[clients_mask].copy()

    cutoff_anomalies = []
    if fiscal_year and not df_ventes.empty:
        start = pd.Timestamp(fiscal_year, 1, 1)
        end = pd.Timestamp(fiscal_year, 12, 31)
        out_of_period = df_ventes[
            (df_ventes["EcritureDate"] < start) | (df_ventes["EcritureDate"] > end)
        ]
        for _, row in out_of_period.head(20).iterrows():
            cutoff_anomalies.append({
                "date": str(row["EcritureDate"].date()) if pd.notna(row["EcritureDate"]) else None,
                "account": str(row.get("CompteNum", "")),
                "label": str(row.get("EcritureLib", ""))[:80],
                "debit": float(row.get("Debit", 0) or 0),
                "credit": float(row.get("Credit", 0) or 0),
            })

    # Analyse des ventes par mois
    monthly_ventes = {}
    if not df_ventes.empty:
        df_ventes["month"] = df_ventes["EcritureDate"].dt.to_period("M").astype(str)
        monthly_ventes = (
            df_ventes.groupby("month")["Credit"].sum().round(2).to_dict()
        )

    risk_level = "VERT"
    if len(cutoff_anomalies) > 10:
        risk_level = "ROUGE"
    elif len(cutoff_anomalies) > 3:
        risk_level = "ORANGE"

    return {
        "fiscal_year_analyzed": int(fiscal_year) if fiscal_year else None,
        "ventes_entries": len(df_ventes),
        "clients_entries": len(df_clients),
        "cutoff_anomalies_count": len(cutoff_anomalies),
        "cutoff_anomalies_sample": cutoff_anomalies,
        "monthly_ventes": monthly_ventes,
        "risk_level": risk_level,
        "interpretation": f"{len(cutoff_anomalies)} anomalie(s) de cut-off détectée(s)." if cutoff_anomalies else "Aucune anomalie de cut-off détectée.",
    }


def run_cycle_tresorerie(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Rapprochement bancaire intelligent — détection de flux suspects :
    - Montants élevés sans libellé
    - Transactions week-end / jours fériés UEMOA
    - Flux ronds suspects
    """
    if "CompteNum" not in df.columns:
        return {"error": "Colonne CompteNum absente."}

    df = df.copy()
    df["EcritureDate"] = pd.to_datetime(df.get("EcritureDate"), errors="coerce")

    tres_mask = df["CompteNum"].str[:3].isin(TRESORERIE_ACCOUNTS)
    df_tres = df[tres_mask].copy()

    if df_tres.empty:
        return {"error": "Aucune écriture de trésorerie (511-572) trouvée."}

    suspicious = []

    # 1. Flux sans libellé
    if "EcritureLib" in df_tres.columns:
        no_label = df_tres[
            df_tres["EcritureLib"].isna() | (df_tres["EcritureLib"].str.strip() == "")
        ]
        for _, row in no_label.head(10).iterrows():
            suspicious.append({
                "type": "SANS_LIBELLE",
                "date": str(row["EcritureDate"].date()) if pd.notna(row["EcritureDate"]) else None,
                "account": str(row.get("CompteNum", "")),
                "amount": float(max(row.get("Debit", 0) or 0, row.get("Credit", 0) or 0)),
                "severity": "ORANGE",
            })

    # 2. Transactions week-end
    if "EcritureDate" in df_tres.columns:
        weekend_mask = df_tres["EcritureDate"].dt.dayofweek >= 5
        weekend_txs = df_tres[weekend_mask]
        for _, row in weekend_txs.head(10).iterrows():
            amount = float(max(row.get("Debit", 0) or 0, row.get("Credit", 0) or 0))
            if amount > 100000:
                suspicious.append({
                    "type": "WEEKEND_HIGH_AMOUNT",
                    "date": str(row["EcritureDate"].date()),
                    "account": str(row.get("CompteNum", "")),
                    "amount": amount,
                    "day": row["EcritureDate"].strftime("%A"),
                    "severity": "ROUGE",
                })

    # 3. Montants ronds suspects (multiples de 1 000 000)
    for col in ["Debit", "Credit"]:
        if col in df_tres.columns:
            round_mask = (df_tres[col] > 0) & (df_tres[col] % 1_000_000 == 0)
            for _, row in df_tres[round_mask].head(10).iterrows():
                suspicious.append({
                    "type": "MONTANT_ROND_SUSPECT",
                    "date": str(row["EcritureDate"].date()) if pd.notna(row.get("EcritureDate")) else None,
                    "account": str(row.get("CompteNum", "")),
                    "amount": float(row.get(col, 0)),
                    "severity": "ORANGE",
                })

    risk_level = "VERT"
    rouge_count = sum(1 for s in suspicious if s["severity"] == "ROUGE")
    orange_count = sum(1 for s in suspicious if s["severity"] == "ORANGE")
    if rouge_count > 0:
        risk_level = "ROUGE"
    elif orange_count > 3:
        risk_level = "ORANGE"

    total_flux = float(df_tres[["Debit", "Credit"]].sum().sum())

    return {
        "tresorerie_entries": len(df_tres),
        "total_flux": round(total_flux, 2),
        "suspicious_transactions_count": len(suspicious),
        "suspicious_transactions": suspicious[:30],
        "risk_level": risk_level,
        "breakdown": {
            "sans_libelle": sum(1 for s in suspicious if s["type"] == "SANS_LIBELLE"),
            "weekend": sum(1 for s in suspicious if s["type"] == "WEEKEND_HIGH_AMOUNT"),
            "montant_rond": sum(1 for s in suspicious if s["type"] == "MONTANT_ROND_SUSPECT"),
        },
    }

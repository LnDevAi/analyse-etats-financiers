"""
Parseur FEC (Fichier des Écritures Comptables) — format texte délimité.
Norme DGFiP France / SYSCOHADA UEMOA.
"""
import pandas as pd
import io
import chardet
from typing import Tuple


FEC_COLUMNS = [
    "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
    "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
    "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit",
    "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
]


def detect_encoding(raw_bytes: bytes) -> str:
    result = chardet.detect(raw_bytes)
    return result.get("encoding") or "utf-8"


def parse_fec(content: bytes) -> Tuple[pd.DataFrame, dict]:
    encoding = detect_encoding(content)
    text = content.decode(encoding, errors="replace")

    sep = "\t" if "\t" in text.split("\n")[0] else "|"
    df = pd.read_csv(
        io.StringIO(text),
        sep=sep,
        dtype=str,
        on_bad_lines="skip",
    )

    df.columns = [c.strip() for c in df.columns]

    for col in ["Debit", "Credit"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
                .fillna(0.0)
                .astype(float)
            )

    if "EcritureDate" in df.columns:
        df["EcritureDate"] = pd.to_datetime(df["EcritureDate"], format="%Y%m%d", errors="coerce")

    meta = {
        "rows": len(df),
        "encoding": encoding,
        "separator": sep,
        "columns_found": list(df.columns),
        "date_range": {
            "min": str(df["EcritureDate"].min()) if "EcritureDate" in df.columns else None,
            "max": str(df["EcritureDate"].max()) if "EcritureDate" in df.columns else None,
        },
        "total_debit": float(df["Debit"].sum()) if "Debit" in df.columns else 0,
        "total_credit": float(df["Credit"].sum()) if "Credit" in df.columns else 0,
    }
    return df, meta


def validate_partie_double(df: pd.DataFrame) -> dict:
    """Vérifie l'équilibre Débit = Crédit par journal/écriture."""
    if "Debit" not in df.columns or "Credit" not in df.columns:
        return {"valid": False, "error": "Colonnes Débit/Crédit absentes"}

    total_debit = df["Debit"].sum()
    total_credit = df["Credit"].sum()
    diff = abs(total_debit - total_credit)
    tolerance = 0.01

    if "EcritureNum" in df.columns:
        by_ecriture = df.groupby("EcritureNum").agg(
            debit=("Debit", "sum"), credit=("Credit", "sum")
        )
        by_ecriture["diff"] = abs(by_ecriture["debit"] - by_ecriture["credit"])
        unbalanced = by_ecriture[by_ecriture["diff"] > tolerance]
        unbalanced_list = unbalanced.head(20).to_dict("records")
    else:
        unbalanced_list = []

    return {
        "valid": bool(diff <= tolerance),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "difference": round(diff, 2),
        "unbalanced_entries_count": len(unbalanced_list),
        "unbalanced_entries_sample": unbalanced_list,
    }

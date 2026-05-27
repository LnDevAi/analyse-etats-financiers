"""
Réconciliation entre la Balance Générale (trial balance) et le FEC.

La balance générale est le document comptable intermédiaire qui sert
à produire les états financiers (bilan, compte de résultat).
Un écart entre le FEC et la balance révèle une manipulation post-clôture.

Format attendu de la balance (CSV/TSV) — colonnes reconnues :
  CompteNum | CompteLib | Debit | Credit
  ou
  CompteNum | Libelle | MouvDebit | MouvCredit | SoldeDebiteur | SoldeCrediteur
  ou
  NumCompte | Compte | TotalDebit | TotalCredit
"""
import pandas as pd
import io
import chardet
from typing import Dict, Any, List, Optional


COMPTE_COL_ALIASES = ["CompteNum", "NumCompte", "Compte", "CodeCompte", "N°Compte"]
LIB_COL_ALIASES = ["CompteLib", "Libelle", "Designation", "Intitule", "LibelleCompte"]
DEBIT_COL_ALIASES = ["Debit", "MouvDebit", "TotalDebit", "Mouvement_Debit", "Debit_Mouv"]
CREDIT_COL_ALIASES = ["Credit", "MouvCredit", "TotalCredit", "Mouvement_Credit", "Credit_Mouv"]


def _find_column(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    """Trouve le premier alias correspondant dans les colonnes du DataFrame (insensible à la casse)."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in cols_lower:
            return cols_lower[alias.lower()]
    return None


def parse_balance_generale(content: bytes) -> Dict[str, Any]:
    """
    Parse une balance générale depuis un fichier CSV/TSV.
    Retourne un DataFrame normalisé avec CompteNum, CompteLib, total_debit, total_credit, solde_net.
    """
    detected = chardet.detect(content)
    encoding = detected.get("encoding") or "utf-8"
    text = content.decode(encoding, errors="replace")

    # Auto-détection du séparateur
    first_line = text.split("\n")[0]
    if "\t" in first_line:
        sep = "\t"
    elif ";" in first_line:
        sep = ";"
    else:
        sep = ","

    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]

    compte_col = _find_column(df, COMPTE_COL_ALIASES)
    debit_col = _find_column(df, DEBIT_COL_ALIASES)
    credit_col = _find_column(df, CREDIT_COL_ALIASES)
    lib_col = _find_column(df, LIB_COL_ALIASES)

    if not compte_col:
        return {"error": "Colonne numéro de compte introuvable dans la balance."}
    if not debit_col or not credit_col:
        return {"error": "Colonnes Débit/Crédit introuvables dans la balance."}

    result = pd.DataFrame()
    result["CompteNum"] = df[compte_col].astype(str).str.strip().str.replace(" ", "")
    result["CompteLib"] = df[lib_col].astype(str).str.strip() if lib_col else ""

    for col, src in [("total_debit", debit_col), ("total_credit", credit_col)]:
        result[col] = (
            df[src]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace("\xa0", "", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )

    result["solde_net"] = result["total_debit"] - result["total_credit"]
    result = result[result["CompteNum"].str.match(r"^\d+$", na=False)]  # Garder uniquement les comptes numériques

    return {
        "data": result,
        "rows": len(result),
        "total_debit": round(float(result["total_debit"].sum()), 2),
        "total_credit": round(float(result["total_credit"].sum()), 2),
    }


def _compute_fec_balances(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les soldes par compte depuis le FEC."""
    return (
        df.groupby("CompteNum")
        .agg(total_debit=("Debit", "sum"), total_credit=("Credit", "sum"))
        .reset_index()
        .assign(solde_net=lambda d: d["total_debit"] - d["total_credit"])
    )


def run_balance_reconciliation(
    df_fec: pd.DataFrame,
    balance_content: bytes,
    tolerance_pct: float = 0.1,
) -> Dict[str, Any]:
    """
    Réconcilie les soldes du FEC avec ceux de la balance générale.

    tolerance_pct : écart relatif acceptable en % (défaut 0,1%)
    Retourne les discordances compte par compte.
    """
    if "CompteNum" not in df_fec.columns:
        return {"error": "Colonne CompteNum absente dans le FEC."}

    balance_result = parse_balance_generale(balance_content)
    if "error" in balance_result:
        return balance_result

    df_balance = balance_result["data"]
    df_fec_bal = _compute_fec_balances(df_fec)

    # Fusion sur CompteNum
    merged = df_fec_bal.merge(
        df_balance[["CompteNum", "total_debit", "total_credit", "solde_net"]],
        on="CompteNum",
        how="outer",
        suffixes=("_fec", "_balance"),
    ).fillna(0)

    discrepancies = []
    for _, row in merged.iterrows():
        sol_fec = float(row.get("solde_net_fec", 0))
        sol_bal = float(row.get("solde_net_balance", 0))
        deb_fec = float(row.get("total_debit_fec", 0))
        deb_bal = float(row.get("total_debit_balance", 0))
        cred_fec = float(row.get("total_credit_fec", 0))
        cred_bal = float(row.get("total_credit_balance", 0))

        compte = str(row["CompteNum"])

        # Écart sur le solde net
        ref = max(abs(sol_fec), abs(sol_bal))
        if ref == 0:
            continue

        ecart_solde = abs(sol_fec - sol_bal)
        ecart_pct = ecart_solde / ref * 100

        # Écart sur les mouvements (débit seul, crédit seul)
        ecart_debit = abs(deb_fec - deb_bal)
        ecart_credit = abs(cred_fec - cred_bal)

        if ecart_pct <= tolerance_pct and ecart_debit < 1 and ecart_credit < 1:
            continue

        flag = _flag_discrepancy(sol_fec, sol_bal, deb_fec, deb_bal, cred_fec, cred_bal)
        severity = _severity(ecart_solde, ecart_pct, flag)

        discrepancies.append({
            "account": compte,
            "flag": flag,
            "severity": severity,
            "fec": {
                "solde_net": round(sol_fec, 2),
                "total_debit": round(deb_fec, 2),
                "total_credit": round(cred_fec, 2),
            },
            "balance": {
                "solde_net": round(sol_bal, 2),
                "total_debit": round(deb_bal, 2),
                "total_credit": round(cred_bal, 2),
            },
            "ecart_solde": round(ecart_solde, 2),
            "ecart_pct": round(ecart_pct, 2),
            "ecart_debit": round(ecart_debit, 2),
            "ecart_credit": round(ecart_credit, 2),
            "description": _describe_discrepancy(compte, flag, ecart_solde, sol_fec, sol_bal),
        })

    discrepancies.sort(key=lambda x: -x["ecart_solde"])

    rouge_count = sum(1 for d in discrepancies if d["severity"] == "ROUGE")
    risk_level = "VERT"
    if rouge_count > 0:
        risk_level = "ROUGE"
    elif len(discrepancies) > 2:
        risk_level = "ORANGE"

    # Récapitulatif global
    total_fec = round(float(df_fec_bal["total_debit"].sum()), 2)
    total_bal = round(float(df_balance["total_debit"].sum()), 2)
    ecart_global = round(abs(total_fec - total_bal), 2)

    return {
        "risk_level": risk_level,
        "fec_summary": {
            "accounts": len(df_fec_bal),
            "total_debit": total_fec,
            "total_credit": round(float(df_fec_bal["total_credit"].sum()), 2),
        },
        "balance_summary": {
            "accounts": len(df_balance),
            "total_debit": total_bal,
            "total_credit": round(float(df_balance["total_credit"].sum()), 2),
        },
        "ecart_global_debit": ecart_global,
        "accounts_compared": len(merged),
        "discrepancies_count": len(discrepancies),
        "rouge_discrepancies": rouge_count,
        "discrepancies": discrepancies[:40],
        "interpretation": _interpret(discrepancies, rouge_count, ecart_global),
    }


def _flag_discrepancy(sol_fec, sol_bal, deb_fec, deb_bal, cred_fec, cred_bal) -> str:
    if sol_fec == 0 and sol_bal != 0:
        return "ABSENT_FEC"
    if sol_bal == 0 and sol_fec != 0:
        return "ABSENT_BALANCE"
    if abs(deb_fec - deb_bal) < 1 and abs(cred_fec - cred_bal) > 1:
        return "ECART_CREDIT_UNIQUEMENT"
    if abs(cred_fec - cred_bal) < 1 and abs(deb_fec - deb_bal) > 1:
        return "ECART_DEBIT_UNIQUEMENT"
    if abs(deb_fec - cred_bal) < 1 and abs(cred_fec - deb_bal) < 1:
        return "INVERSION_DEBIT_CREDIT"
    return "ECART_SOLDE"


def _severity(ecart_abs: float, ecart_pct: float, flag: str) -> str:
    if flag in ("INVERSION_DEBIT_CREDIT", "ABSENT_FEC") or ecart_pct > 10 or ecart_abs > 5_000_000:
        return "ROUGE"
    if ecart_pct > 1 or ecart_abs > 500_000:
        return "ORANGE"
    return "ORANGE"


def _describe_discrepancy(compte, flag, ecart, sol_fec, sol_bal) -> str:
    descs = {
        "ABSENT_FEC": f"Compte {compte} présent dans la balance ({sol_bal:,.0f}) mais ABSENT du FEC — manipulation possible",
        "ABSENT_BALANCE": f"Compte {compte} dans le FEC ({sol_fec:,.0f}) mais ABSENT de la balance — omission suspecte",
        "INVERSION_DEBIT_CREDIT": f"Compte {compte} : débit et crédit INVERSÉS entre FEC et balance — erreur ou fraude",
        "ECART_CREDIT_UNIQUEMENT": f"Compte {compte} : écart uniquement côté crédit ({ecart:,.0f}) — produits potentiellement modifiés",
        "ECART_DEBIT_UNIQUEMENT": f"Compte {compte} : écart uniquement côté débit ({ecart:,.0f}) — charges potentiellement modifiées",
        "ECART_SOLDE": f"Compte {compte} : écart de solde net {ecart:,.0f} entre FEC ({sol_fec:,.0f}) et balance ({sol_bal:,.0f})",
    }
    return descs.get(flag, f"Compte {compte} : écart de {ecart:,.0f}")


def _interpret(discrepancies, rouge_count, ecart_global) -> str:
    if not discrepancies:
        return (
            f"Réconciliation parfaite — aucun écart entre le FEC et la balance générale "
            f"(écart global mouvements : {ecart_global:,.0f})."
        )
    if rouge_count > 0:
        return (
            f"ALERTE : {rouge_count} écart(s) CRITIQUE(S) sur {len(discrepancies)} compte(s). "
            "Des divergences majeures entre le FEC et la balance suggèrent des manipulations "
            "post-clôture ou des falsifications des états financiers."
        )
    return (
        f"{len(discrepancies)} écart(s) entre le FEC et la balance générale. "
        f"Écart global mouvements : {ecart_global:,.0f}. "
        "Vérification manuelle recommandée."
    )

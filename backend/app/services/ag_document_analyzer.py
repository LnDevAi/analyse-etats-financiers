"""
Module d'analyse comparative des documents AG (Assemblée Générale).

Compare les états financiers (FEC) avec les autres documents présentés en AG :
1. Rapport d'exécution budgétaire  → Budget alloué vs réalisé FEC par classe
2. Bilan social                    → Masse salariale déclarée vs FEC comptes 66x
3. Plan de passation des marchés   → Montants marchés vs FEC comptes 40x
4. Rapport d'activités             → Montants cités vs transactions FEC
5. Score de cohérence global       → Agrégé des 4 analyses
"""
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.services.document_text_extractor import extract_document, extract_amounts_from_text

logger = logging.getLogger(__name__)


# ─── Comptes SYSCOHADA de référence ───────────────────────────────────────────

COMPTE_CLASSES = {
    "1": "Ressources durables",
    "2": "Actif immobilisé",
    "3": "Stocks",
    "4": "Tiers",
    "5": "Trésorerie",
    "6": "Charges",
    "7": "Produits",
}

# Charges de personnel : 66x
PERSONNEL_ACCOUNTS = ["660", "661", "662", "663", "664", "665", "666", "667", "668"]
# Fournisseurs / Marchés : 40x + certains 60x achats
FOURNISSEURS_ACCOUNTS = ["401", "402", "403", "404", "405", "408", "409"]
ACHATS_ACCOUNTS = ["601", "602", "604", "605", "606", "607", "608"]


def _fec_totals_by_class(df: pd.DataFrame) -> Dict[str, Dict]:
    """Calcule les totaux débit/crédit/solde par classe de comptes."""
    if "CompteNum" not in df.columns:
        return {}
    df = df.copy()
    df["classe"] = df["CompteNum"].str[:1]
    result = {}
    for cls, lib in COMPTE_CLASSES.items():
        mask = df["classe"] == cls
        sub = df[mask]
        total_d = float(sub["Debit"].sum()) if "Debit" in sub.columns else 0.0
        total_c = float(sub["Credit"].sum()) if "Credit" in sub.columns else 0.0
        result[cls] = {
            "label": lib,
            "total_debit": round(total_d, 2),
            "total_credit": round(total_c, 2),
            "solde_net": round(total_d - total_c, 2),
            "nb_ecritures": int(mask.sum()),
        }
    return result


def _fec_accounts_total(df: pd.DataFrame, prefix_list: List[str], side: str = "debit") -> float:
    """Somme des débits ou crédits pour les comptes correspondant aux préfixes."""
    if "CompteNum" not in df.columns:
        return 0.0
    mask = df["CompteNum"].apply(lambda c: any(str(c).startswith(p) for p in prefix_list))
    col = "Debit" if side == "debit" else "Credit"
    return float(df.loc[mask, col].sum()) if col in df.columns else 0.0


def _parse_budget_table(tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Tente de trouver un tableau budget/réalisé dans les DataFrames extraits.
    Colonnes attendues : quelque chose comme Compte/Rubrique, Budget, Réalisé/Exécuté.
    """
    budget_keywords = ["budget", "prévision", "dotation", "allocation"]
    realise_keywords = ["réalisé", "realise", "exécuté", "execute", "dépense", "depense"]
    compte_keywords = ["compte", "rubrique", "poste", "classe", "libellé", "designation"]

    for df in tables:
        if df is None or df.empty:
            continue
        cols_lower = [str(c).lower().strip() for c in df.columns]

        compte_col = next((df.columns[i] for i, c in enumerate(cols_lower)
                           if any(k in c for k in compte_keywords)), None)
        budget_col = next((df.columns[i] for i, c in enumerate(cols_lower)
                           if any(k in c for k in budget_keywords)), None)
        realise_col = next((df.columns[i] for i, c in enumerate(cols_lower)
                            if any(k in c for k in realise_keywords)), None)

        if budget_col and realise_col:
            result = pd.DataFrame()
            result["rubrique"] = df[compte_col].astype(str) if compte_col else df.iloc[:, 0].astype(str)
            for col_name, src in [("budget", budget_col), ("realise_doc", realise_col)]:
                result[col_name] = (
                    df[src].astype(str)
                    .str.replace(",", ".", regex=False)
                    .str.replace(" ", "", regex=False)
                    .str.replace("\xa0", "", regex=False)
                    .pipe(pd.to_numeric, errors="coerce")
                    .fillna(0.0)
                )
            result = result[result["budget"] > 0]
            if not result.empty:
                return result
    return None


# ─── 1. Rapport d'exécution budgétaire ───────────────────────────────────────

def run_budget_execution_analysis(
    df_fec: pd.DataFrame,
    budget_content: Optional[bytes],
    budget_filename: str,
) -> Dict[str, Any]:
    """
    Compare le budget alloué et le réalisé déclaré (dans le rapport)
    avec le réalisé réel issu du FEC, par classe de comptes SYSCOHADA.
    """
    if not budget_content:
        return {
            "coherence_score": 1.0,
            "risk_level": "VERT",
            "table_found": False,
            "comparaison_par_classe": {},
            "ecarts_significatifs": [],
            "ecarts_count": 0,
            "interpretation": "Aucun document budgétaire fourni.",
        }

    extracted = extract_document(budget_content, budget_filename)
    tables = extracted["tables"]
    amounts = extracted["amounts_found"]

    fec_by_class = _fec_totals_by_class(df_fec)
    budget_table = _parse_budget_table(tables)

    comparaison_par_classe: Dict[str, Any] = {}
    ecarts_significatifs = []

    # Comparaison structurée si tableau trouvé
    if budget_table is not None:
        for _, row in budget_table.iterrows():
            rubrique = str(row["rubrique"])
            budget_alloue = float(row["budget"])
            realise_doc = float(row["realise_doc"])

            # Chercher la classe correspondante dans le FEC
            fec_realise = 0.0
            classe_match = None
            for cls, data in fec_by_class.items():
                if cls in rubrique or data["label"].lower() in rubrique.lower():
                    fec_realise = abs(data["solde_net"])
                    classe_match = cls
                    break

            taux_execution_doc = round(realise_doc / budget_alloue * 100, 1) if budget_alloue > 0 else 0.0
            taux_execution_fec = round(fec_realise / budget_alloue * 100, 1) if budget_alloue > 0 else 0.0
            ecart = round(abs(realise_doc - fec_realise), 2)
            ecart_pct = round(ecart / max(realise_doc, 1) * 100, 1)

            key = classe_match or rubrique
            comparaison_par_classe[key] = {
                "rubrique": rubrique,
                "budget_prevu": round(budget_alloue, 2),
                "realise_doc": round(realise_doc, 2),
                "realise_fec": round(fec_realise, 2),
                "taux_execution_rapport": taux_execution_doc,
                "taux_execution_fec": taux_execution_fec,
                "ecart": ecart,
                "ecart_pct": ecart_pct,
            }

            if ecart_pct > 5 and ecart > 500_000:
                severity = "ROUGE" if ecart_pct > 20 else "ORANGE"
                ecarts_significatifs.append({
                    "rubrique": rubrique,
                    "ecart": ecart,
                    "ecart_pct": ecart_pct,
                    "severity": severity,
                    "description": f"Écart {ecart_pct}% entre rapport budgétaire et FEC pour '{rubrique}'",
                })

    # Fallback : utiliser les montants extraits du texte
    total_budget_text = sum(a["value"] for a in amounts if "budget" in a["context"].lower())
    total_realise_text = sum(a["value"] for a in amounts
                             if any(k in a["context"].lower() for k in ["réalisé", "réalisation", "exécuté"]))

    fec_charges_total = sum(d["total_debit"] for k, d in fec_by_class.items() if k == "6")

    rouge_count = sum(1 for d in ecarts_significatifs if d["severity"] == "ROUGE")
    risk_level = "VERT" if not ecarts_significatifs else ("ROUGE" if rouge_count > 0 else "ORANGE")

    score_map = {"VERT": 1.0, "ORANGE": 0.5, "ROUGE": 0.0}
    coherence_score = score_map[risk_level]
    if risk_level == "ORANGE" and ecarts_significatifs:
        coherence_score = max(0.0, 1.0 - len(ecarts_significatifs) * 0.1)

    return {
        "coherence_score": round(coherence_score, 2),
        "risk_level": risk_level,
        "table_found": budget_table is not None,
        "comparaison_par_classe": comparaison_par_classe,
        "ecarts_significatifs": ecarts_significatifs[:10],
        "ecarts_count": len(ecarts_significatifs),
        "summary": {
            "total_budget_mentionne": round(total_budget_text, 2),
            "total_realise_mentionne": round(total_realise_text, 2),
            "total_charges_fec": round(fec_charges_total, 2),
            "fec_by_class": fec_by_class,
        },
        "interpretation": _interpret_budget(ecarts_significatifs, rouge_count, budget_table is not None),
    }


def _interpret_budget(ecarts, rouge_count, has_table) -> str:
    if not has_table:
        return "Aucun tableau budgétaire structuré détecté — analyse basée sur les montants textuels."
    if not ecarts:
        return "Cohérence validée : les réalisations du rapport budgétaire correspondent aux mouvements du FEC."
    if rouge_count > 0:
        return (f"ALERTE : {rouge_count} écart(s) majeur(s) entre le rapport budgétaire et le FEC. "
                "Possible sur/sous-déclaration de dépenses.")
    return f"{len(ecarts)} écart(s) modéré(s) détecté(s) entre le rapport et le FEC."


# ─── 2. Bilan social ─────────────────────────────────────────────────────────

# Motifs regex pour extraire les métriques RH du bilan social
SOCIAL_PATTERNS = {
    "effectif_total": re.compile(r"(?:effectif|effectifs?|agents?|employés?|personnel)\s*(?:total|:)?\s*[:\s]*([\d\s]+)", re.I),
    "masse_salariale": re.compile(r"(?:masse\s+salariale|salaires?\s+bruts?|charges?\s+de\s+personnel)\s*[:\s]*([\d\s,\.]+)\s*(?:FCFA|XOF|F\.?CFA)?", re.I),
    "charges_sociales": re.compile(r"(?:charges?\s+sociales?|cotisations?\s+sociales?)\s*[:\s]*([\d\s,\.]+)", re.I),
    "nb_formations": re.compile(r"(?:formations?|sessions?\s+de\s+formation)\s*[:\s]*(\d+)", re.I),
}


def run_masse_salariale_check(
    df_fec: pd.DataFrame,
    social_content: Optional[bytes],
    social_filename: str,
) -> Dict[str, Any]:
    """
    Compare la masse salariale déclarée dans le bilan social
    avec les charges de personnel enregistrées dans le FEC (comptes 66x).
    """
    fec_masse_salariale = _fec_accounts_total(df_fec, PERSONNEL_ACCOUNTS, "debit")

    if not social_content:
        return {
            "coherence_score": 1.0,
            "risk_level": "VERT",
            "masse_salariale_document": None,
            "masse_salariale_fec": round(fec_masse_salariale, 2),
            "ecart": 0.0,
            "ecart_pct": 0.0,
            "interpretation": "Aucun bilan social fourni.",
        }

    extracted = extract_document(social_content, social_filename)
    text = extracted["text_preview"] + " " + " ".join(
        [a["context"] for a in extracted["amounts_found"]]
    )

    # Extraction des métriques RH
    metrics = {}
    for key, pattern in SOCIAL_PATTERNS.items():
        m = pattern.search(text)
        if m:
            try:
                raw = m.group(1).strip().replace(" ", "").replace(",", ".")
                metrics[key] = float(raw)
            except (ValueError, IndexError):
                metrics[key] = None
        else:
            metrics[key] = None

    # Masse salariale depuis les montants textuels
    masse_salariale_doc = metrics.get("masse_salariale")
    if not masse_salariale_doc:
        sal_amounts = [a["value"] for a in extracted["amounts_found"]
                       if any(k in a["context"].lower() for k in ["salarial", "personnel", "salaire"])]
        masse_salariale_doc = max(sal_amounts) if sal_amounts else None

    ecart = round(abs((masse_salariale_doc or 0) - fec_masse_salariale), 2)
    ecart_pct = round(ecart / max(masse_salariale_doc or 1, fec_masse_salariale, 1) * 100, 1)

    risk_level = "VERT"
    if masse_salariale_doc and ecart_pct > 10:
        risk_level = "ROUGE" if ecart_pct > 25 else "ORANGE"

    score_map = {"VERT": 1.0, "ORANGE": 0.5, "ROUGE": 0.0}
    coherence_score = round(max(0.0, 1.0 - ecart_pct / 100), 2) if masse_salariale_doc else 1.0

    # Détail par sous-compte 66x
    detail_66x = []
    if "CompteNum" in df_fec.columns:
        mask = df_fec["CompteNum"].apply(lambda c: any(str(c).startswith(p) for p in PERSONNEL_ACCOUNTS))
        sub = df_fec[mask].groupby("CompteNum").agg(
            total_debit=("Debit", "sum"), nb=("Debit", "count")
        ).reset_index()
        for _, row in sub.iterrows():
            detail_66x.append({
                "account": str(row["CompteNum"]),
                "total_debit": round(float(row["total_debit"]), 2),
                "nb_ecritures": int(row["nb"]),
            })

    if risk_level == "VERT":
        ms_doc_fmt = f"{masse_salariale_doc:,.0f}" if masse_salariale_doc is not None else "N/A"
        interpretation = f"Masse salariale cohérente : bilan social {ms_doc_fmt} ≈ FEC {fec_masse_salariale:,.0f} FCFA."
    else:
        ms_doc_fmt = f"{masse_salariale_doc:,.0f}" if masse_salariale_doc is not None else "N/A"
        interpretation = (
            f"ÉCART {'CRITIQUE' if risk_level == 'ROUGE' else 'MODÉRÉ'} : "
            f"Bilan social {ms_doc_fmt} vs FEC {fec_masse_salariale:,.0f} FCFA (écart {ecart_pct}%)."
        )

    return {
        "coherence_score": coherence_score,
        "risk_level": risk_level,
        "masse_salariale_document": masse_salariale_doc,
        "masse_salariale_fec": round(fec_masse_salariale, 2),
        "ecart": ecart,
        "ecart_pct": ecart_pct,
        "effectif_declare": metrics.get("effectif_total"),
        "charges_sociales_doc": metrics.get("charges_sociales"),
        "detail_personnel_fec": detail_66x,
        "interpretation": interpretation,
    }


# ─── 3. Plan de passation des marchés ────────────────────────────────────────

MARCHE_COLS_BUDGET = ["montant", "valeur", "prix", "budget"]
MARCHE_COLS_OBJECT = ["objet", "designation", "libelle", "description", "marche"]


def _parse_marches_table(tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Tente d'extraire le tableau des marchés."""
    for df in tables:
        if df is None or df.empty or len(df) < 2:
            continue
        cols_lower = [str(c).lower() for c in df.columns]
        montant_col = next((df.columns[i] for i, c in enumerate(cols_lower)
                            if any(k in c for k in MARCHE_COLS_BUDGET)), None)
        if montant_col:
            result = df.copy()
            result["_montant"] = (
                result[montant_col].astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
                .fillna(0.0)
            )
            result = result[result["_montant"] > 0]
            if not result.empty:
                return result
    return None


def run_marches_check(
    df_fec: pd.DataFrame,
    marches_content: Optional[bytes],
    marches_filename: str,
) -> Dict[str, Any]:
    """
    Compare les montants du plan de passation des marchés
    avec les factures fournisseurs dans le FEC (crédits 40x + débits 60x).
    """
    fec_fournisseurs = _fec_accounts_total(df_fec, FOURNISSEURS_ACCOUNTS, "credit")
    fec_achats = _fec_accounts_total(df_fec, ACHATS_ACCOUNTS, "debit")
    fec_total_achats = round(fec_fournisseurs + fec_achats, 2)

    if not marches_content:
        return {
            "coherence_score": 1.0,
            "risk_level": "VERT",
            "total_marches_doc": 0.0,
            "total_achats_fec": fec_total_achats,
            "ecart": 0.0,
            "ecart_pct": 0.0,
            "nb_marches": 0,
            "marches_compares": [],
            "interpretation": "Aucun plan de passation des marchés fourni.",
        }

    extracted = extract_document(marches_content, marches_filename)
    tables = extracted["tables"]
    amounts = extracted["amounts_found"]

    marches_df = _parse_marches_table(tables)
    total_marches_doc = 0.0
    marches_list = []

    if marches_df is not None:
        total_marches_doc = float(marches_df["_montant"].sum())
        cols_lower = {c.lower(): c for c in marches_df.columns}
        objet_col = next((cols_lower[k] for k in cols_lower if any(x in k for x in MARCHE_COLS_OBJECT)), None)
        for _, row in marches_df.head(20).iterrows():
            entry = {"montant": round(float(row["_montant"]), 2)}
            if objet_col:
                entry["objet"] = str(row[objet_col])[:100]
            marches_list.append(entry)
    else:
        marche_amounts = [a["value"] for a in amounts
                          if any(k in a["context"].lower() for k in ["marché", "marche", "contrat", "prestataire"])]
        total_marches_doc = sum(marche_amounts)

    ecart = round(abs(total_marches_doc - fec_total_achats), 2)
    ecart_pct = round(ecart / max(total_marches_doc, 1) * 100, 1) if total_marches_doc > 0 else 0.0

    risk_level = "VERT"
    if total_marches_doc > 0 and ecart_pct > 15:
        risk_level = "ROUGE" if ecart_pct > 30 else "ORANGE"

    coherence_score = round(max(0.0, 1.0 - ecart_pct / 100), 2) if total_marches_doc > 0 else 1.0

    tranches = {"< 5M": 0, "5–50M": 0, "50–500M": 0, "> 500M": 0}
    for m in marches_list:
        v = m["montant"]
        if v < 5_000_000:
            tranches["< 5M"] += 1
        elif v < 50_000_000:
            tranches["5–50M"] += 1
        elif v < 500_000_000:
            tranches["50–500M"] += 1
        else:
            tranches["> 500M"] += 1

    return {
        "coherence_score": coherence_score,
        "risk_level": risk_level,
        "total_marches_doc": round(total_marches_doc, 2),
        "total_achats_fec": fec_total_achats,
        "ecart": ecart,
        "ecart_pct": ecart_pct,
        "nb_marches": len(marches_list),
        "marches_compares": marches_list[:15],
        "tranches_montant": tranches,
        "interpretation": (
            "Cohérence marchés/FEC validée." if risk_level == "VERT" else
            f"{'ALERTE' if risk_level == 'ROUGE' else 'ATTENTION'} : "
            f"Marchés déclarés {total_marches_doc:,.0f} vs achats FEC {fec_total_achats:,.0f} FCFA "
            f"(écart {ecart_pct}%)."
        ),
    }


# ─── 4. Rapport d'activités ──────────────────────────────────────────────────

def run_activites_check(
    df_fec: pd.DataFrame,
    activites_content: Optional[bytes],
    activites_filename: str,
) -> Dict[str, Any]:
    """
    Extrait les montants cités dans le rapport d'activités
    et tente de les retrouver dans le FEC.
    """
    if not activites_content:
        return {
            "coherence_score": 1.0,
            "risk_level": "VERT",
            "amounts_extracted": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "match_rate_pct": 100.0,
            "matched": [],
            "unmatched": [],
            "interpretation": "Aucun rapport d'activités fourni.",
        }

    extracted = extract_document(activites_content, activites_filename)
    amounts = extracted["amounts_found"]

    if not amounts:
        return {
            "coherence_score": 1.0,
            "risk_level": "VERT",
            "amounts_extracted": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "match_rate_pct": 100.0,
            "matched": [],
            "unmatched": [],
            "interpretation": "Aucun montant extrait du rapport d'activités.",
        }

    # Totaux FEC pour comparaison rapide
    fec_by_class = _fec_totals_by_class(df_fec)
    fec_total_charges = fec_by_class.get("6", {}).get("total_debit", 0)
    fec_total_produits = fec_by_class.get("7", {}).get("total_credit", 0)

    matched = []
    unmatched = []

    for amt in amounts[:30]:
        v = amt["value"]
        # Chercher dans le FEC un montant proche (±5%)
        fec_match = None
        if "Debit" in df_fec.columns:
            close = df_fec[abs(df_fec["Debit"] - v) / max(v, 1) < 0.05]
            if not close.empty:
                row = close.iloc[0]
                fec_match = {
                    "account": str(row.get("CompteNum", "")),
                    "label": str(row.get("EcritureLib", ""))[:80],
                    "fec_amount": float(row.get("Debit", 0)),
                }

        entry = {
            "amount_doc": round(v, 2),
            "context": amt["context"][:100],
        }
        if fec_match:
            matched.append({**entry, "fec_match": fec_match})
        else:
            unmatched.append(entry)

    match_rate = round(len(matched) / len(amounts) * 100, 1) if amounts else 100.0
    risk_level = "VERT" if match_rate >= 70 else ("ORANGE" if match_rate >= 40 else "ROUGE")
    coherence_score = round(match_rate / 100, 2)

    return {
        "coherence_score": coherence_score,
        "risk_level": risk_level,
        "amounts_extracted": len(amounts),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "match_rate_pct": match_rate,
        "matched": matched[:10],
        "unmatched": unmatched[:10],
        "fec_reference": {
            "total_charges": round(fec_total_charges, 2),
            "total_produits": round(fec_total_produits, 2),
        },
        "interpretation": (
            f"{len(amounts)} montant(s) extrait(s) du rapport d'activités — "
            f"{len(matched)} retrouvé(s) dans le FEC ({match_rate}%)."
        ),
    }


# ─── Orchestrateur ────────────────────────────────────────────────────────────

def run_ag_comparative_analysis(
    df_fec: pd.DataFrame,
    budget_content: Optional[bytes] = None,
    budget_filename: str = "budget.csv",
    social_content: Optional[bytes] = None,
    social_filename: str = "bilan_social.xlsx",
    marches_content: Optional[bytes] = None,
    marches_filename: str = "marches.xlsx",
    activites_content: Optional[bytes] = None,
    activites_filename: str = "rapport_activites.pdf",
) -> Dict[str, Any]:
    """
    Orchestrateur principal — exécute les 4 analyses AG disponibles.
    """
    results: Dict[str, Any] = {}

    # Toujours exécuter les 4 modules — les fonctions gèrent le cas content=None
    for key, func, content, filename in [
        ("budget_execution", run_budget_execution_analysis, budget_content, budget_filename),
        ("masse_salariale", run_masse_salariale_check, social_content, social_filename),
        ("marches", run_marches_check, marches_content, marches_filename),
        ("activites", run_activites_check, activites_content, activites_filename),
    ]:
        try:
            results[key] = func(df_fec, content, filename)
        except Exception as e:
            logger.error(f"Erreur module AG '{key}': {e}")
            results[key] = {"coherence_score": 1.0, "risk_level": "VERT", "error": str(e)}

    # Score global (0.0 – 1.0)
    scores = [r.get("coherence_score", 1.0) for r in results.values()]
    coherence_score = round(sum(scores) / len(scores), 3) if scores else 1.0

    if coherence_score >= 0.75:
        global_level = "VERT"
    elif coherence_score >= 0.45:
        global_level = "ORANGE"
    else:
        global_level = "ROUGE"

    results["global"] = {
        "risk_level": global_level,
        "coherence_score": coherence_score,
        "modules_run": [k for k in results if k != "global"],
        "interpretation": _global_ag_interpretation(global_level, coherence_score, list(results.keys())),
    }

    return results


def _global_ag_interpretation(level: str, score: float, modules: List[str]) -> str:
    modules_str = ", ".join(modules)
    if level == "VERT":
        return (f"Cohérence AG validée (score {score}/100). "
                f"Les documents comparés ({modules_str}) sont cohérents avec le FEC.")
    elif level == "ORANGE":
        return (f"Cohérence AG modérée (score {score}/100). "
                f"Des écarts ont été relevés dans certains documents AG — revue recommandée.")
    else:
        return (f"ALERTE COHÉRENCE AG (score {score}/100). "
                f"Des incohérences significatives entre les documents AG et le FEC ont été détectées. "
                "Investigation approfondie requise avant la tenue de l'Assemblée Générale.")

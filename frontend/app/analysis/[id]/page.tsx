"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  FileText, Download, RefreshCw, CheckCircle,
  AlertTriangle, TrendingUp, Scale, Zap, BarChart2,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";
import { getAnalysis, downloadDocx, downloadXlsx } from "@/lib/api";
import Sidebar from "@/components/dashboard/Sidebar";
import RiskBadge from "@/components/dashboard/RiskBadge";
import ScoreGauge from "@/components/dashboard/ScoreGauge";
import toast from "react-hot-toast";

const BENFORD_EXPECTED = [30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6];
const BENFORD_LABELS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];

function ModuleCard({ title, icon: Icon, result, children }: any) {
  if (!result) return null;
  const level = result.risk_level || result.valid === false ? "ROUGE" : "VERT";
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-[#1e293b]" />
          <h3 className="text-sm font-semibold text-[#1e293b]">{title}</h3>
        </div>
        {result.risk_level && <RiskBadge level={result.risk_level} />}
      </div>
      {result.interpretation && (
        <p className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 mb-4">{result.interpretation}</p>
      )}
      {children}
    </div>
  );
}

export default function AnalysisDetailPage() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);

  const load = async () => {
    try {
      const res = await getAnalysis(id as string);
      setAnalysis(res.data);
      if (res.data.status === "RUNNING" || res.data.status === "PENDING") {
        setPolling(true);
      } else {
        setPolling(false);
      }
    } catch {
      toast.error("Analyse introuvable");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  useEffect(() => {
    if (!polling) return;
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [polling]);

  const handleDownload = async (format: "docx" | "xlsx") => {
    try {
      const fn = format === "docx" ? downloadDocx : downloadXlsx;
      const res = await fn(id as string);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `rapport_audit.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Rapport non disponible");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 ml-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#1e293b]" />
        </main>
      </div>
    );
  }

  if (!analysis) return null;

  const benfordChartData = analysis.benford_result?.distribution
    ? Object.entries(analysis.benford_result.distribution).map(([digit, data]: any) => ({
        digit,
        expected: data.expected_pct,
        observed: data.observed_pct,
      }))
    : [];

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <main className="flex-1 ml-64 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b]">
              Rapport d'analyse #{(id as string).slice(0, 8).toUpperCase()}
            </h1>
            <p className="text-gray-500 text-sm mt-0.5">
              {new Date(analysis.created_at).toLocaleString("fr-FR")}
              {analysis.status !== "COMPLETED" && (
                <span className="ml-3 text-blue-600 animate-pulse font-medium text-xs">
                  {analysis.status === "RUNNING" ? "Analyse en cours..." : analysis.status}
                </span>
              )}
            </p>
          </div>
          {analysis.status === "COMPLETED" && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleDownload("docx")}
                className="flex items-center gap-2 btn-secondary text-sm"
              >
                <Download className="w-4 h-4" /> Word
              </button>
              <button
                onClick={() => handleDownload("xlsx")}
                className="flex items-center gap-2 btn-secondary text-sm"
              >
                <Download className="w-4 h-4" /> Excel
              </button>
            </div>
          )}
        </div>

        {/* Score global */}
        {analysis.status === "COMPLETED" && (
          <div className="card mb-6">
            <div className="flex items-center gap-8">
              <ScoreGauge score={analysis.risk_score || 0} riskLevel={analysis.risk_level || "ORANGE"} />
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-xl font-bold text-[#1e293b]">Score de confiance global</h2>
                  {analysis.risk_level && <RiskBadge level={analysis.risk_level} />}
                </div>
                {analysis.ai_synthesis && (
                  <p className="text-sm text-gray-600 leading-relaxed line-clamp-4">
                    {analysis.ai_synthesis}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {analysis.status === "RUNNING" && (
          <div className="card mb-6 flex flex-col items-center justify-center py-12">
            <RefreshCw className="w-12 h-12 text-[#1e293b] animate-spin mb-4" />
            <p className="text-[#1e293b] font-semibold">Analyse IA en cours...</p>
            <p className="text-sm text-gray-400 mt-1">
              Les algorithmes analysent vos données comptables. Actualisation automatique.
            </p>
          </div>
        )}

        {analysis.status === "COMPLETED" && (
          <div className="grid grid-cols-2 gap-6">
            {/* Vérification intrinsèque */}
            {analysis.intrinsic_check && (
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <Scale className="w-4 h-4 text-[#1e293b]" />
                  <h3 className="text-sm font-semibold text-[#1e293b]">Vérification Intrinsèque</h3>
                </div>
                <div className="space-y-3">
                  <div className={`flex items-center gap-2 p-3 rounded-lg ${
                    analysis.intrinsic_check.valid ? "bg-green-50" : "bg-red-50"
                  }`}>
                    {analysis.intrinsic_check.valid ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                    )}
                    <span className={`text-sm font-medium ${
                      analysis.intrinsic_check.valid ? "text-green-700" : "text-red-700"
                    }`}>
                      {analysis.intrinsic_check.valid ? "Équilibre Débit = Crédit validé" : "Déséquilibre détecté"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Total Débit</p>
                      <p className="font-semibold text-[#1e293b]">
                        {analysis.intrinsic_check.total_debit?.toLocaleString("fr-FR")} FCFA
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Total Crédit</p>
                      <p className="font-semibold text-[#1e293b]">
                        {analysis.intrinsic_check.total_credit?.toLocaleString("fr-FR")} FCFA
                      </p>
                    </div>
                  </div>
                  {!analysis.intrinsic_check.valid && (
                    <p className="text-xs text-red-600">
                      Écart : {analysis.intrinsic_check.difference?.toLocaleString("fr-FR")} FCFA
                      ({analysis.intrinsic_check.unbalanced_entries_count} écritures déséquilibrées)
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Loi de Benford */}
            {analysis.benford_result?.sufficient_data && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#1e293b]" />
                    <h3 className="text-sm font-semibold text-[#1e293b]">Loi de Benford</h3>
                  </div>
                  <RiskBadge level={analysis.benford_result.risk_level} />
                </div>
                <p className="text-xs text-gray-500 mb-3">
                  Conformité : <span className="font-semibold">{analysis.benford_result.conformity_score}%</span>
                  {" "}— p-value : {analysis.benford_result.p_value}
                </p>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={benfordChartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="digit" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip formatter={(v: any) => `${v}%`} />
                    <Bar dataKey="expected" name="Attendu" fill="#e2e8f0" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="observed" name="Observé" radius={[2, 2, 0, 0]}>
                      {benfordChartData.map((entry, i) => (
                        <Cell
                          key={i}
                          fill={Math.abs(entry.observed - entry.expected) > 5 ? "#dc2626" : "#1e293b"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Isolation Forest */}
            {analysis.isolation_forest_result?.sufficient_data && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-[#1e293b]" />
                    <h3 className="text-sm font-semibold text-[#1e293b]">Anomalies ML (Isolation Forest)</h3>
                  </div>
                  <RiskBadge level={analysis.isolation_forest_result.risk_level} />
                </div>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-[#1e293b]">
                      {analysis.isolation_forest_result.anomalies_detected}
                    </p>
                    <p className="text-xs text-gray-500">Anomalies</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-[#1e293b]">
                      {analysis.isolation_forest_result.anomaly_rate_pct}%
                    </p>
                    <p className="text-xs text-gray-500">Taux</p>
                  </div>
                </div>
                {analysis.isolation_forest_result.top_anomalies?.slice(0, 3).map((a: any, i: number) => (
                  <div key={i} className="text-xs text-gray-600 border-l-2 border-red-300 pl-3 mb-2">
                    <span className="font-medium">{a.account || "?"}</span>
                    {" "}{a.label && `— ${a.label.slice(0, 50)}`}
                    <span className="ml-2 text-gray-400">{a.date}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Cycle Trésorerie */}
            {analysis.cycle_tresorerie_result && !analysis.cycle_tresorerie_result.error && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-[#1e293b]" />
                    <h3 className="text-sm font-semibold text-[#1e293b]">Cycle Trésorerie</h3>
                  </div>
                  <RiskBadge level={analysis.cycle_tresorerie_result.risk_level} />
                </div>
                <div className="grid grid-cols-3 gap-2 mb-3">
                  {Object.entries(analysis.cycle_tresorerie_result.breakdown || {}).map(([key, val]: any) => (
                    <div key={key} className="bg-gray-50 rounded-lg p-2 text-center">
                      <p className="text-lg font-bold text-[#1e293b]">{val}</p>
                      <p className="text-xs text-gray-400">
                        {key === "sans_libelle" ? "Sans libellé" :
                         key === "weekend" ? "Week-end" : "Montants ronds"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Cohérence SYSCOHADA */}
            {analysis.coherence_check_result && (
              <div className="card col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Scale className="w-4 h-4 text-[#1e293b]" />
                    <h3 className="text-sm font-semibold text-[#1e293b]">Cohérence des États Financiers SYSCOHADA</h3>
                  </div>
                  <RiskBadge level={analysis.coherence_check_result.risk_level} />
                </div>
                <p className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 mb-4">
                  {analysis.coherence_check_result.interpretation}
                </p>

                {/* 4 sous-modules en grille */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Soldes normaux */}
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-[#1e293b]">Soldes normaux SYSCOHADA</p>
                      <RiskBadge level={analysis.coherence_check_result.soldes_normaux?.risk_level || "VERT"} />
                    </div>
                    <p className="text-xs text-gray-500 mb-2">
                      {analysis.coherence_check_result.soldes_normaux?.anomalies_count || 0} compte(s) avec signe anormal
                      {" sur "}
                      {analysis.coherence_check_result.soldes_normaux?.accounts_checked || 0} vérifiés
                    </p>
                    {analysis.coherence_check_result.soldes_normaux?.anomalies?.slice(0, 3).map((a: any, i: number) => (
                      <div key={i} className="text-xs text-red-600 border-l-2 border-red-300 pl-2 mb-1 truncate" title={a.description}>
                        {a.account} — {a.description}
                      </div>
                    ))}
                  </div>

                  {/* Résultat */}
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-[#1e293b]">Cohérence du résultat net</p>
                      <RiskBadge level={analysis.coherence_check_result.resultat_coherence?.risk_level || "VERT"} />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-gray-50 rounded p-2">
                        <p className="text-gray-400">Produits (Cl.7)</p>
                        <p className="font-semibold text-[#1e293b]">
                          {(analysis.coherence_check_result.resultat_coherence?.produits_cl7 || 0).toLocaleString("fr-FR")}
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded p-2">
                        <p className="text-gray-400">Charges (Cl.6)</p>
                        <p className="font-semibold text-[#1e293b]">
                          {(analysis.coherence_check_result.resultat_coherence?.charges_cl6 || 0).toLocaleString("fr-FR")}
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded p-2">
                        <p className="text-gray-400">Résultat FEC</p>
                        <p className={`font-bold ${(analysis.coherence_check_result.resultat_coherence?.resultat_fec || 0) >= 0 ? "text-green-700" : "text-red-700"}`}>
                          {(analysis.coherence_check_result.resultat_coherence?.resultat_fec || 0).toLocaleString("fr-FR")}
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded p-2">
                        <p className="text-gray-400">Compte 13x</p>
                        <p className="font-semibold text-[#1e293b]">
                          {(analysis.coherence_check_result.resultat_coherence?.resultat_enregistre_13x || 0).toLocaleString("fr-FR")}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Équilibre bilan */}
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-[#1e293b]">Équilibre du bilan (Actif = Passif)</p>
                      <RiskBadge level={analysis.coherence_check_result.equilibre_bilan?.risk_level || "VERT"} />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-blue-50 rounded p-2">
                        <p className="text-blue-500">Total Actif</p>
                        <p className="font-bold text-[#1e293b]">
                          {(analysis.coherence_check_result.equilibre_bilan?.total_actif || 0).toLocaleString("fr-FR")}
                        </p>
                      </div>
                      <div className="bg-purple-50 rounded p-2">
                        <p className="text-purple-500">Total Passif</p>
                        <p className="font-bold text-[#1e293b]">
                          {(analysis.coherence_check_result.equilibre_bilan?.total_passif || 0).toLocaleString("fr-FR")}
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">
                      Écart : {(analysis.coherence_check_result.equilibre_bilan?.ecart || 0).toLocaleString("fr-FR")}
                      {" "}({analysis.coherence_check_result.equilibre_bilan?.ecart_pct || 0}%)
                    </p>
                  </div>

                  {/* Doublons */}
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-[#1e293b]">Doublons d'écritures</p>
                      <RiskBadge level={analysis.coherence_check_result.doublons?.risk_level || "VERT"} />
                    </div>
                    <p className="text-xs text-gray-500 mb-2">
                      {analysis.coherence_check_result.doublons?.duplicates_count || 0} doublon(s) détecté(s)
                      {" ("}
                      {analysis.coherence_check_result.doublons?.exact_duplicates || 0} exact(s)
                      {")"}
                    </p>
                    {analysis.coherence_check_result.doublons?.duplicates?.slice(0, 2).map((d: any, i: number) => (
                      <div key={i} className={`text-xs border-l-2 pl-2 mb-1 ${d.severity === "ROUGE" ? "border-red-300 text-red-600" : "border-amber-300 text-amber-700"}`}>
                        {d.type} — {d.account} {d.date ? `(${d.date})` : ""}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Réconciliation Balance Générale */}
            {analysis.balance_reconciliation_result && !analysis.balance_reconciliation_result.error && (
              <div className="card col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-[#1e293b]" />
                    <h3 className="text-sm font-semibold text-[#1e293b]">Réconciliation Balance Générale ↔ FEC</h3>
                  </div>
                  <RiskBadge level={analysis.balance_reconciliation_result.risk_level} />
                </div>
                <p className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 mb-4">
                  {analysis.balance_reconciliation_result.interpretation}
                </p>
                <div className="grid grid-cols-4 gap-3 mb-4 text-xs">
                  <div className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-gray-400">Comptes FEC</p>
                    <p className="font-bold text-[#1e293b]">{analysis.balance_reconciliation_result.fec_summary?.accounts || 0}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-gray-400">Comptes Balance</p>
                    <p className="font-bold text-[#1e293b]">{analysis.balance_reconciliation_result.balance_summary?.accounts || 0}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-gray-400">Écarts trouvés</p>
                    <p className={`font-bold ${analysis.balance_reconciliation_result.discrepancies_count > 0 ? "text-red-600" : "text-green-700"}`}>
                      {analysis.balance_reconciliation_result.discrepancies_count}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-gray-400">Écarts ROUGE</p>
                    <p className="font-bold text-red-600">{analysis.balance_reconciliation_result.rouge_discrepancies || 0}</p>
                  </div>
                </div>
                {analysis.balance_reconciliation_result.discrepancies?.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-gray-100 text-gray-500">
                          <th className="text-left py-1.5 px-2">Compte</th>
                          <th className="text-left py-1.5 px-2">Type d'écart</th>
                          <th className="text-right py-1.5 px-2">Solde FEC</th>
                          <th className="text-right py-1.5 px-2">Solde Balance</th>
                          <th className="text-right py-1.5 px-2">Écart</th>
                          <th className="text-center py-1.5 px-2">Sévérité</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysis.balance_reconciliation_result.discrepancies.slice(0, 10).map((d: any, i: number) => (
                          <tr key={i} className="border-b border-gray-50 hover:bg-gray-50/50">
                            <td className="py-1.5 px-2 font-mono font-medium text-[#1e293b]">{d.account}</td>
                            <td className="py-1.5 px-2 text-gray-500">{d.flag}</td>
                            <td className="py-1.5 px-2 text-right">{d.fec?.solde_net?.toLocaleString("fr-FR")}</td>
                            <td className="py-1.5 px-2 text-right">{d.balance?.solde_net?.toLocaleString("fr-FR")}</td>
                            <td className="py-1.5 px-2 text-right font-semibold text-red-600">
                              {d.ecart_solde?.toLocaleString("fr-FR")}
                            </td>
                            <td className="py-1.5 px-2 text-center">
                              <RiskBadge level={d.severity} showDot={false} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Revue analytique */}
            {analysis.analytical_review?.comparison_n_vs_n1 && (
              <div className="card col-span-2">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-4 h-4 text-[#1e293b]" />
                  <h3 className="text-sm font-semibold text-[#1e293b]">
                    Revue Analytique N vs N-1
                  </h3>
                </div>
                <p className="text-xs text-gray-500 mb-3">
                  {analysis.analytical_review.comparison_n_vs_n1.deviations_count} déviations significatives (seuil ≥ {analysis.analytical_review.comparison_n_vs_n1.threshold_pct}%)
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-100 text-gray-500">
                        <th className="text-left py-1.5 px-2">Compte</th>
                        <th className="text-right py-1.5 px-2">N</th>
                        <th className="text-right py-1.5 px-2">N-1</th>
                        <th className="text-right py-1.5 px-2">Variation</th>
                        <th className="text-center py-1.5 px-2">Sévérité</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.analytical_review.comparison_n_vs_n1.deviations?.slice(0, 8).map((d: any, i: number) => (
                        <tr key={i} className="border-b border-gray-50">
                          <td className="py-1.5 px-2 font-mono font-medium text-[#1e293b]">{d.account}</td>
                          <td className="py-1.5 px-2 text-right">{d.solde_n?.toLocaleString("fr-FR")}</td>
                          <td className="py-1.5 px-2 text-right text-gray-400">{d.solde_n1?.toLocaleString("fr-FR")}</td>
                          <td className="py-1.5 px-2 text-right font-semibold text-red-600">+{d.variation_pct}%</td>
                          <td className="py-1.5 px-2 text-center">
                            <RiskBadge level={d.severity} showDot={false} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Scores par module */}
            <div className="card col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <BarChart2 className="w-4 h-4 text-[#1e293b]" />
                <h3 className="text-sm font-semibold text-[#1e293b]">Scores par module d'analyse</h3>
              </div>
              {(() => {
                const RISK_SCORE: Record<string, number> = { VERT: 95, ORANGE: 55, ROUGE: 15 };
                const RISK_COLOR: Record<string, string> = { VERT: "#22c55e", ORANGE: "#f97316", ROUGE: "#ef4444" };
                const modules = [
                  { name: "Vérification intrinsèque", level: analysis.intrinsic_check?.valid === false ? "ROUGE" : analysis.intrinsic_check ? "VERT" : null },
                  { name: "Cohérence SYSCOHADA", level: analysis.coherence_check_result?.risk_level ?? null },
                  { name: "Loi de Benford", level: analysis.benford_result?.risk_level ?? null },
                  { name: "Isolation Forest", level: analysis.isolation_forest_result?.risk_level ?? null },
                  { name: "Revue analytique", level: analysis.analytical_review?.risk_level ?? null },
                  { name: "Cycle ventes", level: analysis.cycle_ventes_result?.risk_level ?? null },
                  { name: "Cycle trésorerie", level: analysis.cycle_tresorerie_result?.risk_level ?? null },
                ].filter((m) => m.level !== null);
                const barData = modules.map((m) => ({
                  name: m.name,
                  score: RISK_SCORE[m.level!] ?? 50,
                  fill: RISK_COLOR[m.level!] ?? "#64748b",
                }));
                return (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={barData} layout="vertical" margin={{ left: 8, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                      <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: "#94a3b8" }} unit="%" />
                      <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 11, fill: "#475569" }} />
                      <Tooltip
                        formatter={(v: number, _: string, props: any) => [
                          `${v}% — ${modules.find(m => m.name === props.payload.name)?.level}`,
                          "Score",
                        ]}
                      />
                      <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                        {barData.map((d, i) => (
                          <Cell key={i} fill={d.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                );
              })()}
            </div>

            {/* Note de synthèse complète */}
            {analysis.ai_synthesis && (
              <div className="card col-span-2">
                <h3 className="text-sm font-semibold text-[#1e293b] mb-3">Note de synthèse IA</h3>
                <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {analysis.ai_synthesis}
                </div>
              </div>
            )}

            {/* Anomalies détectées */}
            {analysis.anomalies?.length > 0 && (
              <div className="card col-span-2">
                <h3 className="text-sm font-semibold text-[#1e293b] mb-4">
                  Anomalies détectées ({analysis.anomalies.length})
                </h3>
                <div className="space-y-2">
                  {analysis.anomalies.map((a: any) => (
                    <div key={a.id} className={`flex items-start gap-3 p-3 rounded-lg ${
                      a.severity === "ROUGE" ? "bg-red-50 border border-red-100" :
                      a.severity === "ORANGE" ? "bg-amber-50 border border-amber-100" :
                      "bg-green-50 border border-green-100"
                    }`}>
                      <RiskBadge level={a.severity} />
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-gray-800">{a.module}</p>
                        <p className="text-xs text-gray-600 mt-0.5">{a.description}</p>
                        {a.affected_account && (
                          <p className="text-xs text-gray-400 mt-0.5">Compte : {a.affected_account}</p>
                        )}
                      </div>
                      {a.amount && (
                        <span className="text-xs font-semibold text-gray-700">
                          {a.amount.toLocaleString("fr-FR")} FCFA
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

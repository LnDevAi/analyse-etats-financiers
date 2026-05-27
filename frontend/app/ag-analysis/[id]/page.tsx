"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  CheckCircle2, XCircle, AlertTriangle, Clock, Loader2,
  ChevronLeft, TrendingUp, Users, ShoppingCart, Activity,
  BarChart2, Target,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, PieChart, Pie, Cell, LineChart, Line,
} from "recharts";
import { getAGAnalysis } from "@/lib/api";
import toast from "react-hot-toast";

interface AGAnalysis {
  id: string;
  status: string;
  coherence_score: number | null;
  risk_level: string | null;
  ai_synthesis: string | null;
  budget_comparison: any;
  masse_salariale_check: any;
  marches_check: any;
  activites_check: any;
  created_at: string;
}

const RISK_COLORS: Record<string, string> = {
  VERT: "#22c55e",
  ORANGE: "#f97316",
  ROUGE: "#ef4444",
};

const RISK_BG: Record<string, string> = {
  VERT: "bg-green-500/20 text-green-400 border-green-500/30",
  ORANGE: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  ROUGE: "bg-red-500/20 text-red-400 border-red-500/30",
};

const CHART_COLORS = ["#3b82f6", "#22c55e", "#f97316", "#a855f7", "#06b6d4", "#eab308"];

const STATUS_LABEL: Record<string, string> = {
  PENDING: "En attente",
  RUNNING: "En cours",
  COMPLETED: "Terminée",
  FAILED: "Échouée",
};

function StatusBadge({ status }: { status: string }) {
  const icons: Record<string, React.ReactNode> = {
    PENDING: <Clock className="w-3.5 h-3.5" />,
    RUNNING: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    COMPLETED: <CheckCircle2 className="w-3.5 h-3.5" />,
    FAILED: <XCircle className="w-3.5 h-3.5" />,
  };
  const colors: Record<string, string> = {
    PENDING: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    RUNNING: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    COMPLETED: "bg-green-500/20 text-green-400 border-green-500/30",
    FAILED: "bg-red-500/20 text-red-400 border-red-500/30",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${colors[status]}`}>
      {icons[status]}
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

// ─── Budget Execution Charts ────────────────────────────────────────────────
function BudgetCharts({ data }: { data: any }) {
  if (!data?.comparaison_par_classe) return null;
  const classes = data.comparaison_par_classe as Record<string, any>;

  const barData = Object.entries(classes).map(([cls, vals]: [string, any]) => ({
    name: `Cl.${cls}`,
    "Prévu (budget)": Math.round((vals.budget_prevu ?? 0) / 1000),
    "Réalisé (doc)": Math.round((vals.realise_document ?? 0) / 1000),
    "Réalisé (FEC)": Math.round((vals.realise_fec ?? 0) / 1000),
  }));

  const pieData = barData.map((d, i) => ({
    name: d.name,
    value: Math.abs(d["Prévu (budget)"]),
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <div className="space-y-6">
      {/* Grouped bar: budget vs réalisé */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4 text-sm">
          Budget prévu vs réalisé par classe (milliers FCFA)
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData} barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              labelStyle={{ color: "#f1f5f9" }}
              formatter={(v: number) => [`${v.toLocaleString("fr-FR")} k FCFA`]}
            />
            <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
            <Bar dataKey="Prévu (budget)" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Réalisé (doc)" fill="#22c55e" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Réalisé (FEC)" fill="#f97316" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Pie: budget breakdown */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4 text-sm">
          Répartition budgétaire par classe (prévu)
        </h3>
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={{ stroke: "#475569" }}
            >
              {pieData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              formatter={(v: number) => [`${v.toLocaleString("fr-FR")} k FCFA`]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Écarts table */}
      {data.ecarts_significatifs?.length > 0 && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
          <p className="text-red-400 text-sm font-semibold mb-3">
            Écarts significatifs ({data.ecarts_significatifs.length})
          </p>
          <div className="space-y-2">
            {data.ecarts_significatifs.slice(0, 5).map((e: any, i: number) => (
              <div key={i} className="flex justify-between text-xs">
                <span className="text-white/70">Classe {e.classe}</span>
                <span className="text-red-400 font-mono">
                  {e.ecart_pct !== undefined ? `${e.ecart_pct.toFixed(1)}%` : e.detail}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Masse Salariale Charts ──────────────────────────────────────────────────
function MasseSalarialeCharts({ data }: { data: any }) {
  if (!data) return null;

  const fec = data.masse_salariale_fec ?? 0;
  const doc = data.masse_salariale_document ?? 0;
  const ecart = data.ecart_absolu ?? 0;

  const barData = [
    { name: "FEC (compte 66x)", value: Math.round(fec / 1000) },
    { name: "Document social", value: Math.round(doc / 1000) },
  ];

  const pieData = [
    { name: "Masse salariale FEC", value: Math.abs(Math.round(fec / 1000)), color: "#3b82f6" },
    { name: "Écart", value: Math.abs(Math.round(ecart / 1000)), color: ecart > 0 ? "#f97316" : "#22c55e" },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4 text-sm">
          Masse salariale — FEC vs document (milliers FCFA)
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={barData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <YAxis dataKey="name" type="category" width={130} tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              formatter={(v: number) => [`${v.toLocaleString("fr-FR")} k FCFA`]}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {barData.map((_, i) => (
                <Cell key={i} fill={i === 0 ? "#3b82f6" : "#22c55e"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "FEC (66x)", value: `${(fec / 1_000_000).toFixed(2)} M FCFA`, color: "text-blue-400" },
          { label: "Document", value: `${(doc / 1_000_000).toFixed(2)} M FCFA`, color: "text-green-400" },
          {
            label: "Écart",
            value: `${(data.ecart_pct ?? 0).toFixed(1)}%`,
            color: Math.abs(data.ecart_pct ?? 0) > 5 ? "text-red-400" : "text-green-400",
          },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
            <p className={`text-base font-bold ${color}`}>{value}</p>
            <p className="text-white/50 text-xs mt-0.5">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Marchés Charts ──────────────────────────────────────────────────────────
function MarchesCharts({ data }: { data: any }) {
  if (!data) return null;
  const marches: any[] = data.marches_compares ?? [];

  const barData = marches.slice(0, 8).map((m: any) => ({
    name: (m.libelle ?? m.marche_id ?? "—").slice(0, 20),
    "Montant marché": Math.round((m.montant_marche ?? 0) / 1000),
    "Payé (FEC)": Math.round((m.paye_fec ?? 0) / 1000),
  }));

  const ecartData = marches.slice(0, 8).map((m: any) => ({
    name: (m.libelle ?? m.marche_id ?? "—").slice(0, 16),
    ecart: Math.round(((m.montant_marche ?? 0) - (m.paye_fec ?? 0)) / 1000),
  }));

  return (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4 text-sm">
          Marchés — montant vs paiements FEC (milliers FCFA)
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData} barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              formatter={(v: number) => [`${v.toLocaleString("fr-FR")} k FCFA`]}
            />
            <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
            <Bar dataKey="Montant marché" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Payé (FEC)" fill="#22c55e" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Écarts bar (horizontal) */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4 text-sm">
          Soldes non décaissés par marché (milliers FCFA)
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={ecartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <YAxis dataKey="name" type="category" width={120} tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              formatter={(v: number) => [`${v.toLocaleString("fr-FR")} k FCFA`]}
            />
            <Bar dataKey="ecart" radius={[0, 4, 4, 0]}>
              {ecartData.map((d, i) => (
                <Cell key={i} fill={d.ecart > 0 ? "#f97316" : "#22c55e"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─── Activités Charts ────────────────────────────────────────────────────────
function ActivitesCharts({ data }: { data: any }) {
  if (!data) return null;
  const matches: any[] = data.montants_trouves_fec ?? [];

  const barData = matches.slice(0, 8).map((m: any) => ({
    name: (m.description ?? "—").slice(0, 20),
    "Montant rapport": Math.round((m.montant_rapport ?? 0) / 1000),
    "Montant FEC": Math.round((m.montant_fec ?? 0) / 1000),
  }));

  return (
    <div className="space-y-6">
      {barData.length > 0 ? (
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-4 text-sm">
            Montants rapport d'activités ↔ FEC (milliers FCFA)
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} angle={-15} textAnchor="end" height={50} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                formatter={(v: number) => [`${v.toLocaleString("fr-FR")} k FCFA`]}
              />
              <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
              <Bar dataKey="Montant rapport" fill="#a855f7" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Montant FEC" fill="#06b6d4" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="bg-white/5 border border-white/10 rounded-xl p-6 text-center">
          <p className="text-white/40 text-sm">Aucun montant corrélé entre le rapport et le FEC.</p>
        </div>
      )}

      {data.anomalies?.length > 0 && (
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-4">
          <p className="text-orange-400 text-sm font-semibold mb-2">
            Anomalies détectées ({data.anomalies.length})
          </p>
          <ul className="space-y-1">
            {data.anomalies.slice(0, 5).map((a: string, i: number) => (
              <li key={i} className="text-white/60 text-xs">• {a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─── Radar global ────────────────────────────────────────────────────────────
function GlobalRadar({ ag }: { ag: AGAnalysis }) {
  const moduleScores: Record<string, number> = {};
  if (ag.budget_comparison) moduleScores["Budget"] = (ag.budget_comparison.coherence_score ?? 0) * 100;
  if (ag.masse_salariale_check) moduleScores["Masse sal."] = (ag.masse_salariale_check.coherence_score ?? 0) * 100;
  if (ag.marches_check) moduleScores["Marchés"] = (ag.marches_check.coherence_score ?? 0) * 100;
  if (ag.activites_check) moduleScores["Activités"] = (ag.activites_check.coherence_score ?? 0) * 100;

  const radarData = Object.entries(moduleScores).map(([k, v]) => ({ subject: k, score: Math.round(v) }));
  if (radarData.length < 2) return null;

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-5">
      <h3 className="text-white font-semibold mb-4 text-sm flex items-center gap-2">
        <Target className="w-4 h-4 text-blue-400" />
        Cohérence par module
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 12 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 10 }} />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.35}
          />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            formatter={(v: number) => [`${v}%`, "Score"]}
          />
          <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────
export default function AGAnalysisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [ag, setAg] = useState<AGAnalysis | null>(null);
  const [tab, setTab] = useState<"budget" | "social" | "marches" | "activites">("budget");

  const fetch = useCallback(async () => {
    try {
      const res = await getAGAnalysis(id);
      setAg(res.data);
    } catch {
      toast.error("Erreur de chargement");
    }
  }, [id]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  // Poll while running
  useEffect(() => {
    if (!ag || ag.status === "COMPLETED" || ag.status === "FAILED") return;
    const interval = setInterval(fetch, 4000);
    return () => clearInterval(interval);
  }, [ag, fetch]);

  if (!ag) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  const tabs = [
    { key: "budget", label: "Budget", icon: TrendingUp, available: !!ag.budget_comparison },
    { key: "social", label: "Bilan social", icon: Users, available: !!ag.masse_salariale_check },
    { key: "marches", label: "Marchés", icon: ShoppingCart, available: !!ag.marches_check },
    { key: "activites", label: "Activités", icon: Activity, available: !!ag.activites_check },
  ] as const;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push("/ag-analysis")}
          className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-white">
            Analyse AG — {new Date(ag.created_at).toLocaleDateString("fr-FR", {
              day: "2-digit", month: "long", year: "numeric",
            })}
          </h1>
        </div>
        <StatusBadge status={ag.status} />
      </div>

      {/* Running state */}
      {ag.status === "RUNNING" && (
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
          <p className="text-blue-300 text-sm">Analyse en cours — actualisation automatique…</p>
        </div>
      )}

      {/* Failed state */}
      {ag.status === "FAILED" && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-400" />
          <p className="text-red-300 text-sm">L'analyse a échoué. Veuillez relancer une nouvelle analyse.</p>
        </div>
      )}

      {ag.status === "COMPLETED" && (
        <>
          {/* Score header */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="col-span-2 bg-white/5 border border-white/10 rounded-xl p-5 flex items-center gap-4">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold"
                style={{
                  background: `conic-gradient(${RISK_COLORS[ag.risk_level ?? ""] ?? "#64748b"} ${(ag.coherence_score ?? 0) * 360}deg, #1e293b 0deg)`,
                }}
              >
                <div className="w-12 h-12 rounded-full bg-[#0f172a] flex items-center justify-center">
                  <span className="text-white text-sm font-bold">
                    {Math.round((ag.coherence_score ?? 0) * 100)}%
                  </span>
                </div>
              </div>
              <div>
                <p className="text-white font-bold text-lg">Score global</p>
                <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium border mt-1 ${RISK_BG[ag.risk_level ?? ""] ?? ""}`}>
                  {ag.risk_level ?? "—"}
                </span>
              </div>
            </div>
            {tabs.filter((t) => t.available).map(({ key, label, icon: Icon }) => {
              const moduleData = {
                budget: ag.budget_comparison,
                social: ag.masse_salariale_check,
                marches: ag.marches_check,
                activites: ag.activites_check,
              }[key];
              const score = moduleData?.coherence_score ?? null;
              return (
                <div key={key} className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="w-4 h-4 text-white/40" />
                    <p className="text-white/50 text-xs">{label}</p>
                  </div>
                  <p className="text-white text-xl font-bold">
                    {score !== null ? `${Math.round(score * 100)}%` : "—"}
                  </p>
                  {moduleData?.risk_level && (
                    <span className={`text-xs font-medium ${RISK_COLORS[moduleData.risk_level] ? "" : ""}`}
                      style={{ color: RISK_COLORS[moduleData.risk_level] }}>
                      {moduleData.risk_level}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Radar */}
          <GlobalRadar ag={ag} />

          {/* AI synthesis */}
          {ag.ai_synthesis && (
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-5">
              <p className="text-blue-300 text-xs font-semibold mb-2 uppercase tracking-wide">
                Synthèse IA
              </p>
              <p className="text-white/80 text-sm leading-relaxed">{ag.ai_synthesis}</p>
            </div>
          )}

          {/* Tabs */}
          <div>
            <div className="flex gap-1 bg-white/5 rounded-lg p-1 mb-5 w-fit">
              {tabs.map(({ key, label, icon: Icon, available }) => (
                <button
                  key={key}
                  onClick={() => available && setTab(key as any)}
                  disabled={!available}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    tab === key
                      ? "bg-white/15 text-white"
                      : available
                      ? "text-white/50 hover:text-white hover:bg-white/10"
                      : "text-white/20 cursor-not-allowed"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </button>
              ))}
            </div>

            {tab === "budget" && <BudgetCharts data={ag.budget_comparison} />}
            {tab === "social" && <MasseSalarialeCharts data={ag.masse_salariale_check} />}
            {tab === "marches" && <MarchesCharts data={ag.marches_check} />}
            {tab === "activites" && <ActivitesCharts data={ag.activites_check} />}
          </div>
        </>
      )}
    </div>
  );
}

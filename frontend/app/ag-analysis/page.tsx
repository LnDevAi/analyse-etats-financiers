"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  FolderOpen, Plus, ChevronRight, Loader2, CheckCircle2,
  AlertTriangle, XCircle, Clock, FileText, BarChart2,
} from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, Legend,
} from "recharts";
import { listDocuments, listAGAnalyses, createAGAnalysis } from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";

interface Document {
  id: string;
  original_filename: string;
  document_type: string;
  created_at: string;
}

interface AGAnalysis {
  id: string;
  status: string;
  coherence_score: number | null;
  risk_level: string | null;
  created_at: string;
  fec_document_id: string;
  budget_document_id: string | null;
  social_document_id: string | null;
  marches_document_id: string | null;
  activites_document_id: string | null;
}

const RISK_COLORS: Record<string, string> = {
  VERT: "text-green-400",
  ORANGE: "text-orange-400",
  ROUGE: "text-red-400",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  PENDING: <Clock className="w-4 h-4 text-gray-400" />,
  RUNNING: <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />,
  COMPLETED: <CheckCircle2 className="w-4 h-4 text-green-400" />,
  FAILED: <XCircle className="w-4 h-4 text-red-400" />,
};

export default function AGAnalysisPage() {
  const router = useRouter();
  const [docs, setDocs] = useState<Document[]>([]);
  const [analyses, setAnalyses] = useState<AGAnalysis[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    fec_document_id: "",
    budget_document_id: "",
    social_document_id: "",
    marches_document_id: "",
    activites_document_id: "",
  });

  useEffect(() => {
    Promise.all([listDocuments(), listAGAnalyses()])
      .then(([docsRes, agRes]) => {
        setDocs(docsRes.data);
        setAnalyses(agRes.data);
      })
      .catch(() => toast.error("Erreur lors du chargement"));
  }, []);

  const fecDocs = docs.filter((d) => d.document_type === "FEC");
  const otherDocs = docs.filter((d) => d.document_type !== "FEC");

  const handleSubmit = async () => {
    if (!form.fec_document_id) {
      toast.error("Sélectionnez un document FEC");
      return;
    }
    setLoading(true);
    try {
      const payload: any = { fec_document_id: form.fec_document_id };
      if (form.budget_document_id) payload.budget_document_id = form.budget_document_id;
      if (form.social_document_id) payload.social_document_id = form.social_document_id;
      if (form.marches_document_id) payload.marches_document_id = form.marches_document_id;
      if (form.activites_document_id) payload.activites_document_id = form.activites_document_id;
      const res = await createAGAnalysis(payload);
      toast.success("Analyse AG lancée");
      setShowModal(false);
      router.push(`/ag-analysis/${res.data.id}`);
    } catch {
      toast.error("Erreur lors du lancement");
    } finally {
      setLoading(false);
    }
  };

  // Radar data for overview of completed analyses
  const radarData = analyses
    .filter((a) => a.status === "COMPLETED" && a.coherence_score !== null)
    .slice(0, 5)
    .map((a, i) => ({
      name: `AG ${i + 1}`,
      score: Math.round((a.coherence_score ?? 0) * 100),
    }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Analyse AG</h1>
          <p className="text-white/50 text-sm mt-1">
            Comparaison FEC ↔ documents d'Assemblée Générale
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Nouvelle analyse
        </button>
      </div>

      {/* Overview radar (only when there are completed analyses) */}
      {radarData.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-blue-400" />
            Scores de cohérence — dernières analyses
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Radar
                name="Score cohérence"
                dataKey="score"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
              />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#f1f5f9" }}
                formatter={(v: number) => [`${v}%`, "Score"]}
              />
              <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* List */}
      <div className="space-y-3">
        {analyses.length === 0 && (
          <div className="bg-white/5 border border-white/10 rounded-xl p-10 text-center">
            <FolderOpen className="w-10 h-10 text-white/20 mx-auto mb-3" />
            <p className="text-white/40 text-sm">Aucune analyse AG. Lancez votre première analyse.</p>
          </div>
        )}
        {analyses.map((ag) => (
          <Link
            key={ag.id}
            href={`/ag-analysis/${ag.id}`}
            className="flex items-center justify-between bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors group"
          >
            <div className="flex items-center gap-4">
              {STATUS_ICONS[ag.status] || STATUS_ICONS.PENDING}
              <div>
                <p className="text-white text-sm font-medium">
                  Analyse AG — {new Date(ag.created_at).toLocaleDateString("fr-FR", {
                    day: "2-digit", month: "short", year: "numeric",
                  })}
                </p>
                <p className="text-white/40 text-xs mt-0.5">
                  {[
                    ag.budget_document_id && "Budget",
                    ag.social_document_id && "Bilan social",
                    ag.marches_document_id && "Marchés",
                    ag.activites_document_id && "Activités",
                  ]
                    .filter(Boolean)
                    .join(" · ") || "FEC seul"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {ag.coherence_score !== null && (
                <div className="text-right">
                  <p className={`text-sm font-bold ${RISK_COLORS[ag.risk_level ?? ""] ?? "text-white"}`}>
                    {Math.round(ag.coherence_score * 100)}%
                  </p>
                  <p className="text-white/40 text-xs">cohérence</p>
                </div>
              )}
              <ChevronRight className="w-4 h-4 text-white/30 group-hover:text-white/60 transition-colors" />
            </div>
          </Link>
        ))}
      </div>

      {/* Create modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-lg p-6 space-y-5">
            <h2 className="text-white font-bold text-lg">Nouvelle analyse AG</h2>

            <div className="space-y-4">
              {/* FEC — required */}
              <div>
                <label className="text-white/70 text-xs font-medium mb-1 block">
                  FEC <span className="text-red-400">*</span>
                </label>
                <select
                  value={form.fec_document_id}
                  onChange={(e) => setForm({ ...form, fec_document_id: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="">-- Sélectionner un FEC --</option>
                  {fecDocs.map((d) => (
                    <option key={d.id} value={d.id}>{d.original_filename}</option>
                  ))}
                </select>
              </div>

              {/* Optional AG docs */}
              {[
                { key: "budget_document_id", label: "Rapport d'exécution budgétaire" },
                { key: "social_document_id", label: "Bilan social" },
                { key: "marches_document_id", label: "Plan de passation des marchés" },
                { key: "activites_document_id", label: "Rapport d'activités" },
              ].map(({ key, label }) => (
                <div key={key}>
                  <label className="text-white/70 text-xs font-medium mb-1 block">
                    {label} <span className="text-white/30">(optionnel)</span>
                  </label>
                  <select
                    value={(form as any)[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="">-- Aucun --</option>
                    {otherDocs.map((d) => (
                      <option key={d.id} value={d.id}>{d.original_filename}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 bg-white/5 hover:bg-white/10 text-white/70 rounded-lg py-2 text-sm transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg py-2 text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Lancer l'analyse
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

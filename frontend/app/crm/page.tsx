"use client";
import { useEffect, useState } from "react";
import {
  Plus, Search, ChevronRight, Building2, Phone, Mail,
  TrendingUp, Users, Target, Star,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import toast from "react-hot-toast";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const STAGES = [
  { key: "PROSPECT", label: "Prospect", color: "bg-gray-500" },
  { key: "QUALIFIÉ", label: "Qualifié", color: "bg-blue-500" },
  { key: "DÉMO", label: "Démo", color: "bg-purple-500" },
  { key: "NÉGOCIATION", label: "Négociation", color: "bg-orange-500" },
  { key: "GAGNÉ", label: "Gagné", color: "bg-green-500" },
  { key: "PERDU", label: "Perdu", color: "bg-red-500" },
];

const STAGE_COLORS: Record<string, string> = {
  PROSPECT: "#64748b",
  QUALIFIÉ: "#3b82f6",
  DÉMO: "#a855f7",
  NÉGOCIATION: "#f97316",
  GAGNÉ: "#22c55e",
  PERDU: "#ef4444",
};

const LIFECYCLE_BADGE: Record<string, string> = {
  PROSPECT: "bg-gray-500/20 text-gray-400",
  TRIAL: "bg-blue-500/20 text-blue-400",
  ACTIF: "bg-green-500/20 text-green-400",
  SUSPENDU: "bg-orange-500/20 text-orange-400",
  CHURNED: "bg-red-500/20 text-red-400",
};

interface CRMClient {
  id: string;
  company_name: string;
  sector: string | null;
  city: string | null;
  lifecycle_status: string;
  pipeline_stage: string;
  deal_value: number | null;
  health_score: number | null;
  last_contact_at: string | null;
  contacts: { full_name: string; email: string; phone: string; is_primary: boolean }[];
}

export default function CRMPage() {
  const [clients, setClients] = useState<CRMClient[]>([]);
  const [stats, setStats] = useState<Record<string, { count: number; deal_value: number }>>({});
  const [view, setView] = useState<"kanban" | "list">("kanban");
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [newForm, setNewForm] = useState({ company_name: "", sector: "", city: "", source: "" });

  const load = async () => {
    try {
      const [clientsRes, statsRes] = await Promise.all([
        api.get("/crm/clients"),
        api.get("/crm/pipeline/stats"),
      ]);
      setClients(clientsRes.data);
      setStats(statsRes.data);
    } catch {
      toast.error("Erreur de chargement");
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = clients.filter((c) =>
    c.company_name.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async () => {
    try {
      await api.post("/crm/clients", newForm);
      toast.success("Client créé");
      setShowNew(false);
      setNewForm({ company_name: "", sector: "", city: "", source: "" });
      load();
    } catch {
      toast.error("Erreur lors de la création");
    }
  };

  const barData = STAGES.map((s) => ({
    name: s.label,
    count: stats[s.key]?.count ?? 0,
    value: Math.round((stats[s.key]?.deal_value ?? 0) / 1000),
    fill: STAGE_COLORS[s.key],
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">CRM Clients</h1>
          <p className="text-white/50 text-sm mt-1">Pipeline commercial & suivi des relations</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-white/5 rounded-lg p-1">
            {(["kanban", "list"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${view === v ? "bg-white/15 text-white" : "text-white/40 hover:text-white"}`}
              >
                {v === "kanban" ? "Pipeline" : "Liste"}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" /> Nouveau client
          </button>
        </div>
      </div>

      {/* Pipeline chart */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h2 className="text-white font-semibold text-sm mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-blue-400" /> Valeur pipeline par stade (k FCFA)
        </h2>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={barData} barGap={4}>
            <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              formatter={(v: number, name: string) => [
                name === "value" ? `${v.toLocaleString("fr-FR")} k FCFA` : v,
                name === "value" ? "Valeur estimée" : "Clients",
              ]}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {barData.map((d, i) => <Cell key={i} fill={d.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher un client…"
          className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-white text-sm placeholder-white/30 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Kanban view */}
      {view === "kanban" && (
        <div className="grid grid-cols-3 xl:grid-cols-6 gap-3">
          {STAGES.map((stage) => {
            const stageClients = filtered.filter((c) => c.pipeline_stage === stage.key);
            return (
              <div key={stage.key} className="bg-white/5 border border-white/10 rounded-xl p-3">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-2 h-2 rounded-full ${stage.color}`} />
                  <span className="text-white/60 text-xs font-medium">{stage.label}</span>
                  <span className="ml-auto bg-white/10 text-white/50 text-xs px-1.5 rounded-full">
                    {stageClients.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {stageClients.map((c) => (
                    <Link
                      key={c.id}
                      href={`/crm/${c.id}`}
                      className="block bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg p-3 transition-colors"
                    >
                      <p className="text-white text-xs font-semibold truncate">{c.company_name}</p>
                      {c.sector && <p className="text-white/40 text-xs mt-0.5 truncate">{c.sector}</p>}
                      {c.deal_value && (
                        <p className="text-blue-400 text-xs mt-1 font-mono">
                          {(c.deal_value / 1000).toFixed(0)}k FCFA
                        </p>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* List view */}
      {view === "list" && (
        <div className="space-y-2">
          {filtered.map((c) => (
            <Link
              key={c.id}
              href={`/crm/${c.id}`}
              className="flex items-center justify-between bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors group"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-white/40" />
                </div>
                <div>
                  <p className="text-white font-medium text-sm">{c.company_name}</p>
                  <p className="text-white/40 text-xs mt-0.5">
                    {[c.sector, c.city].filter(Boolean).join(" · ") || "—"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${LIFECYCLE_BADGE[c.lifecycle_status] ?? ""}`}>
                  {c.lifecycle_status}
                </span>
                {c.deal_value && (
                  <span className="text-blue-400 text-xs font-mono">
                    {(c.deal_value / 1000).toFixed(0)}k FCFA
                  </span>
                )}
                <ChevronRight className="w-4 h-4 text-white/30 group-hover:text-white/60" />
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* New client modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-white font-bold">Nouveau client / prospect</h2>
            {[
              { key: "company_name", label: "Raison sociale *", placeholder: "Ex: Mairie de Ouagadougou" },
              { key: "sector", label: "Secteur", placeholder: "Ex: Collectivité, ONG, PME…" },
              { key: "city", label: "Ville", placeholder: "Ex: Ouagadougou" },
              { key: "source", label: "Source", placeholder: "Ex: Referral, Web, Démarchage…" },
            ].map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="text-white/60 text-xs mb-1 block">{label}</label>
                <input
                  value={(newForm as any)[key]}
                  onChange={(e) => setNewForm({ ...newForm, [key]: e.target.value })}
                  placeholder={placeholder}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 placeholder-white/20"
                />
              </div>
            ))}
            <div className="flex gap-3 pt-2">
              <button onClick={() => setShowNew(false)} className="flex-1 bg-white/5 hover:bg-white/10 text-white/70 rounded-lg py-2 text-sm">Annuler</button>
              <button onClick={handleCreate} className="flex-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-2 text-sm font-medium">Créer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

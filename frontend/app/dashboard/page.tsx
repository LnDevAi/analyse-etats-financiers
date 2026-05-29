"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileSearch, TrendingUp, AlertTriangle, CheckCircle,
  BarChart3, FileText, Plus,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { getDashboard } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import Sidebar from "@/components/dashboard/Sidebar";
import RiskBadge from "@/components/dashboard/RiskBadge";
import ScoreGauge from "@/components/dashboard/ScoreGauge";
import Link from "next/link";

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { router.replace("/auth/login"); return; }
    getDashboard()
      .then((res) => setStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  const kpiCards = stats ? [
    {
      title: "Analyses totales",
      value: stats.total_analyses,
      icon: BarChart3,
      color: "text-[#1e293b]",
      bg: "bg-slate-50",
    },
    {
      title: "Ce mois-ci",
      value: stats.analyses_this_month,
      icon: TrendingUp,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      title: "Score moyen",
      value: `${stats.avg_risk_score}/100`,
      icon: FileSearch,
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      title: "Alertes majeures",
      value: stats.high_risk_count,
      icon: AlertTriangle,
      color: "text-red-600",
      bg: "bg-red-50",
    },
  ] : [];

  const pieData = stats ? [
    { name: "Conforme", value: stats.low_risk_count, color: "#16a34a" },
    { name: "Vigilance", value: stats.medium_risk_count, color: "#d97706" },
    { name: "Alerte", value: stats.high_risk_count, color: "#dc2626" },
  ] : [];

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <main className="flex-1 md:ml-64 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b]">Tableau de bord</h1>
            <p className="text-gray-500 text-sm mt-0.5">
              Bienvenue, {user?.full_name} — {user?.role}
            </p>
          </div>
          <Link href="/documents" className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" />
            Nouvelle analyse
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#1e293b]" />
          </div>
        ) : (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-4 gap-4 mb-8">
              {kpiCards.map((card) => (
                <div key={card.title} className="card">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm text-gray-500">{card.title}</span>
                    <div className={`w-9 h-9 ${card.bg} rounded-lg flex items-center justify-center`}>
                      <card.icon className={`w-5 h-5 ${card.color}`} />
                    </div>
                  </div>
                  <p className="text-2xl font-bold text-[#1e293b]">{card.value}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-6 mb-8">
              {/* Distribution des risques */}
              <div className="card">
                <h3 className="text-sm font-semibold text-[#1e293b] mb-4">Distribution des risques</h3>
                {stats.total_analyses > 0 ? (
                  <>
                    <PieChart width={180} height={180}>
                      <Pie data={pieData} cx={90} cy={90} innerRadius={50} outerRadius={80} dataKey="value">
                        {pieData.map((entry, index) => (
                          <Cell key={index} fill={entry.color} />
                        ))}
                      </Pie>
                    </PieChart>
                    <div className="space-y-2 mt-2">
                      {pieData.map((item) => (
                        <div key={item.name} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ background: item.color }} />
                            <span className="text-gray-600">{item.name}</span>
                          </div>
                          <span className="font-semibold text-[#1e293b]">{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                    <BarChart3 className="w-10 h-10 mb-2 opacity-30" />
                    <p className="text-sm">Aucune analyse</p>
                  </div>
                )}
              </div>

              {/* Analyses récentes */}
              <div className="card col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-[#1e293b]">Analyses récentes</h3>
                  <Link href="/analysis" className="text-xs text-blue-600 hover:underline">
                    Voir tout
                  </Link>
                </div>
                {stats.recent_analyses?.length > 0 ? (
                  <div className="space-y-3">
                    {stats.recent_analyses.map((a: any) => (
                      <Link
                        key={a.id}
                        href={`/analysis/${a.id}`}
                        className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-[#1e293b]/10 rounded-lg flex items-center justify-center">
                            <FileText className="w-4 h-4 text-[#1e293b]" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-[#1e293b]">
                              {a.status === "COMPLETED" ? `Score ${a.risk_score}/100` : a.status}
                            </p>
                            <p className="text-xs text-gray-400">
                              {new Date(a.created_at).toLocaleDateString("fr-FR")}
                            </p>
                          </div>
                        </div>
                        {a.risk_level && <RiskBadge level={a.risk_level} />}
                        {a.status === "RUNNING" && (
                          <span className="text-xs text-blue-600 font-medium animate-pulse">En cours...</span>
                        )}
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                    <FileText className="w-10 h-10 mb-2 opacity-30" />
                    <p className="text-sm">Aucune analyse</p>
                    <Link href="/documents" className="text-sm text-blue-600 hover:underline mt-2">
                      Importer un FEC
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

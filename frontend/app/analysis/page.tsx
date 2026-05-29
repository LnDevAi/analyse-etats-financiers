"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { FileSearch, ChevronRight, BarChart3, AlertTriangle } from "lucide-react";
import { listAnalyses } from "@/lib/api";
import Sidebar from "@/components/dashboard/Sidebar";
import RiskBadge from "@/components/dashboard/RiskBadge";

const STATUS_LABELS: Record<string, string> = {
  PENDING: "En attente",
  RUNNING: "En cours",
  COMPLETED: "Terminée",
  FAILED: "Échec",
};

export default function AnalysisListPage() {
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAnalyses()
      .then((res) => setAnalyses(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <main className="flex-1 md:ml-64 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[#1e293b]">Analyses IA</h1>
          <p className="text-gray-500 text-sm mt-0.5">Historique de toutes les analyses de votre cabinet</p>
        </div>

        <div className="card">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e293b]" />
            </div>
          ) : analyses.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <BarChart3 className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm">Aucune analyse disponible</p>
              <Link href="/documents" className="text-sm text-blue-600 hover:underline mt-2">
                Importer et analyser un FEC
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {analyses.map((a) => (
                <Link
                  key={a.id}
                  href={`/analysis/${a.id}`}
                  className="flex items-center justify-between p-4 rounded-xl hover:bg-gray-50 border border-transparent hover:border-gray-100 transition-all group"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      a.status === "COMPLETED" ? "bg-[#1e293b]/10" :
                      a.status === "FAILED" ? "bg-red-50" : "bg-blue-50"
                    }`}>
                      {a.status === "FAILED" ? (
                        <AlertTriangle className="w-5 h-5 text-red-500" />
                      ) : (
                        <FileSearch className="w-5 h-5 text-[#1e293b]" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <p className="font-medium text-[#1e293b] text-sm">
                          Analyse #{a.id.slice(0, 8).toUpperCase()}
                        </p>
                        {a.risk_level && <RiskBadge level={a.risk_level} />}
                        {a.status !== "COMPLETED" && (
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            a.status === "RUNNING" ? "bg-blue-100 text-blue-700" :
                            a.status === "FAILED" ? "bg-red-100 text-red-700" :
                            "bg-gray-100 text-gray-600"
                          }`}>
                            {STATUS_LABELS[a.status] || a.status}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {new Date(a.created_at).toLocaleString("fr-FR")}
                        {a.risk_score !== null && ` — Score : ${a.risk_score}/100`}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

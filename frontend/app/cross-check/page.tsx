"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { GitCompare, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import { listDocuments } from "@/lib/api";
import api from "@/lib/api";
import Sidebar from "@/components/dashboard/Sidebar";
import RiskBadge from "@/components/dashboard/RiskBadge";

export default function CrossCheckPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const { register, handleSubmit } = useForm();

  useEffect(() => {
    listDocuments().then((res) => setDocuments(res.data));
  }, []);

  const onSubmit = async (data: any) => {
    if (data.document_a_id === data.document_b_id) {
      toast.error("Sélectionner deux documents différents");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("document_a_id", data.document_a_id);
      fd.append("document_b_id", data.document_b_id);
      fd.append("label_a", data.label_a || "Document A (Impôts)");
      fd.append("label_b", data.label_b || "Document B (Banque)");
      const res = await api.post("/cross-check/", fd);
      setResult(res.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erreur lors du cross-checking");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <main className="flex-1 ml-64 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[#1e293b]">Cross-Checking</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Comparez deux versions d'un même document — détectez les falsifications entre bilan fiscal et bilan bancaire
          </p>
        </div>

        <div className="card mb-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Document A</label>
                <select {...register("document_a_id", { required: true })}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#1e293b]">
                  <option value="">Sélectionner...</option>
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename} {d.fiscal_year ? `(${d.fiscal_year})` : ""} {d.entity_name ? `— ${d.entity_name}` : ""}
                    </option>
                  ))}
                </select>
                <input {...register("label_a")} placeholder="Libellé (ex: Bilan Impôts 2024)"
                  className="mt-2 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Document B</label>
                <select {...register("document_b_id", { required: true })}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#1e293b]">
                  <option value="">Sélectionner...</option>
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename} {d.fiscal_year ? `(${d.fiscal_year})` : ""} {d.entity_name ? `— ${d.entity_name}` : ""}
                    </option>
                  ))}
                </select>
                <input {...register("label_b")} placeholder="Libellé (ex: Bilan Banque 2024)"
                  className="mt-2 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]" />
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="btn-primary flex items-center gap-2 text-sm px-6">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
              Lancer le cross-checking
            </button>
          </form>
        </div>

        {result && (
          <div className="space-y-4">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-[#1e293b]">Résultat</h3>
                <RiskBadge level={result.risk_level} />
              </div>
              <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 mb-4">{result.interpretation}</p>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-[#1e293b]">{result.accounts_compared}</p>
                  <p className="text-xs text-gray-500">Comptes comparés</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-amber-600">{result.discrepancies_count}</p>
                  <p className="text-xs text-gray-500">Divergences</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-red-600">{result.rouge_discrepancies}</p>
                  <p className="text-xs text-gray-500">Majeures (ROUGE)</p>
                </div>
              </div>
            </div>

            {result.discrepancies?.length > 0 && (
              <div className="card">
                <h3 className="text-sm font-semibold text-[#1e293b] mb-4">Divergences détectées</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-100 text-gray-500">
                        <th className="text-left py-2 px-2">Compte</th>
                        <th className="text-right py-2 px-2">Doc A</th>
                        <th className="text-right py-2 px-2">Doc B</th>
                        <th className="text-right py-2 px-2">Écart absolu</th>
                        <th className="text-right py-2 px-2">Écart %</th>
                        <th className="text-center py-2 px-2">Type</th>
                        <th className="text-center py-2 px-2">Sévérité</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.discrepancies.map((d: any, i: number) => (
                        <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-2 px-2 font-mono font-semibold text-[#1e293b]">{d.account}</td>
                          <td className="py-2 px-2 text-right">{Object.values(d).find((v, k) => Object.keys(d)[k].startsWith('solde_') && Object.keys(d)[k].endsWith('_a'))?.toLocaleString("fr-FR")}</td>
                          <td className="py-2 px-2 text-right">{Object.values(d).find((v, k) => Object.keys(d)[k].startsWith('solde_') && Object.keys(d)[k].endsWith('_b'))?.toLocaleString("fr-FR")}</td>
                          <td className="py-2 px-2 text-right font-semibold">{d.difference_abs?.toLocaleString("fr-FR")}</td>
                          <td className="py-2 px-2 text-right font-semibold text-red-600">{d.difference_pct?.toFixed(1)}%</td>
                          <td className="py-2 px-2 text-center text-gray-500">{d.flag?.replace(/_/g, " ")}</td>
                          <td className="py-2 px-2 text-center"><RiskBadge level={d.severity} showDot={false} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

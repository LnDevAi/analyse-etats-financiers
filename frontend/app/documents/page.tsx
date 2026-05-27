"use client";
import { useEffect, useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";
import {
  Upload, FileText, Trash2, Play, Loader2,
  FileSpreadsheet, GitCompare, X,
} from "lucide-react";
import {
  uploadDocument, listDocuments, deleteDocument, createAnalysis,
} from "@/lib/api";
import Sidebar from "@/components/dashboard/Sidebar";
import { useRouter } from "next/navigation";

interface AnalyseModalProps {
  doc: any;
  documents: any[];
  onClose: () => void;
  onConfirm: (docId: string, prevDocId?: string, balanceDocId?: string) => void;
}

function AnalyseModal({ doc, documents, onClose, onConfirm }: AnalyseModalProps) {
  const [previousDocId, setPreviousDocId] = useState("");
  const [balanceDocId, setBalanceDocId] = useState("");

  const otherFecDocs = documents.filter(
    (d) => d.id !== doc.id && d.document_type === "FEC"
  );
  const balanceDocs = documents.filter(
    (d) => d.id !== doc.id && d.document_type === "BALANCE_GENERALE"
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-[#1e293b]">Lancer l'analyse IA</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-gray-600 mb-5">
          Document sélectionné :{" "}
          <span className="font-medium text-[#1e293b]">{doc.original_filename}</span>
          {doc.fiscal_year && <span className="text-gray-400"> — {doc.fiscal_year}</span>}
        </p>

        <div className="space-y-4">
          {/* FEC N-1 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1.5">
              <GitCompare className="w-4 h-4" />
              FEC exercice N-1 — revue analytique (optionnel)
            </label>
            <select
              value={previousDocId}
              onChange={(e) => setPreviousDocId(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
            >
              <option value="">— Sans comparaison N vs N-1 —</option>
              {otherFecDocs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename}{d.fiscal_year ? ` (${d.fiscal_year})` : ""}{d.entity_name ? ` — ${d.entity_name}` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Balance Générale */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Balance générale — réconciliation FEC (optionnel)
            </label>
            <select
              value={balanceDocId}
              onChange={(e) => setBalanceDocId(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
            >
              <option value="">— Sans réconciliation balance —</option>
              {balanceDocs.length > 0
                ? balanceDocs.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename}{d.fiscal_year ? ` (${d.fiscal_year})` : ""}
                    </option>
                  ))
                : <option disabled>Aucune balance importée — importez un fichier de type "Balance Générale"</option>
              }
            </select>
            <p className="text-xs text-gray-400 mt-1">
              Détecte les manipulations entre la balance comptable et le FEC.
            </p>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 btn-secondary text-sm py-2">
            Annuler
          </button>
          <button
            onClick={() => onConfirm(doc.id, previousDocId || undefined, balanceDocId || undefined)}
            className="flex-1 btn-primary text-sm py-2 flex items-center justify-center gap-2"
          >
            <Play className="w-4 h-4" /> Lancer l'analyse
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DocumentsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analysing, setAnalysing] = useState<string | null>(null);
  const [analyseTarget, setAnalyseTarget] = useState<any | null>(null);
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear().toString());
  const [entityName, setEntityName] = useState("");
  const [docType, setDocType] = useState("FEC");

  const loadDocs = async () => {
    try {
      const res = await listDocuments();
      setDocuments(res.data);
    } catch {}
  };

  useEffect(() => { loadDocs(); }, []);

  const onDrop = useCallback(async (accepted: File[]) => {
    if (!accepted.length) return;
    const file = accepted[0];
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("document_type", docType);
    if (fiscalYear) fd.append("fiscal_year", fiscalYear);
    if (entityName) fd.append("entity_name", entityName);
    try {
      await uploadDocument(fd);
      toast.success("Document importé avec succès");
      loadDocs();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erreur lors de l'import");
    } finally {
      setUploading(false);
    }
  }, [docType, fiscalYear, entityName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/plain": [".txt", ".csv"], "application/pdf": [".pdf"] },
    maxFiles: 1,
  });

  const handleAnalyseConfirm = async (docId: string, prevDocId?: string, balanceDocId?: string) => {
    setAnalyseTarget(null);
    setAnalysing(docId);
    try {
      const res = await createAnalysis(docId, prevDocId, balanceDocId);
      const msg = balanceDocId
        ? "Analyse + réconciliation balance lancée"
        : prevDocId ? "Analyse N vs N-1 lancée" : "Analyse lancée en arrière-plan";
      toast.success(msg);
      router.push(`/analysis/${res.data.id}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erreur lors du lancement");
    } finally {
      setAnalysing(null);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm("Supprimer ce document ?")) return;
    try {
      await deleteDocument(docId);
      toast.success("Document supprimé");
      loadDocs();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erreur suppression");
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      {analyseTarget && (
        <AnalyseModal
          doc={analyseTarget}
          documents={documents}
          onClose={() => setAnalyseTarget(null)}
          onConfirm={handleAnalyseConfirm}
        />
      )}
      <Sidebar />
      <main className="flex-1 ml-64 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[#1e293b]">Documents</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Importez vos FEC et liasses fiscales pour lancer l'analyse IA
          </p>
        </div>

        {/* Upload zone */}
        <div className="card mb-6">
          <h3 className="text-sm font-semibold text-[#1e293b] mb-4">Importer un document</h3>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Type de document</label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
              >
                <option value="FEC">FEC (Fichier Écritures Comptables)</option>
                <option value="BALANCE_GENERALE">Balance Générale (CSV/TSV)</option>
                <option value="LIASSE_FISCALE_PDF">Liasse Fiscale PDF</option>
                <option value="BILAN_PDF">Bilan PDF</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Exercice fiscal</label>
              <input
                value={fiscalYear}
                onChange={(e) => setFiscalYear(e.target.value)}
                type="number"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                placeholder="2024"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nom de l'entité</label>
              <input
                value={entityName}
                onChange={(e) => setEntityName(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                placeholder="Entreprise XYZ"
              />
            </div>
          </div>

          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
              isDragActive ? "border-[#1e293b] bg-[#1e293b]/5" : "border-gray-200 hover:border-[#1e293b]/40"
            }`}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-10 h-10 text-[#1e293b] animate-spin" />
                <p className="text-sm text-gray-500">Import en cours...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <Upload className="w-10 h-10 text-gray-400" />
                <p className="text-sm font-medium text-[#1e293b]">
                  Glissez votre fichier ici ou cliquez pour sélectionner
                </p>
                <p className="text-xs text-gray-400">FEC (.txt, .csv) — Liasse PDF — Max 50 MB</p>
              </div>
            )}
          </div>
        </div>

        {/* Documents list */}
        <div className="card">
          <h3 className="text-sm font-semibold text-[#1e293b] mb-4">
            Mes documents ({documents.length})
          </h3>

          {documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <FileText className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm">Aucun document importé</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Fichier</th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Type</th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Entité</th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Exercice</th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Date</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <FileSpreadsheet className="w-4 h-4 text-[#1e293b]" />
                          <span className="font-medium text-[#1e293b] truncate max-w-[200px]">
                            {doc.original_filename}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-gray-500">{doc.document_type}</td>
                      <td className="py-3 px-3 text-gray-600">{doc.entity_name || "—"}</td>
                      <td className="py-3 px-3 text-gray-600">{doc.fiscal_year || "—"}</td>
                      <td className="py-3 px-3 text-gray-400 text-xs">
                        {new Date(doc.created_at).toLocaleDateString("fr-FR")}
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setAnalyseTarget(doc)}
                            disabled={!!analysing}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e293b] text-white rounded-lg text-xs font-medium hover:bg-[#334155] transition-colors disabled:opacity-50"
                          >
                            {analysing === doc.id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Play className="w-3.5 h-3.5" />
                            )}
                            Analyser
                          </button>
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

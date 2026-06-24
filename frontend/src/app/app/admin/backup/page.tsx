"use client";

import { useState, useEffect } from "react";
import { 
  ShieldCheck, 
  Download, 
  RefreshCcw, 
  Upload, 
  Archive, 
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2
} from "lucide-react";
import { format } from "date-fns";
import apiClient from "@/lib/apiClient";
import { useAuthStore } from "@/lib/authStore";

// We use apiClient to automatically include auth tokens

interface BackupMetadata {
  id: string;
  "Created Time": string;
  "Database Version": string;
  "Model Version": string;
  "Backup Size": number;
  "Git SHA"?: string;
  Uploaded?: boolean;
}

function formatBytes(bytes: number, decimals = 2) {
  if (!+bytes) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

export default function BackupRestorePage() {
  const [backups, setBackups] = useState<BackupMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const getErrorMsg = (err: any): string => {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d: any) => `${d.loc?.[d.loc.length - 1] || 'Field'}: ${d.msg}`).join(", ");
    return err.message || "An unknown error occurred";
  };

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/api/system/backups");
      setBackups(res.data);
    } catch (err: any) {
      setError(getErrorMsg(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackups();
  }, []);

  const handleCreate = async () => {
    try {
      setCreating(true);
      setError(null);
      setSuccess(null);
      await apiClient.post("/api/system/backups");
      await fetchBackups();
      setSuccess("Backup created successfully");
    } catch (err: any) {
      setError(getErrorMsg(err));
    } finally {
      setCreating(false);
    }
  };

  const handleRestore = async (id: string) => {
    if (!confirm(`Are you sure you want to restore backup ${id}? This will overwrite current data.`)) return;
    
    try {
      setRestoringId(id);
      setError(null);
      setSuccess(null);
      await apiClient.post(`/api/system/backups/${id}/restore`);
      setSuccess("Backup restored successfully. The system has been rolled back.");
    } catch (err: any) {
      setError(getErrorMsg(err));
    } finally {
      setRestoringId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`Are you sure you want to delete backup ${id}? This action cannot be undone.`)) return;
    
    try {
      setDeletingId(id);
      setError(null);
      setSuccess(null);
      await apiClient.delete(`/api/system/backups/${id}`);
      setSuccess(`Backup ${id} deleted successfully.`);
      await fetchBackups();
    } catch (err: any) {
      setError(getErrorMsg(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);
      
      const formData = new FormData();
      formData.append("file", file);
      
      const { tokens } = useAuthStore.getState();
      const res = await fetch("/api/system/backups/upload", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${tokens?.access_token}`
        },
        body: formData
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw { response: { data: errData }, message: "Upload failed" };
      }
      
      await fetchBackups();
      setSuccess("Backup uploaded successfully");
    } catch (err: any) {
      setError(getErrorMsg(err));
    } finally {
      setUploading(false);
      // reset file input
      e.target.value = '';
    }
  };

  const handleDownload = async (id: string) => {
    try {
      const res = await apiClient.get(`/api/system/backups/${id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${id}.zip`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err: any) {
      setError(getErrorMsg(err));
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-600 dark:from-blue-300 dark:to-indigo-400">
            System Backup & Restore
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2 text-sm max-w-2xl">
            Create full snapshots of the database, AI models, and storage volumes.
            Restore to any previous point in time or download for offsite safekeeping.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className={`relative cursor-pointer px-4 py-2 flex items-center gap-2 bg-white/50 dark:bg-slate-800/50 hover:bg-white dark:hover:bg-slate-700 border border-gray-200 dark:border-slate-700 rounded-lg shadow-sm backdrop-blur-sm transition-all text-sm font-medium ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
            <input 
              type="file" 
              accept=".zip" 
              onChange={handleUpload}
              className="sr-only"
              disabled={uploading}
            />
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            <span>Upload ZIP</span>
          </label>
          <button 
            onClick={handleCreate}
            disabled={creating}
            className="px-5 py-2 flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg shadow-md shadow-blue-500/20 transition-all text-sm font-medium hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
          >
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
            Create Snapshot
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 flex items-start gap-3 animate-in slide-in-from-top-2">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-red-800 dark:text-red-400">Action Failed</h3>
            <p className="text-sm text-red-600 dark:text-red-300 mt-1">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 flex items-start gap-3 animate-in slide-in-from-top-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-emerald-800 dark:text-emerald-400">Success</h3>
            <p className="text-sm text-emerald-600 dark:text-emerald-300 mt-1">{success}</p>
          </div>
        </div>
      )}

      <div className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl border border-gray-200 dark:border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-800/50">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <Database className="w-4 h-4" />
            Backup History
          </div>
        </div>
        
        <div className="divide-y divide-gray-100 dark:divide-slate-800">
          {loading ? (
            <div className="p-12 flex flex-col items-center justify-center text-gray-400">
              <Loader2 className="w-8 h-8 animate-spin mb-4 text-blue-500" />
              <p>Loading backups...</p>
            </div>
          ) : backups.length === 0 ? (
            <div className="p-16 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center mb-4">
                <Archive className="w-8 h-8 text-indigo-500 opacity-80" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">No backups found</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm">
                Create your first system snapshot to ensure you can recover from unexpected data loss.
              </p>
            </div>
          ) : (
            backups.map((backup) => (
              <div key={backup.id} className="p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6 hover:bg-gray-50/50 dark:hover:bg-slate-800/30 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center shrink-0">
                    <Archive className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                      {backup.id}
                      {backup.Uploaded && (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300">
                          External
                        </span>
                      )}
                    </h4>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>{format(new Date(backup["Created Time"]), "MMM d, yyyy h:mm a")}</span>
                      <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                      <span>{formatBytes(backup["Backup Size"])}</span>
                      <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                      <span>{backup["Database Version"]}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 lg:ml-auto shrink-0">
                  <button 
                    onClick={() => handleDownload(backup.id)}
                    className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-lg transition-colors tooltip-trigger relative group"
                  >
                    <Download className="w-4 h-4" />
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                      Download ZIP
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => handleRestore(backup.id)}
                    disabled={restoringId !== null || deletingId !== null}
                    className="px-4 py-2 flex items-center gap-2 bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-500/10 dark:hover:bg-red-500/20 dark:text-red-400 rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
                  >
                    {restoringId === backup.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <RefreshCcw className="w-4 h-4" />
                    )}
                    Restore
                  </button>
                  
                  <button 
                    onClick={() => handleDelete(backup.id)}
                    disabled={deletingId !== null || restoringId !== null}
                    className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors tooltip-trigger relative group disabled:opacity-50"
                  >
                    {deletingId === backup.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                      Delete Backup
                    </div>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

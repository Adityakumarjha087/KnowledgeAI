"use client";

import { useEffect, useState, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

interface DocumentItem {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  processing_status: "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED";
  page_count: number;
  chunk_count: number;
  created_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchDocuments = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const list = await api.get<DocumentItem[]>("/documents");
      setDocuments(list);
      
      const isProcessing = list.some(
        (doc) => doc.processing_status === "UPLOADED" || doc.processing_status === "PROCESSING"
      );
      
      if (isProcessing && !pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(() => {
          fetchDocuments(false);
        }, 3000);
      } else if (!isProcessing && pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      
    } catch (err: any) {
      setError(err.message || "Failed to fetch document inventory.");
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments(true);
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadProgress("Uploading file...");
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      await api.post("/documents/upload", formData);
      setUploadProgress("Ingesting pipeline enqueued...");
      await fetchDocuments(false);
    } catch (err: any) {
      setError(err.message || "Failed to upload file.");
    } finally {
      setUploading(false);
      setUploadProgress("");
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files[0]);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to permanently delete this document and all its indexed chunks?")) {
      return;
    }
    try {
      await api.delete(`/documents/${id}`);
      setDocuments(documents.filter((doc) => doc.id !== id));
    } catch (err: any) {
      setError(err.message || "Failed to delete document.");
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <Sidebar>
      <div className="flex flex-col flex-1 max-w-6xl mx-auto w-full space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md border border-white/15 bg-white/5 text-white/70 text-[10px] font-mono uppercase tracking-wider mb-2">
              Knowledge Repository
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Documents Manager
            </h1>
            <p className="text-white/50 mt-1 text-xs font-normal">
              Upload, parse, and chunk enterprise files for high-accuracy semantic retrieval
            </p>
          </div>
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
          />
        </div>

        {error && (
          <div className="p-3.5 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-xs font-medium max-w-lg">
            {error}
          </div>
        )}

        {/* Upload Zone (Black with White Dashed Border & Shadow) */}
        <div 
          onClick={() => fileInputRef.current?.click()}
          className="black-card rounded-2xl p-10 text-center cursor-pointer relative overflow-hidden group border-dashed border-2 border-white/20 hover:border-white/50 transition-colors"
        >
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/15 flex items-center justify-center text-white/80 group-hover:text-white group-hover:bg-white/10 transition-colors">
              {uploading ? (
                <span className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-white">
                {uploading ? uploadProgress : "Click to select or drag & drop documents"}
              </p>
              <p className="text-xs text-white/40 mt-1 font-normal">
                Supported formats: PDF, DOCX, TXT, and Markdown (Max 10MB)
              </p>
            </div>
          </div>
        </div>

        {/* Documents Table */}
        <div className="black-card rounded-2xl overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-white/40">
              <span className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin inline-block" />
            </div>
          ) : documents.length === 0 ? (
            <div className="p-12 text-center space-y-2">
              <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 mx-auto flex items-center justify-center text-white/40 text-sm">
                📂
              </div>
              <p className="font-semibold text-white text-sm">No documents uploaded</p>
              <p className="text-xs text-white/40">Upload documents above to index them for search.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/10 bg-[#050505] text-white/50 text-[11px] font-mono uppercase tracking-wider">
                    <th className="p-5">Filename</th>
                    <th className="p-5">Size</th>
                    <th className="p-5">Chunks</th>
                    <th className="p-5">Status</th>
                    <th className="p-5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10 text-xs">
                  {documents.map((doc) => {
                    let statusBadge = "text-white/60 bg-white/5 border-white/10";
                    if (doc.processing_status === "PROCESSING") {
                      statusBadge = "text-white bg-white/10 border-white/30 animate-pulse";
                    } else if (doc.processing_status === "COMPLETED") {
                      statusBadge = "text-emerald-400 bg-emerald-950/40 border-emerald-500/30";
                    } else if (doc.processing_status === "FAILED") {
                      statusBadge = "text-red-400 bg-red-950/40 border-red-500/30";
                    }

                    return (
                      <tr key={doc.id} className="hover:bg-white/5 transition-colors">
                        <td className="p-5 font-medium text-white flex items-center gap-2.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-white shadow-sm" />
                          <span className="truncate max-w-xs">{doc.filename}</span>
                        </td>
                        <td className="p-5 text-white/50 font-mono">{formatBytes(doc.file_size)}</td>
                        <td className="p-5 text-white/70 font-medium">
                          {doc.page_count}p • <span className="text-white font-semibold">{doc.chunk_count} chunks</span>
                        </td>
                        <td className="p-5">
                          <span className={`px-2.5 py-1 text-[10px] font-bold rounded-md border ${statusBadge}`}>
                            {doc.processing_status}
                          </span>
                        </td>
                        <td className="p-5 text-right">
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-2 rounded-lg border border-white/10 bg-[#0a0a0a] text-white/50 hover:text-red-400 hover:border-red-500/30 hover:bg-red-950/20 transition-colors cursor-pointer"
                            title="Delete Document"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Sidebar>
  );
}

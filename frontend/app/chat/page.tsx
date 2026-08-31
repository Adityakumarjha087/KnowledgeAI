"use client";

import { useEffect, useState, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

interface ConversationItem {
  id: number;
  title: string;
  document_id?: number | null;
  document_filename?: string | null;
  created_at: string;
  updated_at: string;
}

interface MessageItem {
  id: number | string;
  role: "user" | "assistant";
  content: string;
  sources?: any[] | null;
  created_at?: string;
  rating?: number | null;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const [editingConvId, setEditingConvId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  const [inspectSource, setInspectSource] = useState<any | null>(null);

  const [feedbackMessageId, setFeedbackMessageId] = useState<number | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<number>(1);
  const [feedbackComment, setFeedbackComment] = useState("");

  // Chat/Session-level isolated document attachment
  const [attachedDocId, setAttachedDocId] = useState<number | null>(null);
  const [attachedFileName, setAttachedFileName] = useState<string | null>(null);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, generating]);

  const fetchConversations = async () => {
    try {
      const list = await api.get<ConversationItem[]>("/conversations");
      setConversations(list);
    } catch (err: any) {
      console.error("Failed to load conversations:", err.message);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  // When active conversation changes, load its specific history and bound document
  useEffect(() => {
    if (activeConvId === null) {
      setMessages([]);
      setAttachedDocId(null);
      setAttachedFileName(null);
      return;
    }

    async function fetchHistory() {
      setLoadingHistory(true);
      setError("");
      try {
        const detail = await api.get<any>(`/conversations/${activeConvId}`);
        setMessages(detail.messages || []);
        if (detail.document_id) {
          setAttachedDocId(detail.document_id);
          setAttachedFileName(detail.document_filename || "Attached Document");
        } else {
          setAttachedDocId(null);
          setAttachedFileName(null);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load chat history.");
      } finally {
        setLoadingHistory(false);
      }
    }
    fetchHistory();
  }, [activeConvId]);

  // Upload and attach document strictly to this chat session
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setUploadingDoc(true);
    setAttachedFileName(file.name);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const docRes = await api.post<any>("/documents/upload", formData);
      setAttachedDocId(docRes.id);
      setAttachedFileName(docRes.filename || file.name);
      if (!inputMessage.trim()) {
        setInputMessage(`Explain the key details in ${file.name}`);
      }
    } catch (err: any) {
      setError(err.message || "Failed to upload document");
      setAttachedDocId(null);
      setAttachedFileName(null);
    } finally {
      setUploadingDoc(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Complete reset to start a fresh, isolated chat session
  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
    setAttachedDocId(null);
    setAttachedFileName(null);
    setInputMessage("");
    setError("");
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || generating || uploadingDoc) return;

    const userMsg = inputMessage;
    setInputMessage("");
    setError("");
    setGenerating(true);

    setMessages((prev) => [...prev, { id: "temp-user", role: "user", content: userMsg }]);
    setMessages((prev) => [...prev, { id: "temp-assistant", role: "assistant", content: "", sources: [] }]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          message: userMsg,
          conversation_id: activeConvId,
          document_id: attachedDocId,
        }),
      });

      if (!response.ok) {
        throw new Error("Chat request failed. Please check backend connection.");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let assistantText = "";
      let retrievedSources: any[] = [];
      let savedMsgId: number | null = null;
      let finalConvId = activeConvId;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        const lines = chunkText.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "sources") {
                retrievedSources = data.sources;
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.id === "temp-assistant") {
                    last.sources = retrievedSources;
                  }
                  return updated;
                });
              } else if (data.type === "token") {
                assistantText += data.token;
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.id === "temp-assistant") {
                    last.content = assistantText;
                  }
                  return updated;
                });
              } else if (data.type === "done") {
                savedMsgId = data.message_id;
                finalConvId = data.conversation_id;

                setMessages((prev) => {
                  const updated = [...prev];
                  const last_assistant = updated[updated.length - 1];
                  const last_user = updated[updated.length - 2];
                  if (last_assistant && last_assistant.id === "temp-assistant") {
                    last_assistant.id = savedMsgId!;
                  }
                  if (last_user && last_user.id === "temp-user") {
                    last_user.id = `user-${savedMsgId}`;
                  }
                  return updated;
                });
              } else if (data.type === "error") {
                setError(data.error);
              }
            } catch {
              // Ignore partial chunk lines
            }
          }
        }
      }

      if (activeConvId === null && finalConvId) {
        setActiveConvId(finalConvId);
        await fetchConversations();
      }
    } catch (err: any) {
      setError(err.message || "Failed to process RAG stream query.");
      setMessages((prev) => prev.filter((m) => m.id !== "temp-assistant" && m.id !== "temp-user"));
    } finally {
      setGenerating(false);
    }
  };

  const handleUpdateTitle = async (id: number) => {
    if (!editingTitle.trim()) return;
    try {
      await api.put(`/conversations/${id}`, { title: editingTitle });
      setConversations(conversations.map((c) => (c.id === id ? { ...c, title: editingTitle } : c)));
      setEditingConvId(null);
    } catch {
      alert("Failed to update title");
    }
  };

  const handleDeleteConversation = async (id: number) => {
    if (!confirm("Are you sure you want to delete this chat session?")) {
      return;
    }
    try {
      await api.delete(`/conversations/${id}`);
      setConversations(conversations.filter((c) => c.id !== id));
      if (activeConvId === id) {
        handleNewChat();
      }
    } catch {
      alert("Failed to delete conversation");
    }
  };

  const handleFeedbackSubmit = async () => {
    if (feedbackMessageId === null) return;
    try {
      await api.post("/feedback", {
        message_id: feedbackMessageId,
        rating: feedbackRating,
        feedback: feedbackComment,
      });

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === feedbackMessageId ? { ...msg, rating: feedbackRating } : msg
        )
      );

      setFeedbackMessageId(null);
      setFeedbackComment("");
    } catch {
      alert("Failed to submit feedback");
    }
  };

  return (
    <Sidebar>
      <div className="flex flex-1 -m-4 sm:-m-8 md:-m-12 h-[calc(100vh-3.5rem)] md:h-[calc(100vh)] overflow-hidden bg-transparent">
        {/* Chats Sidebar */}
        <div className="w-64 sm:w-72 border-r border-white/10 bg-[#050505]/90 backdrop-blur-xl flex flex-col p-4 sm:p-5 shrink-0 h-full z-10">
          <button
            onClick={handleNewChat}
            className="w-full py-2.5 rounded-xl bg-white text-black hover:bg-white/90 font-bold text-xs mb-4 flex items-center justify-center gap-2 cursor-pointer shadow-md transition-all active:scale-[0.98]"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            + New Conversation
          </button>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            <span className="text-white/40 text-[10px] font-mono uppercase tracking-wider px-2 block mb-1">Past Chats</span>
            {conversations.length === 0 ? (
              <p className="text-white/40 text-xs px-2 italic">No past conversations.</p>
            ) : (
              conversations.map((conv) => {
                const active = activeConvId === conv.id;
                return (
                  <div
                    key={conv.id}
                    className={`group flex items-center justify-between p-2.5 rounded-xl transition-all border ${
                      active
                        ? "bg-white/10 border-white/30 text-white shadow-lg backdrop-blur-md font-semibold"
                        : "border-transparent text-white/60 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    {editingConvId === conv.id ? (
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={() => handleUpdateTitle(conv.id)}
                        onKeyDown={(e) => e.key === "Enter" && handleUpdateTitle(conv.id)}
                        className="bg-black px-2 py-0.5 rounded border border-white/20 text-xs focus:outline-none w-36 text-white"
                        autoFocus
                      />
                    ) : (
                      <button
                        onClick={() => setActiveConvId(conv.id)}
                        className="text-left text-xs font-medium truncate flex-1 pr-2 cursor-pointer flex items-center gap-1.5"
                      >
                        {conv.document_filename && (
                          <span className="text-[10px] text-white/50 shrink-0">📄</span>
                        )}
                        <span className="truncate">{conv.title}</span>
                      </button>
                    )}

                    {editingConvId !== conv.id && (
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                        <button
                          onClick={() => {
                            setEditingConvId(conv.id);
                            setEditingTitle(conv.title);
                          }}
                          className="p-1 text-white/40 hover:text-white cursor-pointer"
                          title="Rename"
                        >
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteConversation(conv.id)}
                          className="p-1 text-white/40 hover:text-red-400 cursor-pointer"
                          title="Delete"
                        >
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col bg-[#000000]/60 backdrop-blur-md relative h-full">
          {/* Active Session Header Banner */}
          <div className="px-6 py-3 border-b border-white/10 flex items-center justify-between bg-[#050505]/80 backdrop-blur-lg">
            <div className="flex items-center gap-2 text-xs font-mono text-white/70">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Session Isolation: Active</span>
            </div>

            {attachedFileName ? (
              <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-white/5 border border-white/15 text-xs font-mono text-white">
                <span>📄</span>
                <span className="truncate max-w-[200px] sm:max-w-xs">{attachedFileName}</span>
                <button
                  onClick={() => {
                    setAttachedDocId(null);
                    setAttachedFileName(null);
                  }}
                  className="text-white/40 hover:text-white ml-1 text-xs cursor-pointer"
                  title="Detach document from active chat"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="text-[11px] text-white/40 font-mono italic">
                No document attached to this chat
              </div>
            )}
          </div>

          {error && (
            <div className="absolute top-14 left-1/2 -translate-x-1/2 p-2.5 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-xs font-medium text-center z-20 shadow-lg">
              {error}
            </div>
          )}

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 space-y-5">
            {messages.length === 0 && !loadingHistory ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto space-y-4">
                <div className="w-14 h-14 rounded-2xl bg-white/5 text-white border border-white/15 flex items-center justify-center shadow-xl">
                  <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h3 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">Enterprise Knowledge Assistant</h3>
                <p className="text-xs text-white/50 font-normal leading-relaxed max-w-sm">
                  Attach a document below using the 📎 icon to ask questions with strict session-level isolation and verifiable citations.
                </p>
                {attachedFileName && (
                  <div className="p-3 rounded-xl border border-white/20 bg-white/5 flex items-center gap-2 text-xs font-mono text-white">
                    <span>📄</span>
                    <span>Ready to answer questions about <strong>{attachedFileName}</strong></span>
                  </div>
                )}
              </div>
            ) : (
              messages.map((msg, index) => {
                const isUser = msg.role === "user";
                return (
                  <div key={msg.id || index} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-2xl p-4 sm:p-5 rounded-2xl border ${
                        isUser
                          ? "bg-white text-black border-white rounded-br-none shadow-lg font-medium"
                          : "bg-[#0d0d0d]/90 border-white/15 text-white/90 rounded-bl-none shadow-md backdrop-blur-md"
                      }`}
                    >
                      <p className="whitespace-pre-wrap leading-relaxed text-xs sm:text-sm">{msg.content}</p>

                      {/* Assistant Sources & Feedback */}
                      {!isUser && (
                        <div className="mt-3.5 pt-3.5 border-t border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-3">
                          {/* Sources Links */}
                          <div className="flex flex-wrap gap-1.5 items-center">
                            <span className="text-[10px] text-white/40 font-mono uppercase tracking-wider">Sources:</span>
                            {msg.sources && msg.sources.length > 0 ? (
                              msg.sources.map((src, srcIdx) => (
                                <button
                                  key={srcIdx}
                                  onClick={() => setInspectSource(src)}
                                  className="px-2 py-0.5 bg-white/5 text-white/80 hover:bg-white/10 border border-white/15 text-[11px] font-mono rounded-lg transition-colors cursor-pointer"
                                >
                                  [{srcIdx + 1}] {src.filename || "Doc"} {src.page_number ? `p.${src.page_number}` : ""}
                                </button>
                              ))
                            ) : (
                              <span className="text-[11px] text-white/40 italic">No sources referenced.</span>
                            )}
                          </div>

                          {/* Feedback buttons */}
                          {typeof msg.id === "number" && (
                            <div className="flex gap-1.5 shrink-0">
                              <button
                                onClick={() => {
                                  setFeedbackMessageId(msg.id as number);
                                  setFeedbackRating(1);
                                }}
                                className={`p-1 rounded-lg border text-xs transition-colors cursor-pointer ${
                                  msg.rating === 1
                                    ? "bg-white text-black border-white"
                                    : "border-white/10 bg-[#141414] text-white/50 hover:text-white hover:border-white/20"
                                }`}
                              >
                                👍
                              </button>
                              <button
                                onClick={() => {
                                  setFeedbackMessageId(msg.id as number);
                                  setFeedbackRating(-1);
                                }}
                                className={`p-1 rounded-lg border text-xs transition-colors cursor-pointer ${
                                  msg.rating === -1
                                    ? "bg-red-950 text-red-300 border-red-500/40"
                                    : "border-white/10 bg-[#141414] text-white/50 hover:text-red-400 hover:border-white/20"
                                }`}
                              >
                                👎
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}

            {generating && (
              <div className="flex items-center gap-2.5 text-white/60 text-xs font-mono pl-2">
                <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Retrieving context & generating answer...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Panel with Direct Document Attachment */}
          <form onSubmit={handleSendMessage} className="p-4 sm:p-5 border-t border-white/10 bg-[#050505]/95 backdrop-blur-xl">
            <div className="max-w-4xl mx-auto space-y-2">
              {/* Attached file status banner */}
              {attachedFileName && (
                <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/15 w-fit text-xs font-mono">
                  <span className="text-white/70">📄</span>
                  <span className="text-white font-semibold truncate max-w-xs">{attachedFileName}</span>
                  {uploadingDoc ? (
                    <span className="text-yellow-400 text-[10px] flex items-center gap-1 font-sans">
                      <span className="w-2.5 h-2.5 border-2 border-yellow-400/20 border-t-yellow-400 rounded-full animate-spin" />
                      Uploading & Indexing...
                    </span>
                  ) : (
                    <span className="text-emerald-400 text-[10px] font-sans flex items-center gap-1">
                      <span>✓</span> Isolated in active chat
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      setAttachedDocId(null);
                      setAttachedFileName(null);
                    }}
                    className="text-white/40 hover:text-white ml-2 text-xs cursor-pointer"
                    title="Remove attachment"
                  >
                    ✕
                  </button>
                </div>
              )}

              {/* Hidden file input */}
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleFileUpload}
              />

              <div className="relative flex items-center">
                {/* Paperclip attachment button */}
                <button
                  type="button"
                  disabled={uploadingDoc || generating}
                  onClick={() => fileInputRef.current?.click()}
                  title="Attach document (.pdf, .docx, .txt, .md)"
                  className="absolute left-2.5 p-1.5 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-all cursor-pointer disabled:opacity-30 z-10"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </button>

                <input
                  type="text"
                  disabled={generating || uploadingDoc}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={attachedFileName ? `Ask anything about ${attachedFileName}...` : "Attach a document 📎 or ask general questions..."}
                  className="w-full pl-10 pr-12 py-3 rounded-xl input-static text-xs font-medium disabled:opacity-50"
                />

                <button
                  type="submit"
                  disabled={!inputMessage.trim() || generating || uploadingDoc}
                  className="absolute right-2 p-2 rounded-lg btn-white text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center cursor-pointer shadow-sm"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Modal: Source Inspector */}
      {inspectSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="black-card w-full max-w-xl rounded-2xl p-6 space-y-4 shadow-2xl border border-white/20">
            <div className="flex justify-between items-center pb-3 border-b border-white/10">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <span>📄</span> Source Citation Inspector
              </h3>
              <button onClick={() => setInspectSource(null)} className="text-white/40 hover:text-white cursor-pointer text-sm font-bold">
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs text-white/60 font-mono">
                <div>File: <strong className="text-white">{inspectSource.filename}</strong></div>
                <div>Location: <strong className="text-white">
                  {inspectSource.page_number ? `Page ${inspectSource.page_number}` : ""}{inspectSource.section ? `, Sec ${inspectSource.section}` : "Full doc"}
                </strong></div>
              </div>
              <div className="p-4 rounded-xl bg-black border border-white/10 text-xs text-white/80 font-mono leading-relaxed whitespace-pre-wrap max-h-72 overflow-y-auto">
                {inspectSource.text}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Feedback */}
      {feedbackMessageId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="black-card w-full max-w-md rounded-2xl p-6 space-y-4 shadow-2xl border border-white/20">
            <div className="flex justify-between items-center pb-3 border-b border-white/10">
              <h3 className="font-bold text-white text-sm">Answer Feedback</h3>
              <button onClick={() => setFeedbackMessageId(null)} className="text-white/40 hover:text-white cursor-pointer text-sm font-bold">
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-white/50 text-[10px] font-mono uppercase tracking-wider mb-1.5">Rating</label>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-white">
                  {feedbackRating === 1 ? "👍 Helpful" : "👎 Not Helpful"}
                </span>
              </div>
              <div>
                <label className="block text-white/50 text-[10px] font-mono uppercase tracking-wider mb-1.5" htmlFor="comment">
                  Comment (Optional)
                </label>
                <textarea
                  id="comment"
                  rows={4}
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="Tell us how to improve this answer..."
                  className="w-full px-3 py-2 rounded-xl input-static text-xs font-medium"
                />
              </div>
              <button
                onClick={handleFeedbackSubmit}
                className="w-full py-2.5 rounded-xl btn-white font-bold text-xs text-black cursor-pointer shadow-md"
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}
    </Sidebar>
  );
}

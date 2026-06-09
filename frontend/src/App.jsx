import { useState, useEffect } from "react";
import ChatPanel from "./components/ChatPanel";
import DocumentPanel from "./components/DocumentPanel";
import StatusBar from "./components/StatusBar";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [health, setHealth] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => { fetchHealth(); fetchDocuments(); }, []);

  async function fetchHealth() {
    try {
      const r = await fetch("/api/v1/health");
      setHealth(await r.json());
    } catch { setHealth({ status: "unreachable" }); }
  }

  async function fetchDocuments() {
    try {
      const r = await fetch("/api/v1/documents");
      const data = await r.json();
      setDocuments(data.documents || []);
    } catch {}
  }

  async function handleUpload(file) {
    const form = new FormData();
    form.append("file", file);
    const r = await fetch("/api/v1/documents/upload", { method: "POST", body: form });
    if (!r.ok) { const err = await r.json(); throw new Error(err.detail || "Upload failed"); }
    await fetchDocuments();
    return r.json();
  }

  async function handleDelete(docId) {
    await fetch(`/api/v1/documents/${docId}`, { method: "DELETE" });
    setDocuments((d) => d.filter((doc) => doc.doc_id !== docId));
    if (selectedDoc?.doc_id === docId) setSelectedDoc(null);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="menu-btn" onClick={() => setSidebarOpen((o) => !o)} aria-label="Toggle sidebar">
          <span /><span /><span />
        </button>
        <div className="brand">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="2" y="2" width="8" height="10" rx="1.5" fill="var(--accent)" opacity=".85"/>
            <rect x="12" y="2" width="8" height="6" rx="1.5" fill="var(--accent)" opacity=".5"/>
            <rect x="12" y="10" width="8" height="10" rx="1.5" fill="var(--accent)" opacity=".7"/>
            <rect x="2" y="14" width="8" height="6" rx="1.5" fill="var(--accent)" opacity=".55"/>
          </svg>
          <span>DocMind RAG</span>
        </div>
        <StatusBar health={health} />
      </header>
      <div className="workspace">
        {sidebarOpen && (
          <aside className="sidebar">
            <DocumentPanel documents={documents} selectedDoc={selectedDoc}
              onSelect={setSelectedDoc} onUpload={handleUpload} onDelete={handleDelete} />
          </aside>
        )}
        <main className="chat-area">
          <ChatPanel selectedDoc={selectedDoc} />
        </main>
      </div>
    </div>
  );
}

import { useState, useRef, useEffect } from "react";
import Message from "./Message";

export default function ChatPanel({ selectedDoc }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(e) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    const userMsg = { role: "user", content: question, id: Date.now() };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);

    const assistantId = Date.now() + 1;
    setMessages((m) => [...m, { role: "assistant", content: "", id: assistantId, streaming: true }]);

    try {
      const resp = await fetch("/api/v1/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, doc_id: selectedDoc?.doc_id || null, stream: true }),
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const token = line.slice(6);
            if (token === "[DONE]") break;
            accumulated += token;
            setMessages((m) =>
              m.map((msg) =>
                msg.id === assistantId ? { ...msg, content: accumulated } : msg
              )
            );
          }
        }
      }
      setMessages((m) =>
        m.map((msg) => msg.id === assistantId ? { ...msg, streaming: false } : msg)
      );
    } catch (err) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantId
            ? { ...msg, content: `Error: ${err.message}`, streaming: false, error: true }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-panel">
      {selectedDoc && (
        <div className="doc-scope-banner">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M3 2h7l3 3v9H3V2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
            <path d="M10 2v3h3" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
          </svg>
          Scoped to: <strong>{selectedDoc.doc_name}</strong>
          <span className="scope-pages">{selectedDoc.pages}p</span>
        </div>
      )}

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <circle cx="24" cy="24" r="22" stroke="var(--border)" strokeWidth="2"/>
                <path d="M16 24h16M24 16v16" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round"/>
              </svg>
            </div>
            <p>Upload documents in the sidebar, then ask anything about them.</p>
            {!selectedDoc && <p className="hint">Select a document to scope your search, or search across all.</p>}
          </div>
        )}
        {messages.map((msg) => <Message key={msg.id} message={msg} />)}
        <div ref={bottomRef} />
      </div>

      <form className="input-bar" onSubmit={sendMessage}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={selectedDoc ? `Ask about "${selectedDoc.doc_name}"…` : "Ask across all documents…"}
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()} className="send-btn">
          {loading ? (
            <span className="spinner" />
          ) : (
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M2 9h14M9 2l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </button>
      </form>
    </div>
  );
}

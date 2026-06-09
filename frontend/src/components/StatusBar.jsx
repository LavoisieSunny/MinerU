export default function StatusBar({ health }) {
  if (!health) return <div className="status-bar"><span className="status-dot status-dot--unknown" />Connecting…</div>;

  const ok = health.status === "ok";
  return (
    <div className="status-bar">
      <span className={`status-dot ${ok ? "status-dot--ok" : "status-dot--warn"}`} />
      <span className="status-label">{health.model || "—"}</span>
      <span className="status-sep">·</span>
      <span className={`status-service ${health.ollama === "ok" ? "ok" : "err"}`}>Ollama</span>
      <span className="status-sep">·</span>
      <span className={`status-service ${health.qdrant === "ok" ? "ok" : "err"}`}>Qdrant</span>
    </div>
  );
}

import { useState, useRef } from "react";

export default function DocumentPanel({ documents, selectedDoc, onSelect, onUpload, onDelete }) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef(null);

  async function handleFile(file) {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await onUpload(file);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div className="doc-panel">
      <div className="doc-panel-header">
        <h2>Documents</h2>
        <span className="doc-count">{documents.length}</span>
      </div>

      <div
        className={`drop-zone ${dragOver ? "drop-zone--active" : ""} ${uploading ? "drop-zone--uploading" : ""}`}
        onClick={() => !uploading && fileRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.md,.docx"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {uploading ? (
          <div className="uploading-state">
            <span className="spinner spinner--lg" />
            <span>Processing with MinerU…</span>
          </div>
        ) : (
          <>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 4v12M6 10l6-6 6 6" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M4 20h16" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <span>Drop PDF / click to upload</span>
          </>
        )}
      </div>

      {uploadError && <p className="upload-error">{uploadError}</p>}

      <div className="doc-list">
        {documents.length === 0 && !uploading && (
          <p className="doc-empty">No documents yet. Upload one to get started.</p>
        )}
        {documents.map((doc) => (
          <div
            key={doc.doc_id}
            className={`doc-item ${selectedDoc?.doc_id === doc.doc_id ? "doc-item--active" : ""}`}
            onClick={() => onSelect(selectedDoc?.doc_id === doc.doc_id ? null : doc)}
          >
            <div className="doc-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 2h7l3 3v9H3V2z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
                <path d="M10 2v3h3" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
                <path d="M5 8h6M5 10.5h4" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="doc-info">
              <span className="doc-name">{doc.doc_name}</span>
              <span className="doc-meta">{doc.pages} pages</span>
            </div>
            <button
              className="doc-delete"
              onClick={(e) => { e.stopPropagation(); onDelete(doc.doc_id); }}
              aria-label="Delete document"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

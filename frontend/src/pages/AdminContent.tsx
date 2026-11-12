import { useEffect, useState } from "react";
import {
  deleteAdminCollection,
  deleteAdminDocument,
  getAdminCollections,
  getAdminDocuments,
  retryAdminDocument,
  type AdminCollection,
  type AdminDocument,
} from "../api/admin";
import AdminNav from "../components/AdminNav";

const PAGE_SIZE = 50;
const STATUSES = ["", "processed", "processing", "uploaded", "failed"] as const;

function describe(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export default function AdminContent() {
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [total, setTotal] = useState(0);
  const [collections, setCollections] = useState<AdminCollection[]>([]);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState("");

  // Bumped after an action to reload the lists.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getAdminDocuments({ status, search: search.trim(), limit: PAGE_SIZE, offset }),
      getAdminCollections(),
    ])
      .then(([page, allCollections]) => {
        if (cancelled) return;
        setDocuments(page.items);
        setTotal(page.total);
        setCollections(allCollections);
      })
      .catch((reason: unknown) => { if (!cancelled) setError(describe(reason, "Unable to load content.")); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [status, search, offset, reloadToken]);

  async function run(key: string, action: () => Promise<void>, failure: string) {
    setBusyKey(key);
    setError("");
    try {
      await action();
      setLoading(true);
      setReloadToken((value) => value + 1);
    } catch (reason) {
      setError(describe(reason, failure));
    } finally {
      setBusyKey(null);
    }
  }

  function removeDocument(document: AdminDocument) {
    if (!window.confirm(`Delete "${document.filename}" owned by ${document.owner_email}? This removes the file and its chunks and cannot be undone.`)) return;
    void run(`doc-delete-${document.id}`, () => deleteAdminDocument(document.id), "Unable to delete the document.");
  }

  function removeCollection(collection: AdminCollection) {
    if (!window.confirm(`Delete collection "${collection.name}" owned by ${collection.owner_email}? Its ${collection.document_count} documents are kept and become unassigned.`)) return;
    void run(`col-delete-${collection.id}`, () => deleteAdminCollection(collection.id), "Unable to delete the collection.");
  }

  const pageEnd = Math.min(offset + PAGE_SIZE, total);

  return (
    <main className="admin-page dashboard-page">
      <header className="chat-header dashboard-header">
        <div className="chat-header-info"><h1>Content</h1><p>Documents and collections across all users</p></div>
        <AdminNav active="/admin/content" />
      </header>
      {error && <div className="chat-error" role="alert">{error}</div>}

      <section className="dashboard-panel">
        <div className="dashboard-panel-heading"><h2>Documents</h2><span>{total} matching</span></div>
        <div className="dashboard-toolbar admin-content-filters">
          <label>
            Status{" "}
            <select value={status} onChange={(event) => { setLoading(true); setOffset(0); setStatus(event.target.value); }}>
              {STATUSES.map((value) => <option key={value} value={value}>{value || "All"}</option>)}
            </select>
          </label>
          <label>
            Filename{" "}
            <input type="search" value={search} placeholder="Search…" onChange={(event) => { setLoading(true); setOffset(0); setSearch(event.target.value); }} />
          </label>
        </div>
        {loading && <p className="dashboard-empty">Loading documents…</p>}
        <div className="admin-table">
          {documents.map((document) => (
            <div className="admin-row admin-content-row" key={document.id}>
              <span title={document.source_url ?? document.filename}><strong>{document.filename}</strong></span>
              <span>{document.owner_email}</span>
              <span>{document.collection_name ?? "—"}</span>
              <span className={`admin-status admin-status-${document.status}`} title={document.processing_error ?? undefined}>
                {document.status}{document.status === "processed" ? ` · ${document.chunk_count} chunks` : ""}
              </span>
              <span className="admin-row-actions">
                {(document.status === "failed" || document.status === "uploaded") && (
                  <button type="button" className="admin-user-status-button" disabled={busyKey !== null}
                    onClick={() => void run(`doc-retry-${document.id}`, () => retryAdminDocument(document.id), "Unable to retry processing.")}>
                    {busyKey === `doc-retry-${document.id}` ? "Retrying…" : "Retry"}
                  </button>
                )}
                <button type="button" className="admin-user-status-button" disabled={busyKey !== null} onClick={() => removeDocument(document)}>
                  {busyKey === `doc-delete-${document.id}` ? "Deleting…" : "Delete"}
                </button>
              </span>
              {document.processing_error && <p className="failed-case-error admin-row-error">{document.processing_error}</p>}
            </div>
          ))}
          {!loading && !documents.length && <p className="dashboard-empty">No documents match these filters.</p>}
        </div>
        {total > PAGE_SIZE && (
          <div className="dashboard-toolbar">
            <button type="button" disabled={offset === 0} onClick={() => { setLoading(true); setOffset(Math.max(0, offset - PAGE_SIZE)); }}>Previous</button>
            <span>{offset + 1}–{pageEnd} of {total}</span>
            <button type="button" disabled={pageEnd >= total} onClick={() => { setLoading(true); setOffset(offset + PAGE_SIZE); }}>Next</button>
          </div>
        )}
      </section>

      <section className="dashboard-panel">
        <div className="dashboard-panel-heading"><h2>Collections</h2><span>{collections.length} total</span></div>
        <div className="admin-table">
          {collections.map((collection) => (
            <div className="admin-row" key={collection.id}>
              <span><strong>{collection.name}</strong></span>
              <span>{collection.owner_email}</span>
              <span>{collection.document_count} documents</span>
              <button type="button" className="admin-user-status-button" disabled={busyKey !== null} onClick={() => removeCollection(collection)}>
                {busyKey === `col-delete-${collection.id}` ? "Deleting…" : "Delete"}
              </button>
            </div>
          ))}
          {!loading && !collections.length && <p className="dashboard-empty">No collections yet.</p>}
        </div>
      </section>
    </main>
  );
}

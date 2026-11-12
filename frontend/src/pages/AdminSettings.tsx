import { useEffect, useState } from "react";
import AdminNav from "../components/AdminNav";
import { getRagSettings, updateRagSettings, type RagSettings } from "../api/admin";

export default function AdminSettings() {
  const [settings, setSettings] = useState<RagSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getRagSettings().then(setSettings)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load RAG settings."))
      .finally(() => setLoading(false));
  }, []);

  function setValue<K extends keyof RagSettings>(key: K, value: RagSettings[K]) {
    setSettings((current) => current ? { ...current, [key]: value } : current);
  }

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!settings) return;
    setSaving(true); setError(""); setMessage("");
    try {
      const saved = await updateRagSettings(settings);
      setSettings(saved); setMessage("RAG settings saved. New requests will use these values.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save RAG settings.");
    } finally { setSaving(false); }
  }

  return (
    <main className="admin-page dashboard-page">
      <header className="chat-header dashboard-header"><div className="chat-header-info"><h1>RAG settings</h1><p>Adjust generation, retrieval, reranking, and ingestion defaults</p></div>
        <AdminNav active="/admin/settings" />
      </header>
      {loading && <p className="dashboard-empty">Loading settings…</p>}
      {error && <div className="chat-error" role="alert">{error}</div>}
      {message && <div className="settings-success" role="status">{message}</div>}
      {settings && <form className="dashboard-panel settings-form" onSubmit={save}>
        <section><h2>Provider</h2><div className="settings-fields">
          <label>Primary provider<select value={settings.provider} onChange={(event) => setValue("provider", event.target.value as RagSettings["provider"])}><option value="ollama">Ollama</option><option value="gemini">Gemini</option></select></label>
          <label>Fallback provider<select value={settings.fallback_provider} onChange={(event) => setValue("fallback_provider", event.target.value as RagSettings["fallback_provider"])}><option value="">Disabled</option><option value="ollama" disabled={settings.provider === "ollama"}>Ollama</option><option value="gemini" disabled={settings.provider === "gemini"}>Gemini</option></select></label>
          <label>Ollama model<input value={settings.ollama_model} maxLength={255} onChange={(event) => setValue("ollama_model", event.target.value)} /></label>
          <label>Gemini model<input value={settings.gemini_model} maxLength={255} onChange={(event) => setValue("gemini_model", event.target.value)} /></label>
        </div><p className="settings-help">Fallback is attempted when the primary provider fails before returning a response. Ensure its credentials and service are configured.</p></section>

        <section><h2>Retrieval and context</h2><div className="settings-fields">
          <label>Final retrieval count<input type="number" min={1} max={20} value={settings.retrieval_top_k} onChange={(event) => setValue("retrieval_top_k", Number(event.target.value))} /></label>
          <label>Candidate multiplier<input type="number" min={1} max={10} value={settings.candidate_multiplier} onChange={(event) => setValue("candidate_multiplier", Number(event.target.value))} /></label>
          <label>Reranked chunk count<input type="number" min={1} max={20} value={settings.rerank_limit} onChange={(event) => setValue("rerank_limit", Number(event.target.value))} /></label>
          <label>Minimum reranker score<input type="number" min={-100} max={100} step={0.1} value={settings.minimum_reranker_score} onChange={(event) => setValue("minimum_reranker_score", Number(event.target.value))} /></label>
          <label>Context character budget<input type="number" min={1000} max={100000} step={1000} value={settings.max_context_chars} onChange={(event) => setValue("max_context_chars", Number(event.target.value))} /></label>
          <label>Generation temperature<input type="number" min={0} max={2} step={0.1} value={settings.temperature} onChange={(event) => setValue("temperature", Number(event.target.value))} /></label>
          <label>Maximum answer tokens<input type="number" min={64} max={8192} step={64} value={settings.max_output_tokens} onChange={(event) => setValue("max_output_tokens", Number(event.target.value))} /></label>
        </div></section>

        <section><h2>Document chunking</h2><div className="settings-fields">
          <label>Chunk token limit<input type="number" min={100} max={2000} value={settings.chunk_size} onChange={(event) => setValue("chunk_size", Number(event.target.value))} /></label>
          <label>Token overlap<input type="number" min={0} max={settings.chunk_size - 1} value={settings.chunk_overlap} onChange={(event) => setValue("chunk_overlap", Number(event.target.value))} /></label>
        </div><p className="settings-help">Chunking changes apply to documents processed after saving. Existing chunks are not rewritten.</p></section>

        <section><h2>Estimated token cost</h2><div className="settings-fields">
          <label>Input USD per 1,000 tokens<input type="number" min={0} max={1000} step={0.0001} value={settings.input_cost_per_1k_tokens_usd} onChange={(event) => setValue("input_cost_per_1k_tokens_usd", Number(event.target.value))} /></label>
          <label>Output USD per 1,000 tokens<input type="number" min={0} max={1000} step={0.0001} value={settings.output_cost_per_1k_tokens_usd} onChange={(event) => setValue("output_cost_per_1k_tokens_usd", Number(event.target.value))} /></label>
        </div><p className="settings-help">Cost is an estimate based on token counts and rates you enter; set the current provider/model rates. Actual billing can differ.</p></section>

        <section><h2>Redis answer cache</h2><div className="settings-fields">
          <label>Enable verified answer cache<select value={String(settings.query_cache_enabled)} onChange={(event) => setValue("query_cache_enabled", event.target.value === "true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label>
          <label>Cache lifetime in seconds<input type="number" min={1} max={3600} value={settings.query_cache_ttl_seconds} onChange={(event) => setValue("query_cache_ttl_seconds", Number(event.target.value))} /></label>
        </div><p className="settings-help">Entries are scoped by user, conversation history, retrieval scope, prompt settings, and chunk index/version. Redis errors bypass the cache safely.</p></section>

        <section><h2>Embeddings</h2><div className="settings-fields"><label>Embedding model<input value={settings.embedding_model} readOnly /></label><label>Vector dimensions<input value={settings.embedding_dimensions} readOnly /></label></div>
          <p className="settings-help">Set EMBEDDING_MODEL in deployment configuration. This build supports two 384-dimensional models. Changing it requires a database backup, stopping API/worker services, and running `python -m app.maintenance.reindex_embeddings --confirm-reindex` before bringing the app back online.</p></section>
        <div className="settings-actions"><button type="submit" disabled={saving}>{saving ? "Saving…" : "Save settings"}</button></div>
      </form>}
    </main>
  );
}

import { useEffect, useMemo, useState } from "react";
import AdminNav from "../components/AdminNav";

import {
  getAdminAnalytics,
  getAdminSummary,
  getAdminUsers,
  updateAdminUserStatus,
  type AdminAnalytics,
  type AdminSummary,
  type AdminUser,
} from "../api/admin";

function TrendChart({ data, metric }: { data: AdminAnalytics["daily"]; metric: "queries" | "average_latency_ms" }) {
  const points = useMemo(() => {
    if (!data.length) return "";
    const max = Math.max(1, ...data.map((point) => point[metric]));
    return data.map((point, index) => {
      const x = data.length === 1 ? 50 : (index / (data.length - 1)) * 100;
      const y = 90 - (point[metric] / max) * 78;
      return `${x},${y}`;
    }).join(" ");
  }, [data, metric]);

  if (!data.length) return <p className="dashboard-empty">No query history for this period yet.</p>;
  return (
    <div className="dashboard-chart-wrap">
      <svg className="dashboard-chart" viewBox="0 0 100 100" role="img" aria-label={metric === "queries" ? "Queries per day trend" : "Average latency per day trend"}>
        <line x1="0" y1="90" x2="100" y2="90" className="chart-axis" />
        <polyline points={points} className="chart-line" />
      </svg>
      <div className="chart-labels"><span>{data[0].date}</span><span>{data[data.length - 1].date}</span></div>
    </div>
  );
}

export default function Admin() {
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [days, setDays] = useState(30);
  const [loadedDays, setLoadedDays] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null);

  async function toggleUserStatus(user: AdminUser) {
    setUpdatingUserId(user.id);
    setError("");
    try {
      const updated = await updateAdminUserStatus(user.id, !user.is_active);
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to update this account.");
    } finally {
      setUpdatingUserId(null);
    }
  }

  useEffect(() => {
    let active = true;
    Promise.all([getAdminSummary(), getAdminUsers(), getAdminAnalytics(days)])
      .then(([nextSummary, nextUsers, nextAnalytics]) => {
        if (!active) return;
        setSummary(nextSummary);
        setUsers(nextUsers);
        setAnalytics(nextAnalytics);
        setError("");
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Unable to load admin data.");
      })
      .finally(() => {
        if (active) setLoadedDays(days);
      });
    return () => { active = false; };
  }, [days]);

  const loading = loadedDays !== days;

  return (
    <main className="admin-page dashboard-page">
      <header className="chat-header dashboard-header">
        <div className="chat-header-info">
          <h1>Administration</h1>
          <p>Usage, latency, and platform activity</p>
        </div>
        <AdminNav active="/admin" />
      </header>

      {error && <div className="chat-error" role="alert">{error}</div>}
      {loading && <p className="dashboard-empty">Loading analytics…</p>}

      {analytics && (
        <>
          <div className="dashboard-toolbar">
            <label htmlFor="analytics-period">Time period</label>
            <select id="analytics-period" value={days} onChange={(event) => setDays(Number(event.target.value))}>
              <option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option>
            </select>
          </div>
          <section className="dashboard-stats" aria-label="Usage metrics">
            <article><span>Queries</span><strong>{analytics.total_queries}</strong></article>
            <article><span>Failures</span><strong>{analytics.failed_queries}</strong></article>
            <article><span>Fallback answers</span><strong>{analytics.fallback_queries}</strong></article>
            <article><span>Answer cache hits</span><strong>{analytics.cache_hits}</strong></article>
            <article><span>Average latency</span><strong>{analytics.average_latency_ms} ms</strong></article>
            <article><span>95th percentile</span><strong>{analytics.p95_latency_ms} ms</strong></article>
            <article><span>Retrieval + reranking</span><strong>{analytics.retrieval_latency_ms} ms</strong></article>
            <article><span>Generation</span><strong>{analytics.generation_latency_ms} ms</strong></article>
            <article><span>Citation verification</span><strong>{analytics.verification_latency_ms} ms</strong></article>
            <article><span>Retrieved chunks</span><strong>{analytics.retrieved_chunks}</strong></article>
            <article><span>Citations</span><strong>{analytics.citations}</strong></article>
            <article><span>Estimated tokens</span><strong>{(analytics.prompt_tokens + analytics.completion_tokens).toLocaleString()}</strong></article>
            <article><span>Estimated cost</span><strong>${analytics.estimated_cost_usd.toFixed(4)}</strong></article>
          </section>
          <div className="dashboard-grid">
            <section className="dashboard-panel">
              <div className="dashboard-panel-heading"><h2>Query volume</h2><span>Queries per day</span></div>
              <TrendChart data={analytics.daily} metric="queries" />
            </section>
            <section className="dashboard-panel">
              <div className="dashboard-panel-heading"><h2>Latency trend</h2><span>Average request latency in ms</span></div>
              <TrendChart data={analytics.daily} metric="average_latency_ms" />
            </section>
            <section className="dashboard-panel">
              <div className="dashboard-panel-heading"><h2>Provider usage</h2><span>Requests and estimated tokens</span></div>
              {analytics.providers.length ? analytics.providers.map((provider) => (
                <div className="provider-row" key={`${provider.provider}-${provider.model}`}>
                  <div><strong>{provider.provider} · {provider.model}</strong><span>{provider.queries} queries · {provider.failures} failures</span></div>
                  <div><strong>{provider.average_latency_ms} ms</strong><span>{(provider.prompt_tokens + provider.completion_tokens).toLocaleString()} estimated tokens · ${provider.estimated_cost_usd.toFixed(4)}</span></div>
                </div>
              )) : <p className="dashboard-empty">No provider usage recorded.</p>}
            </section>
          </div>
        </>
      )}

      {summary && (
        <section className="dashboard-panel dashboard-users">
          <div className="dashboard-panel-heading"><h2>Users and documents</h2><span>{summary.users} users · {summary.documents} documents · {summary.processing_jobs} processing jobs</span></div>
          <div className="admin-table">
            {users.map((user) => (
              <div className="admin-row" key={user.id}>
                <span>{user.username}</span><span>{user.email}</span><span>{user.is_active ? "Active" : "Inactive"}</span>
                {user.can_change_status && (
                  <button
                    type="button"
                    className="admin-user-status-button"
                    disabled={updatingUserId !== null}
                    onClick={() => void toggleUserStatus(user)}
                  >
                    {updatingUserId === user.id ? "Saving…" : user.is_active ? "Deactivate" : "Reactivate"}
                  </button>
                )}
              </div>
            ))}
            {!users.length && <p className="dashboard-empty">No users found.</p>}
          </div>
        </section>
      )}
    </main>
  );
}

import { useEffect, useState } from "react";

import {
  getAdminSummary,
  getAdminUsers,
  type AdminSummary,
  type AdminUser,
} from "../api/admin";

export default function Admin() {
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getAdminSummary(), getAdminUsers()])
      .then(([nextSummary, nextUsers]) => {
        setSummary(nextSummary);
        setUsers(nextUsers);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Unable to load admin data.");
      });
  }, []);

  return (
    <main className="admin-page">
      <header className="chat-header">
        <div className="chat-header-info">
          <h1>Administration</h1>
          <p>System usage and user management</p>
        </div>
      </header>

      {error && <div className="chat-error">{error}</div>}

      {summary && (
        <section className="admin-stats">
          <div><strong>{summary.users}</strong><span>Users</span></div>
          <div><strong>{summary.documents}</strong><span>Documents</span></div>
          <div><strong>{summary.queries}</strong><span>Queries</span></div>
          <div><strong>{summary.average_query_latency_ms} ms</strong><span>Average latency</span></div>
        </section>
      )}

      <section className="admin-table-section">
        <h2>Users</h2>
        <div className="admin-table">
          {users.map((user) => (
            <div className="admin-row" key={user.id}>
              <span>{user.username}</span>
              <span>{user.email}</span>
              <span>{user.is_active ? "Active" : "Inactive"}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

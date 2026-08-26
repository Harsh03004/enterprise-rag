import { useAuth } from "../context/AuthContext";

export default function Header() {
  const { logout } = useAuth();

  return (
    <header className="app-header">
      <div className="header-brand">
        <h2>Enterprise RAG</h2>
      </div>

      <div className="header-actions">
        <button onClick={logout}>
          Logout
        </button>
      </div>
    </header>
  );
}
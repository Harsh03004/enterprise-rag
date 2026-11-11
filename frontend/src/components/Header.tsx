import { useAuth } from "../context/useAuth";
import { Link } from "react-router-dom";

export default function Header() {
  const { logout, isAdmin } = useAuth();

  return (
    <header className="app-header">
      <div className="header-brand">
        <h2>Enterprise RAG</h2>
      </div>

      <div className="header-actions">
        {isAdmin && <Link to="/admin">Administration</Link>}
        <button onClick={logout}>
          Logout
        </button>
      </div>
    </header>
  );
}

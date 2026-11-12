import { useAuth } from "../context/useAuth";
import { Link } from "react-router-dom";

interface HeaderProps {
  // Provided by the chat layout; the button only shows on narrow screens.
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export default function Header({ sidebarOpen = false, onToggleSidebar }: HeaderProps) {
  const { logout, isAdmin } = useAuth();

  return (
    <header className="app-header">
      <div className="header-brand">
        {onToggleSidebar && (
          <button
            type="button"
            className="header-menu-button"
            aria-label={sidebarOpen ? "Close projects and chats" : "Open projects and chats"}
            aria-expanded={sidebarOpen}
            aria-controls="app-sidebar"
            onClick={onToggleSidebar}
          >
            <span aria-hidden="true">{sidebarOpen ? "\u2715" : "\u2630"}</span>
          </button>
        )}
        <h2>Enterprise RAG</h2>
      </div>

      <div className="header-actions">
        <Link to="/settings">Settings</Link>
        {isAdmin && <Link to="/admin">Administration</Link>}
        <button onClick={logout}>
          Logout
        </button>
      </div>
    </header>
  );
}

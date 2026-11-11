import { Navigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, authLoading } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (authLoading) return <main className="route-loading">Checking administrator access…</main>;
  if (!isAdmin) return <Navigate to="/chat" replace />;
  return children;
}

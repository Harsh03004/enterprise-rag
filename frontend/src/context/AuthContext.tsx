import {
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { AuthContext, TOKEN_KEY } from "./auth-context";
import { getCurrentUser } from "../api/auth";
import { AUTH_EXPIRED_EVENT } from "../api/client";

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY);
  });
  const [isAdmin, setIsAdmin] = useState(false);
  const [authLoading, setAuthLoading] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)));

  useEffect(() => {
    if (!token) return;

    let active = true;
    getCurrentUser()
      .then((user) => { if (active) setIsAdmin(user.is_admin); })
      .catch(() => { if (active) setIsAdmin(false); })
      .finally(() => { if (active) setAuthLoading(false); });
    return () => { active = false; };
  }, [token]);

  useEffect(() => {
    function clearExpiredSession() {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setIsAdmin(false);
      setAuthLoading(false);
    }

    window.addEventListener(AUTH_EXPIRED_EVENT, clearExpiredSession);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, clearExpiredSession);
  }, []);

  function login(newToken: string) {
    localStorage.setItem(TOKEN_KEY, newToken);
    setIsAdmin(false);
    setAuthLoading(true);
    setToken(newToken);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setIsAdmin(false);
    setAuthLoading(false);
    setToken(null);
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: token !== null,
        isAdmin,
        authLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

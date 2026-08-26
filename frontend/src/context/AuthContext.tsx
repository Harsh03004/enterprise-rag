import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);

const TOKEN_KEY = "enterprise_rag_token";

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY);
  });

  function login(newToken: string) {
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: token !== null,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider",
    );
  }

  return context;
}
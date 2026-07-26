import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCurrentUser,
  getStoredToken,
  loginUser,
  removeStoredToken,
  storeToken,
} from "../services/authService";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(getStoredToken());
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    removeStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  const loadCurrentUser = useCallback(
    async (accessToken) => {
      try {
        const response = await getCurrentUser(accessToken);
        setUser(response.user);
      } catch (error) {
        console.error("Session validation failed:", error);
        logout();
      } finally {
        setLoading(false);
      }
    },
    [logout],
  );

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    loadCurrentUser(token);
  }, [token, loadCurrentUser]);

  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener(
      "auth:unauthorized",
      handleUnauthorized,
    );

    return () => {
      window.removeEventListener(
        "auth:unauthorized",
        handleUnauthorized,
      );
    };
  }, [logout]);

  const login = useCallback(async (email, password) => {
    const response = await loginUser(email, password);

    const accessToken = response.access_token;

    if (!accessToken) {
      throw new Error("Access token was not returned.");
    }

    storeToken(accessToken);
    setToken(accessToken);

    if (response.user) {
      setUser(response.user);
    } else {
      const profileResponse =
        await getCurrentUser(accessToken);

      setUser(profileResponse.user);
    }

    return response;
  }, []);

  const hasRole = useCallback(
    (...roles) => {
      return Boolean(user && roles.includes(user.role));
    },
    [user],
  );

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(user && token),
      login,
      logout,
      hasRole,
    }),
    [user, token, loading, login, logout, hasRole],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
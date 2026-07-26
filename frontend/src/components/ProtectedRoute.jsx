import { Navigate, useLocation } from "react-router-dom";
import useAuth from "../hooks/useAuth";

export default function ProtectedRoute({
  children,
  allowedRoles,
}) {
  const {
    isAuthenticated,
    loading,
    user,
  } = useAuth();

  const location = useLocation();

  if (loading) {
    return (
      <div className="auth-loader-page">
        <div className="auth-spinner" />
        <p>Checking your session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname }}
      />
    );
  }

  if (
    allowedRoles?.length &&
    !allowedRoles.includes(user?.role)
  ) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
}
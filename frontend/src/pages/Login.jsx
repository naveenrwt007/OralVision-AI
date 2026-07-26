import { useEffect, useState } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import useAuth from "../hooks/useAuth";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    login,
    isAuthenticated,
    loading: authLoading,
  } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] =
    useState(false);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] = useState("");

  const redirectPath =
    location.state?.from || "/";

  useEffect(() => {
    setError("");
  }, [form.email, form.password]);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.email.trim() || !form.password) {
      setError(
        "Please enter your email and password."
      );
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      await login(
        form.email.trim(),
        form.password
      );

      navigate(redirectPath, {
        replace: true,
      });
    } catch (loginError) {
      setError(
        loginError.message ||
          "Unable to log in. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (!authLoading && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <main className="login-page">
      <section className="login-brand-panel">
        <div className="login-brand-content">
          <div className="login-brand-icon">
            OV
          </div>

          <h1>OralVision</h1>

          <p>
            Explainable AI-assisted preliminary oral
            cancer screening.
          </p>

          <div className="security-message">
            Secure clinical access for authorized
            healthcare professionals.
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <form
          className="login-card"
          onSubmit={handleSubmit}
          noValidate
        >
          <div className="login-heading">
            <p className="login-label">
              SECURE ACCESS
            </p>

            <h2>Welcome back</h2>

            <p>
              Enter your registered credentials to
              continue.
            </p>
          </div>

          {error && (
            <div
              className="login-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <label className="form-field">
            <span>Email address</span>

            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="doctor@example.com"
              autoComplete="email"
              disabled={submitting}
            />
          </label>

          <label className="form-field">
            <span>Password</span>

            <div className="password-input-wrapper">
              <input
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={submitting}
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword(
                    (previous) => !previous
                  )
                }
                aria-label={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
              >
                {showPassword
                  ? "Hide"
                  : "Show"}
              </button>
            </div>
          </label>

          <button
            type="submit"
            className="login-button"
            disabled={submitting}
          >
            {submitting
              ? "Signing in..."
              : "Sign in"}
          </button>

          <p className="auth-switch">
            New to OralVision?{" "}
            <Link to="/register">Create an account</Link>
          </p>

          <p className="login-disclaimer">
            OralVision provides preliminary screening
            support only. Diagnosis requires examination
            and biopsy by a qualified medical
            professional.
          </p>
        </form>
      </section>
    </main>
  );
}
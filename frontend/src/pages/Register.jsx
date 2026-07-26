import { useEffect, useState } from "react";
import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";

import useAuth from "../hooks/useAuth";
import { signupUser } from "../services/authService";
import "./Login.css";
import "./Register.css";

export default function Register() {
  const navigate = useNavigate();
  const {
    isAuthenticated,
    loading: authLoading,
  } = useAuth();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "doctor",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setError("");
  }, [
    form.name,
    form.email,
    form.password,
    form.confirmPassword,
    form.role,
  ]);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (form.name.trim().length < 2) {
      setError("Please enter your full name.");
      return;
    }

    if (!form.email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    if (form.password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      setSuccess("");

      await signupUser({
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        role: form.role,
      });

      setSuccess(
        "Registration successful. You can now sign in."
      );

      window.setTimeout(() => {
        navigate("/login", {
          replace: true,
          state: {
            registeredEmail:
              form.email.trim().toLowerCase(),
          },
        });
      }, 900);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to create your account."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (!authLoading && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <main className="login-page register-page">
      <section className="login-brand-panel">
        <div className="login-brand-content">
          <div className="login-brand-icon">OV</div>

          <h1>Join OralVision</h1>

          <p>
            Create a secure clinical account for
            AI-assisted preliminary oral cancer screening.
          </p>

          <div className="security-message">
            Registration is available for healthcare
            professionals and screening technicians.
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <form
          className="login-card register-card"
          onSubmit={handleSubmit}
          noValidate
        >
          <div className="login-heading">
            <p className="login-label">
              CREATE ACCOUNT
            </p>

            <h2>Register</h2>

            <p>
              Enter your details to create an OralVision
              account.
            </p>
          </div>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          {success && (
            <div className="register-success">
              {success}
            </div>
          )}

          <label className="form-field">
            <span>Full name</span>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Enter your full name"
              disabled={submitting}
              autoComplete="name"
            />
          </label>

          <label className="form-field">
            <span>Email address</span>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="doctor@example.com"
              disabled={submitting}
              autoComplete="email"
            />
          </label>

          <label className="form-field">
            <span>Professional role</span>
            <select
              name="role"
              value={form.role}
              onChange={handleChange}
              disabled={submitting}
            >
              <option value="doctor">Doctor</option>
              <option value="technician">
                Screening technician
              </option>
            </select>
          </label>

          <label className="form-field">
            <span>Password</span>

            <div className="password-input-wrapper">
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="Minimum 8 characters"
                disabled={submitting}
                autoComplete="new-password"
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword((current) => !current)
                }
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </label>

          <label className="form-field">
            <span>Confirm password</span>
            <input
              type={showPassword ? "text" : "password"}
              name="confirmPassword"
              value={form.confirmPassword}
              onChange={handleChange}
              placeholder="Re-enter your password"
              disabled={submitting}
              autoComplete="new-password"
            />
          </label>

          <button
            type="submit"
            className="login-button"
            disabled={submitting}
          >
            {submitting
              ? "Creating account..."
              : "Create account"}
          </button>

          <p className="auth-switch">
            Already registered?{" "}
            <Link to="/login">Sign in</Link>
          </p>
        </form>
      </section>
    </main>
  );
}

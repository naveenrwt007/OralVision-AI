import { useState } from "react";
import useAuth from "../hooks/useAuth";
import { registerUser } from "../services/authService";
import "./Users.css";

export default function Users() {
  const { token, user } = useAuth();

  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [createdUsers, setCreatedUsers] = useState([]);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "doctor",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const visibleUsers = createdUsers.filter((item) => {
    const query = search.trim().toLowerCase();

    if (!query) return true;

    return [item.name, item.email, item.role]
      .filter(Boolean)
      .some((value) =>
        String(value).toLowerCase().includes(query)
      );
  });

  function updateField(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
  }

  function closeModal() {
    if (submitting) return;

    setModalOpen(false);
    setError("");
    setSuccess("");
    setForm({
      name: "",
      email: "",
      password: "",
      role: "doctor",
    });
  }

  async function createUser(event) {
    event.preventDefault();

    if (form.name.trim().length < 2) {
      setError("Enter a valid full name.");
      return;
    }

    if (!form.email.trim()) {
      setError("Enter a valid email address.");
      return;
    }

    if (form.password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      const response = await registerUser(token, {
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        role: form.role,
      });

      if (response?.user) {
        setCreatedUsers((current) => [
          response.user,
          ...current,
        ]);
      }

      setSuccess("User created successfully.");

      window.setTimeout(() => {
        closeModal();
      }, 700);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to create the user."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="emr-page ov-users-page">
      <header className="emr-page-header">
        <div>
          <span>Administration</span>
          <h1>User management</h1>
          <p>
            Create and manage secure OralVision accounts.
          </p>
        </div>

        <button
          type="button"
          className="emr-primary"
          onClick={() => setModalOpen(true)}
        >
          + New user
        </button>
      </header>

      <section className="ov-users-summary">
        <article>
          <span>Current administrator</span>
          <strong>{user?.name || "Administrator"}</strong>
          <small>{user?.email || "—"}</small>
        </article>

        <article>
          <span>Created this session</span>
          <strong>{createdUsers.length}</strong>
          <small>New user accounts</small>
        </article>

        <article>
          <span>Allowed roles</span>
          <strong>3</strong>
          <small>Admin · Doctor · Technician</small>
        </article>
      </section>

      <section className="emr-panel ov-users-panel">
        <div className="ov-users-toolbar">
          <div>
            <h2>Users</h2>
            <p>
              Accounts created during this session appear below.
            </p>
          </div>

          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search name, email, or role"
          />
        </div>

        {visibleUsers.length ? (
          <div className="emr-table-wrap flat">
            <table className="emr-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>

              <tbody>
                {visibleUsers.map((item) => (
                  <tr key={item.id || item.email}>
                    <td>
                      <div className="patient-cell">
                        <span className="avatar">
                          {(item.name || "U")[0]}
                        </span>

                        <span>
                          <strong>{item.name}</strong>
                          <small>{item.id || "New account"}</small>
                        </span>
                      </div>
                    </td>

                    <td>{item.email}</td>

                    <td>
                      <span className="ov-role-badge">
                        {item.role}
                      </span>
                    </td>

                    <td>
                      <span className="ov-status-active">
                        Active
                      </span>
                    </td>

                    <td>
                      {item.created_at
                        ? new Date(
                            item.created_at
                          ).toLocaleString()
                        : "Just now"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="emr-empty">
            {search
              ? "No users match your search."
              : "No users have been created in this session."}
          </div>
        )}
      </section>

      {modalOpen && (
        <div
          className="ov-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeModal();
            }
          }}
        >
          <form
            className="ov-user-modal"
            onSubmit={createUser}
          >
            <div className="ov-modal-header">
              <div>
                <span>Administrator action</span>
                <h2>Create user</h2>
                <p>
                  Add a secure OralVision account.
                </p>
              </div>

              <button
                type="button"
                onClick={closeModal}
                aria-label="Close dialog"
              >
                ×
              </button>
            </div>

            {error && (
              <div className="login-error">{error}</div>
            )}

            {success && (
              <div className="register-success">
                {success}
              </div>
            )}

            <label>
              <span>Full name</span>
              <input
                name="name"
                value={form.name}
                onChange={updateField}
                placeholder="Enter full name"
                disabled={submitting}
              />
            </label>

            <label>
              <span>Email address</span>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={updateField}
                placeholder="doctor@example.com"
                disabled={submitting}
              />
            </label>

            <label>
              <span>Temporary password</span>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={updateField}
                placeholder="Minimum 8 characters"
                disabled={submitting}
                autoComplete="new-password"
              />
            </label>

            <label>
              <span>Role</span>
              <select
                name="role"
                value={form.role}
                onChange={updateField}
                disabled={submitting}
              >
                <option value="doctor">Doctor</option>
                <option value="technician">
                  Technician
                </option>
                <option value="admin">
                  Administrator
                </option>
              </select>
            </label>

            <div className="ov-modal-actions">
              <button
                type="button"
                className="emr-secondary"
                onClick={closeModal}
                disabled={submitting}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="emr-primary"
                disabled={submitting}
              >
                {submitting
                  ? "Creating..."
                  : "Create user"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

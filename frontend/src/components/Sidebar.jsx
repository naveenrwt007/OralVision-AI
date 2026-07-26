import { NavLink } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import "./Sidebar.css";

export default function Sidebar({
  darkMode,
  setDarkMode,
  mobileMenuOpen,
  setMobileMenuOpen,
  onLogout,
}) {
  const { user } = useAuth();

  const links = [
    ["/", "▦", "Dashboard"],
    ["/screening", "+", "Screening"],
    ["/patients", "♙", "Patients"],
    ["/reports", "▤", "Reports"],
    ["/search", "⌕", "Search"],
    ["/statistics", "◔", "Statistics"],
    ["/settings", "⚙", "Settings"],
    ...(user?.role === "admin"
      ? [["/users", "♟", "Users"]]
      : []),
  ];

  const displayName = user?.name || "OralVision User";
  const displayEmail = user?.email || "";
  const displayRole = user?.role || "user";
  const initial = (displayName || displayEmail || "U")
    .charAt(0)
    .toUpperCase();

  return (
    <aside
      className={`emr-sidebar ${
        mobileMenuOpen ? "mobile-open" : ""
      }`}
    >
      <div className="emr-sidebar-top">
        <div className="emr-logo">
          <div className="brand-icon">
            <img
              src="/oralvision-logo.svg"
              alt="OralVision logo"
            />
          </div>

          <div>
            <strong>OralVision</strong>
            <span>AI-powered oral cancer screening</span>
          </div>
        </div>

        <button
          type="button"
          className="emr-sidebar-close"
          onClick={() => setMobileMenuOpen(false)}
          aria-label="Close navigation menu"
        >
          ×
        </button>
      </div>

      <nav className="emr-nav">
        {links.map(([to, icon, label]) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            onClick={() => setMobileMenuOpen(false)}
            className={({ isActive }) =>
              isActive ? "active" : ""
            }
          >
            <span>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="ov-sidebar-account">
        <div className="ov-account-profile">
          <div className="ov-account-avatar">{initial}</div>

          <div className="ov-account-text">
            <strong>{displayName}</strong>
            <span>{displayEmail}</span>
            <small>{displayRole}</small>
          </div>

          <span
            className="ov-online-dot"
            title="Active session"
          />
        </div>

        <div className="ov-account-actions">
          <button
            type="button"
            className="ov-account-action"
            onClick={() =>
              setDarkMode((value) => !value)
            }
          >
            <span>{darkMode ? "☀" : "☾"}</span>
            {darkMode ? "Light mode" : "Dark mode"}
          </button>

          <button
            type="button"
            className="ov-account-action ov-logout-action"
            onClick={onLogout}
          >
            <span>↪</span>
            Sign out
          </button>
        </div>

        <small className="ov-sidebar-version">
          OralVision v1.0 · EfficientNet-B0 · Grad-CAM
        </small>
      </div>
    </aside>
  );
}

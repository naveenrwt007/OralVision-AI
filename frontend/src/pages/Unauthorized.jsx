import { Link } from "react-router-dom";

export default function Unauthorized() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px",
        background: "#f4f8f7",
      }}
    >
      <section
        style={{
          maxWidth: "500px",
          padding: "40px",
          borderRadius: "20px",
          background: "white",
          textAlign: "center",
        }}
      >
        <h1>Access denied</h1>

        <p>
          Your account does not have permission to
          access this page.
        </p>

        <Link to="/dashboard">
          Return to dashboard
        </Link>
      </section>
    </main>
  );
}
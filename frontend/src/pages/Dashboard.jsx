import useAuth from "../hooks/useAuth";

export default function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "40px",
        background: "#f4f8f7",
      }}
    >
      <section
        style={{
          maxWidth: "900px",
          margin: "0 auto",
          padding: "32px",
          borderRadius: "20px",
          background: "white",
          boxShadow:
            "0 18px 50px rgba(21, 57, 51, 0.08)",
        }}
      >
        <h1>OralVision Dashboard</h1>

        <p>
          Welcome, <strong>{user?.name}</strong>
        </p>

        <p>
          Email: {user?.email}
        </p>

        <p>
          Role:{" "}
          <strong>
            {user?.role?.toUpperCase()}
          </strong>
        </p>

        <button
          onClick={logout}
          style={{
            marginTop: "20px",
            padding: "12px 20px",
            border: 0,
            borderRadius: "9px",
            background: "#b91c1c",
            color: "white",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </section>
    </main>
  );
}
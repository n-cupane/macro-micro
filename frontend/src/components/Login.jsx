import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../api";

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      const response = await loginUser(email, password);
      localStorage.setItem("token", response.data.access_token);
      navigate("/dashboard");
    } catch (_err) {
      setError("Credenziali non valide");
    }
  };

  return (
    <main style={styles.page}>
      <section style={styles.card}>
        <h1 style={styles.title}>Accedi</h1>
        <p style={styles.subtitle}>Inserisci le tue credenziali per continuare.</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label} htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="nome@dominio.com"
            style={styles.input}
            required
          />

          <label style={styles.label} htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            style={styles.input}
            required
          />

          {error && <p style={styles.error}>{error}</p>}

          <button type="submit" style={styles.button}>
            Login
          </button>
        </form>
      </section>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    padding: "1rem",
    background: "linear-gradient(135deg, #f2f4f8 0%, #e7edf5 100%)",
  },
  card: {
    width: "100%",
    maxWidth: "420px",
    background: "#ffffff",
    borderRadius: "16px",
    padding: "2rem",
    boxShadow: "0 20px 50px rgba(15, 23, 42, 0.12)",
    border: "1px solid #e5e7eb",
  },
  title: {
    margin: 0,
    fontSize: "1.75rem",
    color: "#0f172a",
  },
  subtitle: {
    marginTop: "0.5rem",
    marginBottom: "1.5rem",
    color: "#475569",
  },
  form: {
    display: "grid",
    gap: "0.75rem",
  },
  label: {
    fontWeight: 600,
    color: "#1e293b",
    fontSize: "0.9rem",
  },
  input: {
    border: "1px solid #cbd5e1",
    borderRadius: "10px",
    padding: "0.75rem 0.9rem",
    fontSize: "1rem",
    outline: "none",
  },
  error: {
    marginTop: "0.25rem",
    marginBottom: "0.25rem",
    color: "#b91c1c",
    fontSize: "0.9rem",
  },
  button: {
    marginTop: "0.5rem",
    border: "none",
    borderRadius: "10px",
    padding: "0.8rem 1rem",
    fontSize: "1rem",
    fontWeight: 700,
    backgroundColor: "#0f766e",
    color: "#ffffff",
    cursor: "pointer",
  },
};

export default Login;

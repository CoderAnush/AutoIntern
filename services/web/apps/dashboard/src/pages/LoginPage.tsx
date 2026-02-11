import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>AutoIntern</h1>
        <h2 style={styles.subtitle}>Login</h2>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formGroup}>
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
              placeholder="your@email.com"
            />
          </div>

          <div style={styles.formGroup}>
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={styles.input}
              placeholder="••••••••"
            />
          </div>

          <button type="submit" disabled={isLoading} style={styles.button}>
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </form>

        <p style={styles.bottomText}>
          Don't have an account?{" "}
          <Link to="/register" style={styles.link}>
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: "flex" as const,
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
  },
  card: {
    background: "white",
    padding: "40px",
    borderRadius: "8px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
    width: "100%",
    maxWidth: "400px",
  },
  title: {
    fontSize: "32px",
    fontWeight: "bold",
    margin: "0 0 10px 0",
    color: "#333",
  },
  subtitle: {
    fontSize: "20px",
    color: "#666",
    margin: "0 0 20px 0",
  },
  form: {
    display: "flex" as const,
    flexDirection: "column" as const,
    gap: "15px",
  },
  formGroup: {
    display: "flex" as const,
    flexDirection: "column" as const,
    gap: "5px",
  },
  input: {
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "14px",
    fontFamily: "inherit",
  },
  button: {
    padding: "12px",
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    borderRadius: "4px",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
    marginTop: "10px",
  },
  error: {
    padding: "10px",
    backgroundColor: "#ffebee",
    color: "#c62828",
    borderRadius: "4px",
    marginBottom: "20px",
    fontSize: "14px",
  },
  bottomText: {
    textAlign: "center" as const,
    marginTop: "20px",
    color: "#666",
    fontSize: "14px",
  },
  link: {
    color: "#4CAF50",
    textDecoration: "none",
    fontWeight: "bold",
  },
};

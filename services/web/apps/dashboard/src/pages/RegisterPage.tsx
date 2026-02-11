import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const { register } = useAuth();
  const navigate = useNavigate();

  const validatePassword = (pwd: string): string[] => {
    const errors: string[] = [];
    if (pwd.length < 8) errors.push("At least 8 characters");
    if (!/[A-Z]/.test(pwd)) errors.push("One uppercase letter");
    if (!/[a-z]/.test(pwd)) errors.push("One lowercase letter");
    if (!/[0-9]/.test(pwd)) errors.push("One number");
    if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(pwd))
      errors.push("One special character (!@#$%^&* etc)");
    return errors;
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const pwd = e.target.value;
    setPassword(pwd);
    setValidationErrors(validatePassword(pwd));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate
    const pwdErrors = validatePassword(password);
    if (pwdErrors.length > 0) {
      setError("Password is too weak. Check requirements above.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password);
      navigate("/login");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>AutoIntern</h1>
        <h2 style={styles.subtitle}>Create Account</h2>

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
              onChange={handlePasswordChange}
              required
              style={styles.input}
              placeholder="••••••••"
            />

            {password && (
              <div style={styles.requirements}>
                <p style={styles.requirementsTitle}>Password must have:</p>
                <ul style={styles.requirementsList}>
                  <li
                    style={{
                      color: password.length >= 8 ? "#4CAF50" : "#999",
                    }}
                  >
                    ✓ At least 8 characters
                  </li>
                  <li
                    style={{
                      color: /[A-Z]/.test(password) ? "#4CAF50" : "#999",
                    }}
                  >
                    ✓ One uppercase letter
                  </li>
                  <li
                    style={{
                      color: /[a-z]/.test(password) ? "#4CAF50" : "#999",
                    }}
                  >
                    ✓ One lowercase letter
                  </li>
                  <li
                    style={{
                      color: /[0-9]/.test(password) ? "#4CAF50" : "#999",
                    }}
                  >
                    ✓ One number
                  </li>
                  <li
                    style={{
                      color: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)
                        ? "#4CAF50"
                        : "#999",
                    }}
                  >
                    ✓ One special character (!@#$%^&* etc)
                  </li>
                </ul>
              </div>
            )}
          </div>

          <div style={styles.formGroup}>
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={styles.input}
              placeholder="••••••••"
            />
            {confirmPassword && password !== confirmPassword && (
              <span style={styles.warning}>Passwords do not match</span>
            )}
          </div>

          <button type="submit" disabled={isLoading} style={styles.button}>
            {isLoading ? "Creating account..." : "Register"}
          </button>
        </form>

        <p style={styles.bottomText}>
          Already have an account?{" "}
          <Link to="/login" style={styles.link}>
            Login here
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
    padding: "20px",
  },
  card: {
    background: "white",
    padding: "40px",
    borderRadius: "8px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
    width: "100%",
    maxWidth: "450px",
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
  requirements: {
    padding: "10px",
    backgroundColor: "#f5f5f5",
    borderRadius: "4px",
    fontSize: "12px",
  },
  requirementsTitle: {
    margin: "0 0 8px 0",
    fontWeight: "bold",
    color: "#666",
  },
  requirementsList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
  },
  warning: {
    color: "#c62828",
    fontSize: "12px",
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

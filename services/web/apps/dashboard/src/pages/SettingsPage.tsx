import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { AutoInternClient } from "@autointern/client";

interface SettingsPageProps {
  apiClient: AutoInternClient;
  onClose: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ apiClient, onClose }) => {
  const { user, logout } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (newPassword !== confirmPassword) {
      setMessage({ type: "error", text: "New passwords do not match" });
      return;
    }

    if (newPassword.length < 8) {
      setMessage({ type: "error", text: "New password must be at least 8 characters" });
      return;
    }

    setIsLoading(true);

    try {
      await apiClient.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });

      setMessage({ type: "success", text: "Password changed successfully" });
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setMessage({ type: "error", text: err.detail || "Failed to change password" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      onClose();
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <div style={styles.modal}>
      <div style={styles.modalContent}>
        <div style={styles.header}>
          <h2 style={styles.title}>Settings</h2>
          <button onClick={onClose} style={styles.closeBtn}>
            ✕
          </button>
        </div>

        {/* Profile Section */}
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Profile</h3>
          <div style={styles.profileInfo}>
            <p style={styles.profileField}>
              <strong>Email:</strong> {user?.email}
            </p>
            <p style={styles.profileField}>
              <strong>Member Since:</strong> {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "-"}
            </p>
          </div>
        </div>

        {/* Password Change Section */}
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Change Password</h3>

          {message && (
            <div
              style={{
                ...styles.message,
                ...(message.type === "error" ? styles.messageError : styles.messageSuccess),
              }}
            >
              {message.text}
            </div>
          )}

          <form onSubmit={handlePasswordChange} style={styles.form}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Current Password</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                required
                style={styles.input}
                placeholder="Enter current password"
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                style={styles.input}
                placeholder="Enter new password"
              />
              <small style={styles.hint}>
                Must be at least 8 characters with uppercase, lowercase, number, and special character
              </small>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                style={styles.input}
                placeholder="Confirm new password"
              />
            </div>

            <button type="submit" style={styles.submitBtn} disabled={isLoading}>
              {isLoading ? "Updating..." : "Update Password"}
            </button>
          </form>
        </div>

        {/* Danger Zone */}
        <div style={styles.section}>
          <h3 style={{ ...styles.sectionTitle, color: "#d32f2f" }}>Danger Zone</h3>
          <button onClick={handleLogout} style={styles.logoutBtn}>
            Logout
          </button>
          <p style={styles.hint}>You will be redirected to login page</p>
        </div>
      </div>
    </div>
  );
};

const styles = {
  modal: {
    position: "fixed" as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.5)",
    display: "flex" as const,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: "white",
    borderRadius: "8px",
    boxShadow: "0 5px 15px rgba(0,0,0,0.3)",
    maxWidth: "500px",
    width: "90%",
    maxHeight: "80vh",
    overflow: "auto" as const,
    padding: "0",
  },
  header: {
    display: "flex" as const,
    justifyContent: "space-between" as const,
    alignItems: "center" as const,
    padding: "20px",
    borderBottom: "1px solid #eee",
  },
  title: {
    margin: 0,
    fontSize: "24px",
    color: "#333",
  },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: "24px",
    cursor: "pointer",
    color: "#999",
  },
  section: {
    padding: "20px",
    borderBottom: "1px solid #eee",
  },
  sectionTitle: {
    margin: "0 0 15px 0",
    fontSize: "16px",
    fontWeight: "bold",
    color: "#333",
  },
  profileInfo: {
    display: "flex" as const,
    flexDirection: "column" as const,
    gap: "10px",
  },
  profileField: {
    margin: 0,
    fontSize: "14px",
    color: "#666",
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
  label: {
    fontSize: "13px",
    fontWeight: "bold",
    color: "#333",
  },
  input: {
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "14px",
  },
  hint: {
    fontSize: "12px",
    color: "#999",
  },
  submitBtn: {
    padding: "12px",
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    borderRadius: "4px",
    fontSize: "14px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  logoutBtn: {
    padding: "12px",
    backgroundColor: "#d32f2f",
    color: "white",
    border: "none",
    borderRadius: "4px",
    fontSize: "14px",
    fontWeight: "bold",
    cursor: "pointer",
    width: "100%",
  },
  message: {
    padding: "10px",
    borderRadius: "4px",
    marginBottom: "15px",
    fontSize: "13px",
  },
  messageSuccess: {
    backgroundColor: "#e8f5e9",
    color: "#2e7d32",
  },
  messageError: {
    backgroundColor: "#ffebee",
    color: "#c62828",
  },
};

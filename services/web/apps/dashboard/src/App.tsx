import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AutoInternClient } from "@autointern/client";
import { AuthProvider } from "./context/AuthContext";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DashboardPage } from "./pages/DashboardPage";

// Initialize API client - adjust baseURL based on environment
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const apiClient = new AutoInternClient(API_BASE_URL);

function App() {
  return (
    <BrowserRouter>
      <AuthProvider apiClient={apiClient}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage apiClient={apiClient} />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { AutoInternClient, JobOut, ResumeOut } from "@autointern/client";
import { JobRecommendations } from "../components/JobRecommendations";
import { SavedJobsManager, SavedJobsViewer } from "../components/SavedJobsManager";
import { JobFilters, type JobFilters as JobFiltersType } from "../components/JobFilters";
import { SettingsPage } from "./SettingsPage";

interface DashboardPageProps {
  apiClient: AutoInternClient;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ apiClient }) => {
  const { user, logout, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<"jobs" | "resumes" | "recommendations" | "saved">("jobs");
  const [jobs, setJobs] = useState<JobOut[]>([]);
  const [resumes, setResumes] = useState<ResumeOut[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedResume, setSelectedResume] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [currentFilters, setCurrentFilters] = useState<JobFiltersType>({});

  // Saved jobs manager
  const savedJobsManager = SavedJobsManager({ apiClient });
  const [savedJobs, setSavedJobs] = useState<JobOut[]>([]);

  // Check auth
  useEffect(() => {
    if (!apiClient.isAuthenticated()) {
      navigate("/login");
    }
  }, [apiClient, navigate]);

  // Load resumes on mount
  useEffect(() => {
    loadResumes();
  }, []);

  // Load jobs on mount
  useEffect(() => {
    loadJobs();
  }, []);

  // Update saved jobs when component mounts or when savedJobsManager updates
  useEffect(() => {
    setSavedJobs(savedJobsManager.getSavedJobs());
  }, []);

  const loadJobs = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const jobsList = await apiClient.listJobs(50, 0);
      setJobs(jobsList);
    } catch (err: any) {
      setError(err.detail || "Failed to load jobs");
    } finally {
      setIsLoading(false);
    }
  };

  const loadResumes = async () => {
    try {
      const resumesList = await apiClient.listResumes(10, 0);
      setResumes(resumesList);
    } catch (err: any) {
      console.error("Failed to load resumes:", err);
    }
  };

  const handleSearchJobs = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setIsLoading(true);
      setError(null);
      const results = await apiClient.searchJobs(searchQuery);

      // Apply filters if any
      let filtered = results;
      if (currentFilters.location) {
        filtered = filtered.filter((j) =>
          j.location.toLowerCase().includes(currentFilters.location!.toLowerCase())
        );
      }

      setJobs(filtered);
    } catch (err: any) {
      setError(err.detail || "Search failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyFilters = (filters: JobFiltersType) => {
    setCurrentFilters(filters);
    setShowFilters(false);

    // Apply filters to current jobs
    let filtered = jobs;

    if (filters.location) {
      filtered = filtered.filter((j) =>
        j.location.toLowerCase().includes(filters.location!.toLowerCase())
      );
    }

    if (filters.keyword) {
      filtered = filtered.filter((j) =>
        j.title.toLowerCase().includes(filters.keyword!.toLowerCase()) ||
        j.description?.toLowerCase().includes(filters.keyword!.toLowerCase())
      );
    }

    setJobs(filtered);
  };

  const handleUploadResume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select a file");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      await apiClient.uploadResume(selectedFile);
      setSelectedFile(null);
      setError(null);
      await loadResumes();
    } catch (err: any) {
      setError(err.detail || "Upload failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteResume = async (resumeId: string) => {
    if (!confirm("Delete this resume?")) return;

    try {
      await apiClient.deleteResume(resumeId);
      await loadResumes();
    } catch (err: any) {
      setError(err.detail || "Delete failed");
    }
  };

  const handleSaveJob = (job: JobOut) => {
    savedJobsManager.saveJob(job);
    setSavedJobs(savedJobsManager.getSavedJobs());
  };

  const handleRemoveSavedJob = (jobId: string) => {
    savedJobsManager.removeSavedJob(jobId);
    setSavedJobs(savedJobsManager.getSavedJobs());
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (err: any) {
      console.error("Logout failed:", err);
    }
  };

  if (authLoading) {
    return <div style={styles.container}>Loading...</div>;
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.headerTitle}>AutoIntern</h1>
          <div style={styles.userSection}>
            <span style={styles.userEmail}>{user?.email}</span>
            <button onClick={() => setShowSettings(true)} style={styles.settingsBtn}>
              ⚙️ Settings
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div style={styles.content}>
        {error && <div style={styles.error}>{error}</div>}

        {/* Tabs */}
        <div style={styles.tabs}>
          <button
            style={{ ...styles.tab, ...(activeTab === "jobs" ? styles.tabActive : {}) }}
            onClick={() => setActiveTab("jobs")}
          >
            Job Search
          </button>
          <button
            style={{ ...styles.tab, ...(activeTab === "recommendations" ? styles.tabActive : {}) }}
            onClick={() => setActiveTab("recommendations")}
          >
            Recommendations
          </button>
          <button
            style={{ ...styles.tab, ...(activeTab === "saved" ? styles.tabActive : {}) }}
            onClick={() => setActiveTab("saved")}
          >
            Saved Jobs ({savedJobs.length})
          </button>
          <button
            style={{ ...styles.tab, ...(activeTab === "resumes" ? styles.tabActive : {}) }}
            onClick={() => setActiveTab("resumes")}
          >
            My Resumes ({resumes.length})
          </button>
        </div>

        {/* Jobs Tab */}
        {activeTab === "jobs" && (
          <div style={styles.tabContent}>
            <form onSubmit={handleSearchJobs} style={styles.searchForm}>
              <input
                type="text"
                placeholder="Search jobs (e.g., 'React Developer', 'Python')"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={styles.searchInput}
              />
              <button type="submit" style={styles.searchBtn} disabled={isLoading}>
                {isLoading ? "Searching..." : "Search"}
              </button>
              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                style={styles.filterBtn}
              >
                🔍 {showFilters ? "Hide" : "Show"} Filters
              </button>
            </form>

            {showFilters && (
              <JobFilters
                onApplyFilters={handleApplyFilters}
                onClearFilters={loadJobs}
              />
            )}

            {isLoading && <p>Loading jobs...</p>}

            {jobs.length === 0 ? (
              <p style={styles.emptyState}>No jobs found. Try searching!</p>
            ) : (
              <div style={styles.jobsList}>
                {jobs.map((job) => (
                  <div key={job.id} style={styles.jobCard}>
                    <div style={styles.jobCardHeader}>
                      <div>
                        <h3 style={styles.jobTitle}>{job.title}</h3>
                        <p style={styles.jobMeta}>{job.location}</p>
                      </div>
                      <button
                        onClick={() => handleSaveJob(job)}
                        style={{
                          ...styles.saveBtn,
                          ...(savedJobsManager.isJobSaved(job.id)
                            ? styles.saveBtnSaved
                            : {}),
                        }}
                        title={savedJobsManager.isJobSaved(job.id) ? "Saved" : "Save"}
                      >
                        {savedJobsManager.isJobSaved(job.id) ? "★" : "☆"}
                      </button>
                    </div>
                    <p style={styles.jobMeta}>
                      <strong>Source:</strong> {job.source}
                    </p>
                    <p style={styles.jobDescription}>
                      {job.description?.substring(0, 200)}...
                    </p>
                    <p style={styles.jobDate}>
                      Posted: {new Date(job.posted_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === "recommendations" && (
          <div style={styles.tabContent}>
            {resumes.length === 0 ? (
              <p style={styles.emptyState}>
                No resumes yet. Upload a resume to see job recommendations!
              </p>
            ) : (
              <>
                <div style={styles.resumeSelector}>
                  <label style={styles.label}>Select a resume to get recommendations:</label>
                  <select
                    value={selectedResume || ""}
                    onChange={(e) => setSelectedResume(e.target.value)}
                    style={styles.selectInput}
                  >
                    <option value="">Choose a resume...</option>
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.file_name}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedResume && (
                  <JobRecommendations apiClient={apiClient} resumeId={selectedResume} />
                )}
              </>
            )}
          </div>
        )}

        {/* Saved Jobs Tab */}
        {activeTab === "saved" && (
          <div style={styles.tabContent}>
            <SavedJobsViewer
              savedJobs={savedJobs}
              onRemoveSavedJob={handleRemoveSavedJob}
            />
          </div>
        )}

        {/* Resumes Tab */}
        {activeTab === "resumes" && (
          <div style={styles.tabContent}>
            <form onSubmit={handleUploadResume} style={styles.uploadForm}>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                style={styles.fileInput}
              />
              <button type="submit" style={styles.uploadBtn} disabled={isLoading || !selectedFile}>
                {isLoading ? "Uploading..." : "Upload Resume"}
              </button>
            </form>

            {resumes.length === 0 ? (
              <p style={styles.emptyState}>
                No resumes uploaded yet. Upload one to get started!
              </p>
            ) : (
              <div style={styles.resumesList}>
                {resumes.map((resume) => (
                  <div key={resume.id} style={styles.resumeCard}>
                    <h3 style={styles.resumeTitle}>{resume.file_name}</h3>
                    <p style={styles.resumeMeta}>
                      <strong>Skills:</strong> {resume.skills.join(", ") || "None detected"}
                    </p>
                    <p style={styles.resumeDate}>
                      Uploaded: {new Date(resume.created_at).toLocaleDateString()}
                    </p>
                    <button
                      onClick={() => handleDeleteResume(resume.id)}
                      style={styles.deleteBtn}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsPage
          apiClient={apiClient}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

const styles = {
  container: {
    display: "flex" as const,
    flexDirection: "column" as const,
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
  },
  header: {
    backgroundColor: "#2c3e50",
    color: "white",
    padding: "20px",
    boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
  },
  headerContent: {
    display: "flex" as const,
    justifyContent: "space-between" as const,
    alignItems: "center" as const,
    maxWidth: "1200px",
    margin: "0 auto",
    width: "100%",
  },
  headerTitle: {
    margin: 0,
    fontSize: "28px",
  },
  userSection: {
    display: "flex" as const,
    alignItems: "center" as const,
    gap: "15px",
  },
  userEmail: {
    fontSize: "14px",
  },
  settingsBtn: {
    padding: "8px 16px",
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "13px",
  },
  content: {
    flex: 1,
    maxWidth: "1200px",
    margin: "0 auto",
    width: "100%",
    padding: "20px",
  },
  error: {
    padding: "15px",
    backgroundColor: "#ffebee",
    color: "#c62828",
    borderRadius: "4px",
    marginBottom: "20px",
  },
  tabs: {
    display: "flex" as const,
    gap: "10px",
    marginBottom: "20px",
    borderBottom: "2px solid #ddd",
    flexWrap: "wrap" as const,
  },
  tab: {
    padding: "12px 20px",
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: "15px",
    borderBottom: "3px solid transparent",
    marginBottom: "-2px",
    color: "#666",
  },
  tabActive: {
    color: "#4CAF50",
    borderBottomColor: "#4CAF50",
  },
  tabContent: {
    backgroundColor: "white",
    padding: "20px",
    borderRadius: "8px",
  },
  searchForm: {
    display: "flex" as const,
    gap: "10px",
    marginBottom: "20px",
    flexWrap: "wrap" as const,
  },
  searchInput: {
    flex: 1,
    minWidth: "250px",
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "14px",
  },
  searchBtn: {
    padding: "10px 20px",
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  filterBtn: {
    padding: "10px 20px",
    backgroundColor: "#2196F3",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  resumeSelector: {
    marginBottom: "20px",
    padding: "15px",
    backgroundColor: "#f0f0f0",
    borderRadius: "8px",
  },
  label: {
    display: "block",
    marginBottom: "8px",
    fontWeight: "bold",
    color: "#333",
  },
  selectInput: {
    width: "100%",
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "14px",
  },
  uploadForm: {
    display: "flex" as const,
    gap: "10px",
    marginBottom: "20px",
  },
  fileInput: {
    flex: 1,
    padding: "10px",
  },
  uploadBtn: {
    padding: "10px 20px",
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  emptyState: {
    textAlign: "center" as const,
    padding: "40px",
    color: "#999",
  },
  jobsList: {
    display: "grid" as const,
    gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
    gap: "15px",
  },
  jobCard: {
    backgroundColor: "#f9f9f9",
    padding: "15px",
    borderRadius: "4px",
    border: "1px solid #eee",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  jobCardHeader: {
    display: "flex" as const,
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "10px",
    gap: "10px",
  },
  jobTitle: {
    margin: "0 0 5px 0",
    fontSize: "16px",
    color: "#333",
  },
  jobMeta: {
    margin: "5px 0",
    fontSize: "13px",
    color: "#666",
  },
  jobDescription: {
    margin: "10px 0",
    fontSize: "13px",
    color: "#555",
    lineHeight: "1.4",
  },
  jobDate: {
    margin: "10px 0 0 0",
    fontSize: "12px",
    color: "#999",
  },
  saveBtn: {
    padding: "5px 10px",
    backgroundColor: "white",
    color: "#FFD700",
    border: "1px solid #FFD700",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "16px",
  },
  saveBtnSaved: {
    backgroundColor: "#FFD700",
    color: "white",
  },
  resumesList: {
    display: "grid" as const,
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: "15px",
  },
  resumeCard: {
    backgroundColor: "#f9f9f9",
    padding: "15px",
    borderRadius: "4px",
    border: "1px solid #eee",
  },
  resumeTitle: {
    margin: "0 0 10px 0",
    fontSize: "16px",
    color: "#333",
  },
  resumeDate: {
    margin: "10px 0",
    fontSize: "12px",
    color: "#999",
  },
  deleteBtn: {
    padding: "8px 12px",
    backgroundColor: "#e74c3c",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "12px",
  },
};


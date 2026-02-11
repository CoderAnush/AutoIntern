import React, { useState, useEffect } from "react";
import { AutoInternClient, JobOut } from "@autointern/client";

export const SavedJobsManager: React.FC<{ apiClient: AutoInternClient }> = ({
  apiClient,
}) => {
  const [savedJobs, setSavedJobs] = useState<JobOut[]>([]);

  // Save job to localStorage
  const saveJob = (job: JobOut) => {
    try {
      const saved = JSON.parse(localStorage.getItem("saved_jobs") || "[]");
      const exists = saved.some((j: JobOut) => j.id === job.id);

      if (!exists) {
        saved.push(job);
        localStorage.setItem("saved_jobs", JSON.stringify(saved));
        updateSavedJobs();
      }
    } catch (err) {
      console.error("Failed to save job:", err);
    }
  };

  // Remove job from saved
  const removeSavedJob = (jobId: string) => {
    try {
      const saved = JSON.parse(localStorage.getItem("saved_jobs") || "[]");
      const filtered = saved.filter((j: JobOut) => j.id !== jobId);
      localStorage.setItem("saved_jobs", JSON.stringify(filtered));
      updateSavedJobs();
    } catch (err) {
      console.error("Failed to remove job:", err);
    }
  };

  // Check if job is saved
  const isJobSaved = (jobId: string): boolean => {
    try {
      const saved = JSON.parse(localStorage.getItem("saved_jobs") || "[]");
      return saved.some((j: JobOut) => j.id === jobId);
    } catch {
      return false;
    }
  };

  // Update saved jobs list
  const updateSavedJobs = () => {
    try {
      const saved = JSON.parse(localStorage.getItem("saved_jobs") || "[]");
      setSavedJobs(saved);
    } catch {
      setSavedJobs([]);
    }
  };

  useEffect(() => {
    updateSavedJobs();
  }, []);

  return {
    saveJob,
    removeSavedJob,
    isJobSaved,
    getSavedJobs: () => savedJobs,
  };
};

/**
 * SavedJobsViewer Component - Display saved jobs
 */
interface SavedJobsViewerProps {
  savedJobs: any[];
  onRemoveSavedJob: (jobId: string) => void;
}

export const SavedJobsViewer: React.FC<SavedJobsViewerProps> = ({
  savedJobs,
  onRemoveSavedJob,
}) => {
  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Saved Jobs ({savedJobs.length})</h2>

      {savedJobs.length === 0 ? (
        <p style={styles.empty}>No saved jobs yet. Save your favorite jobs to view them here!</p>
      ) : (
        <div style={styles.jobsList}>
          {savedJobs.map((job: JobOut) => (
            <div key={job.id} style={styles.jobCard}>
              <div style={styles.jobHeader}>
                <div>
                  <h3 style={styles.jobTitle}>{job.title}</h3>
                  <p style={styles.jobMeta}>{job.location}</p>
                </div>
                <button
                  onClick={() => onRemoveSavedJob(job.id)}
                  style={styles.removeBtn}
                  title="Remove from saved"
                >
                  ✕
                </button>
              </div>
              <p style={styles.jobDesc}>{job.description?.substring(0, 150)}...</p>
              <p style={styles.jobDate}>
                Saved on {new Date().toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: "20px",
  },
  title: {
    fontSize: "22px",
    marginBottom: "15px",
    color: "#333",
  },
  empty: {
    textAlign: "center" as const,
    color: "#999",
    padding: "40px 20px",
  },
  jobsList: {
    display: "grid" as const,
    gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
    gap: "15px",
  },
  jobCard: {
    backgroundColor: "#fff",
    padding: "15px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  jobHeader: {
    display: "flex" as const,
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "10px",
  },
  jobTitle: {
    margin: "0 0 5px 0",
    fontSize: "16px",
    color: "#333",
  },
  jobMeta: {
    margin: "0",
    fontSize: "12px",
    color: "#666",
  },
  jobDesc: {
    margin: "10px 0",
    fontSize: "13px",
    color: "#555",
    lineHeight: "1.4",
  },
  jobDate: {
    margin: "10px 0 0 0",
    fontSize: "11px",
    color: "#999",
  },
  removeBtn: {
    padding: "5px 10px",
    backgroundColor: "#ffebee",
    color: "#c62828",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "bold",
  },
};

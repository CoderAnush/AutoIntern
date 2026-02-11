import React, { useState, useEffect } from "react";
import { AutoInternClient, RecommendationResult, ResumeQualityScore } from "@autointern/client";

interface JobRecommendationsProps {
  apiClient: AutoInternClient;
  resumeId: string;
}

export const JobRecommendations: React.FC<JobRecommendationsProps> = ({
  apiClient,
  resumeId,
}) => {
  const [recommendations, setRecommendations] = useState<RecommendationResult[]>([]);
  const [quality, setQuality] = useState<ResumeQualityScore | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRecommendations();
  }, [resumeId]);

  const loadRecommendations = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load recommendations
      const jobs = await apiClient.getRecommendedJobs(resumeId, 0.5, 10);
      setRecommendations(jobs);

      // Load quality score
      const qualityScore = await apiClient.getResumeQuality(resumeId);
      setQuality(qualityScore);
    } catch (err: any) {
      setError(err.detail || "Failed to load recommendations");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Recommended Jobs for This Resume</h2>

      {error && <div style={styles.error}>{error}</div>}

      {quality && (
        <div style={styles.qualityCard}>
          <h3 style={styles.qualityTitle}>Resume Quality Score</h3>
          <div style={styles.scoreGrid}>
            <div style={styles.scoreItem}>
              <span style={styles.scoreLabel}>Overall</span>
              <div style={styles.scoreBar}>
                <div
                  style={{
                    ...styles.scoreBarFill,
                    width: `${quality.overall_score}%`,
                  }}
                />
              </div>
              <span style={styles.scoreValue}>{quality.overall_score.toFixed(0)}/100</span>
            </div>
            <div style={styles.scoreItem}>
              <span style={styles.scoreLabel}>Text Length</span>
              <span style={styles.scoreValue}>{quality.text_length_score.toFixed(0)}/100</span>
            </div>
            <div style={styles.scoreItem}>
              <span style={styles.scoreLabel}>Skills</span>
              <span style={styles.scoreValue}>{quality.skill_count_score.toFixed(0)}/100</span>
            </div>
            <div style={styles.scoreItem}>
              <span style={styles.scoreLabel}>Completeness</span>
              <span style={styles.scoreValue}>{quality.completeness_score.toFixed(0)}/100</span>
            </div>
          </div>
        </div>
      )}

      {isLoading && <p style={styles.loading}>Loading recommendations...</p>}

      {recommendations.length === 0 ? (
        <p style={styles.empty}>No recommendations yet. This resume may need more details.</p>
      ) : (
        <div style={styles.recommendationsList}>
          {recommendations.map((rec) => (
            <div key={rec.job_id} style={styles.recommendationCard}>
              <div style={styles.recHeader}>
                <h3 style={styles.recTitle}>{rec.job_title}</h3>
                <div style={styles.similarityScore}>
                  <span style={styles.scoreLabel}>Match:</span>
                  <span
                    style={{
                      ...styles.scoreValue,
                      color: rec.similarity_score > 0.7 ? "#4CAF50" : "#ff9800",
                    }}
                  >
                    {(rec.similarity_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <p style={styles.recMeta}>
                <strong>Location:</strong> {rec.job_location}
              </p>

              <p style={styles.recDesc}>{rec.job_description.substring(0, 150)}...</p>

              {rec.matched_skills.length > 0 && (
                <div style={styles.skillsSection}>
                  <strong style={styles.skillsLabel}>Matched Skills:</strong>
                  <div style={styles.skillsTags}>
                    {rec.matched_skills.map((skill) => (
                      <span key={skill} style={styles.skillTag}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {rec.skill_gaps.length > 0 && (
                <div style={styles.skillsSection}>
                  <strong style={styles.skillsLabel}>Skills to Learn:</strong>
                  <div style={styles.skillsTags}>
                    {rec.skill_gaps.map((skill) => (
                      <span key={skill} style={styles.skillTagGap}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
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
    backgroundColor: "#f9f9f9",
    borderRadius: "8px",
    marginBottom: "20px",
  },
  title: {
    fontSize: "22px",
    marginBottom: "15px",
    color: "#333",
  },
  error: {
    padding: "10px",
    backgroundColor: "#ffebee",
    color: "#c62828",
    borderRadius: "4px",
    marginBottom: "15px",
  },
  qualityCard: {
    backgroundColor: "white",
    padding: "15px",
    borderRadius: "8px",
    marginBottom: "20px",
    border: "1px solid #ddd",
  },
  qualityTitle: {
    fontSize: "16px",
    marginBottom: "15px",
    color: "#333",
  },
  scoreGrid: {
    display: "grid" as const,
    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
    gap: "15px",
  },
  scoreItem: {
    display: "flex" as const,
    flexDirection: "column" as const,
    gap: "5px",
  },
  scoreLabel: {
    fontSize: "12px",
    color: "#666",
    fontWeight: "bold",
  },
  scoreValue: {
    fontSize: "14px",
    fontWeight: "bold",
    color: "#4CAF50",
  },
  scoreBar: {
    width: "100%",
    height: "8px",
    backgroundColor: "#eee",
    borderRadius: "4px",
    overflow: "hidden",
  },
  scoreBarFill: {
    height: "100%",
    backgroundColor: "#4CAF50",
    transition: "width 0.3s ease",
  },
  loading: {
    textAlign: "center" as const,
    color: "#999",
    padding: "20px",
  },
  empty: {
    textAlign: "center" as const,
    color: "#999",
    padding: "20px",
  },
  recommendationsList: {
    display: "grid" as const,
    gridTemplateColumns: "repeat(auto-fill, minmax(400px, 1fr))",
    gap: "15px",
  },
  recommendationCard: {
    backgroundColor: "white",
    padding: "15px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  },
  recHeader: {
    display: "flex" as const,
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "10px",
    gap: "10px",
  },
  recTitle: {
    margin: "0",
    fontSize: "16px",
    color: "#333",
    flex: 1,
  },
  similarityScore: {
    display: "flex" as const,
    alignItems: "center",
    gap: "5px",
    padding: "5px 10px",
    backgroundColor: "#f0f0f0",
    borderRadius: "4px",
    whiteSpace: "nowrap" as const,
  },
  recMeta: {
    margin: "8px 0",
    fontSize: "13px",
    color: "#666",
  },
  recDesc: {
    margin: "8px 0",
    fontSize: "13px",
    color: "#555",
    lineHeight: "1.4",
  },
  skillsSection: {
    marginTop: "10px",
    paddingTop: "10px",
    borderTop: "1px solid #eee",
  },
  skillsLabel: {
    fontSize: "12px",
    color: "#666",
    display: "block",
    marginBottom: "8px",
  },
  skillsTags: {
    display: "flex" as const,
    flexWrap: "wrap" as const,
    gap: "5px",
  },
  skillTag: {
    display: "inline-block",
    padding: "4px 8px",
    backgroundColor: "#e8f5e9",
    color: "#2e7d32",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "bold",
  },
  skillTagGap: {
    display: "inline-block",
    padding: "4px 8px",
    backgroundColor: "#fff3e0",
    color: "#e65100",
    borderRadius: "12px",
    fontSize: "12px",
  },
};

import React, { useState } from "react";

interface JobFiltersProps {
  onApplyFilters: (filters: JobFilters) => void;
  onClearFilters: () => void;
}

export interface JobFilters {
  location?: string;
  techStack?: string[];
  keyword?: string;
  minSalary?: number;
  maxSalary?: number;
}

const POPULAR_TECH_STACKS = [
  "React",
  "Node.js",
  "Python",
  "Java",
  "Go",
  "Rust",
  "TypeScript",
  "Vue.js",
  "Angular",
  "Django",
  "FastAPI",
  "Spring Boot",
  "PostgreSQL",
  "MongoDB",
  "Docker",
  "Kubernetes",
];

export const JobFilters: React.FC<JobFiltersProps> = ({ onApplyFilters, onClearFilters }) => {
  const [filters, setFilters] = useState<JobFilters>({});
  const [selectedTech, setSelectedTech] = useState<string[]>([]);

  const handleApplyFilters = () => {
    onApplyFilters({
      ...filters,
      techStack: selectedTech,
    });
  };

  const handleClearFilters = () => {
    setFilters({});
    setSelectedTech([]);
    onClearFilters();
  };

  const toggleTechStack = (tech: string) => {
    setSelectedTech((prev) =>
      prev.includes(tech) ? prev.filter((t) => t !== tech) : [...prev, tech]
    );
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Filter Jobs</h3>

      <div style={styles.filterGroup}>
        <label style={styles.label}>Location</label>
        <input
          type="text"
          placeholder="e.g., San Francisco, Remote"
          value={filters.location || ""}
          onChange={(e) => setFilters({ ...filters, location: e.target.value })}
          style={styles.input}
        />
      </div>

      <div style={styles.filterGroup}>
        <label style={styles.label}>Keyword</label>
        <input
          type="text"
          placeholder="e.g., "Full-time", "Startup""
          value={filters.keyword || ""}
          onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
          style={styles.input}
        />
      </div>

      <div style={styles.filterGroup}>
        <label style={styles.label}>Salary Range</label>
        <div style={styles.salaryInputs}>
          <input
            type="number"
            placeholder="Min"
            value={filters.minSalary || ""}
            onChange={(e) =>
              setFilters({ ...filters, minSalary: e.target.value ? parseInt(e.target.value) : undefined })
            }
            style={styles.salaryInput}
          />
          <span style={styles.salaryDash}>—</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.maxSalary || ""}
            onChange={(e) =>
              setFilters({ ...filters, maxSalary: e.target.value ? parseInt(e.target.value) : undefined })
            }
            style={styles.salaryInput}
          />
          <span style={styles.salaryCurrency}>$k/year</span>
        </div>
      </div>

      <div style={styles.filterGroup}>
        <label style={styles.label}>Technology Stack</label>
        <div style={styles.techGrid}>
          {POPULAR_TECH_STACKS.map((tech) => (
            <button
              key={tech}
              onClick={() => toggleTechStack(tech)}
              style={{
                ...styles.techButton,
                ...(selectedTech.includes(tech) ? styles.techButtonSelected : {}),
              }}
            >
              {tech}
            </button>
          ))}
        </div>
        {selectedTech.length > 0 && (
          <div style={styles.selectedTechs}>
            <small style={styles.selectedCount}>Selected: {selectedTech.length}</small>
          </div>
        )}
      </div>

      <div style={styles.actions}>
        <button onClick={handleApplyFilters} style={styles.applyBtn}>
          Apply Filters
        </button>
        {(filters.location || filters.keyword || selectedTech.length > 0) && (
          <button onClick={handleClearFilters} style={styles.clearBtn}>
            Clear All
          </button>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: "#f5f5f5",
    padding: "20px",
    borderRadius: "8px",
    marginBottom: "20px",
  },
  title: {
    margin: "0 0 15px 0",
    fontSize: "16px",
    fontWeight: "bold",
    color: "#333",
  },
  filterGroup: {
    marginBottom: "15px",
    display: "flex" as const,
    flexDirection: "column" as const,
    gap: "8px",
  },
  label: {
    fontSize: "13px",
    fontWeight: "bold",
    color: "#333",
  },
  input: {
    padding: "8px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "13px",
  },
  salaryInputs: {
    display: "flex" as const,
    alignItems: "center" as const,
    gap: "8px",
  },
  salaryInput: {
    flex: 1,
    padding: "8px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "13px",
  },
  salaryDash: {
    color: "#999",
  },
  salaryCurrency: {
    fontSize: "12px",
    color: "#999",
    whiteSpace: "nowrap" as const,
  },
  techGrid: {
    display: "grid" as const,
    gridTemplateColumns: "repeat(auto-fill, minmax(90px, 1fr))",
    gap: "8px",
  },
  techButton: {
    padding: "8px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    backgroundColor: "white",
    cursor: "pointer",
    fontSize: "12px",
    fontWeight: "bold",
    transition: "all 0.2s ease",
    color: "#666",
  },
  techButtonSelected: {
    backgroundColor: "#4CAF50",
    color: "white",
    borderColor: "#4CAF50",
  },
  selectedTechs: {
    marginTop: "10px",
  },
  selectedCount: {
    color: "#4CAF50",
    fontWeight: "bold",
  },
  actions: {
    display: "flex" as const,
    gap: "10px",
    marginTop: "15px",
  },
  applyBtn: {
    flex: 1,
    padding: "10px",
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "bold",
    fontSize: "13px",
  },
  clearBtn: {
    flex: 1,
    padding: "10px",
    backgroundColor: "#999",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "bold",
    fontSize: "13px",
  },
};

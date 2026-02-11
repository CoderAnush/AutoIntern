import axios, { AxiosInstance } from "axios";
import {
  UserResponse,
  TokenResponse,
  UserCreate,
  UserLogin,
  TokenRefresh,
  PasswordChange,
  ResumeOut,
  JobOut,
  RecommendationResult,
  ResumeQualityScore,
  APIError,
} from "./types";

/**
 * AutoIntern API Client
 * Type-safe TypeScript SDK for the AutoIntern REST API
 */
export class AutoInternClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseURL: string = "http://localhost:8000") {
    this.client = axios.create({
      baseURL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add interceptor to include auth token
    this.client.interceptors.request.use((config) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    // Handle token refresh on 401
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && this.refreshToken && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            await this.refreshAccessToken();
            return this.client(originalRequest);
          } catch (refreshError) {
            this.clearTokens();
            throw refreshError;
          }
        }
        throw error;
      }
    );

    // Load tokens from localStorage
    this.loadTokensFromStorage();
  }

  // ============ Auth Endpoints ============

  /**
   * Register new user with email and password
   */
  async register(userData: UserCreate): Promise<UserResponse> {
    try {
      const response = await this.client.post<UserResponse>("/users/register", userData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Login user and get access/refresh tokens
   */
  async login(credentials: UserLogin): Promise<TokenResponse> {
    try {
      const response = await this.client.post<TokenResponse>("/users/login", credentials);
      const data = response.data;

      // Store tokens
      this.setTokens(data.access_token, data.refresh_token);

      return data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(): Promise<TokenResponse> {
    if (!this.refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await this.client.post<TokenResponse>("/users/refresh-token", {
        refresh_token: this.refreshToken,
      });
      const data = response.data;

      // Update tokens
      this.setTokens(data.access_token, data.refresh_token);

      return data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get current user profile (protected)
   */
  async getCurrentUser(): Promise<UserResponse> {
    try {
      const response = await this.client.get<UserResponse>("/users/me");
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Change user password (protected)
   */
  async changePassword(passwordData: PasswordChange): Promise<void> {
    try {
      await this.client.post("/users/change-password", passwordData);
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Logout user (clears local tokens)
   */
  async logout(): Promise<void> {
    try {
      await this.client.post("/users/logout");
    } finally {
      this.clearTokens();
    }
  }

  // ============ Resume Endpoints ============

  /**
   * Upload resume file (protected)
   */
  async uploadResume(file: File): Promise<ResumeOut> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await this.client.post<ResumeOut>("/resumes/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get single resume by ID (protected)
   */
  async getResume(resumeId: string): Promise<ResumeOut> {
    try {
      const response = await this.client.get<ResumeOut>(`/resumes/${resumeId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * List user's resumes (protected)
   */
  async listResumes(limit: number = 10, offset: number = 0): Promise<ResumeOut[]> {
    try {
      const response = await this.client.get<ResumeOut[]>("/resumes", {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Delete resume by ID (protected)
   */
  async deleteResume(resumeId: string): Promise<void> {
    try {
      await this.client.delete(`/resumes/${resumeId}`);
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ============ Job Endpoints ============

  /**
   * List all jobs with pagination
   */
  async listJobs(limit: number = 20, offset: number = 0): Promise<JobOut[]> {
    try {
      const response = await this.client.get<JobOut[]>("/jobs", {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Search jobs by query
   */
  async searchJobs(
    query: string,
    location?: string,
    limit: number = 20
  ): Promise<JobOut[]> {
    try {
      const response = await this.client.get<JobOut[]>("/jobs/search", {
        params: { q: query, location, limit },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get single job by ID
   */
  async getJob(jobId: string): Promise<JobOut> {
    try {
      const response = await this.client.get<JobOut>(`/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ============ Recommendation Endpoints ============

  /**
   * Get jobs recommended for a resume (protected)
   */
  async getRecommendedJobs(
    resumeId: string,
    minSimilarity: number = 0.5,
    topK: number = 20
  ): Promise<RecommendationResult[]> {
    try {
      const response = await this.client.get<RecommendationResult[]>(
        `/recommendations/jobs-for-resume/${resumeId}`,
        {
          params: {
            min_similarity: minSimilarity,
            top_k: topK,
          },
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get resumes recommended for a job (protected)
   */
  async getRecommendedResumes(
    jobId: string,
    minSimilarity: number = 0.5,
    topK: number = 20
  ): Promise<RecommendationResult[]> {
    try {
      const response = await this.client.get<RecommendationResult[]>(
        `/recommendations/resumes-for-job/${jobId}`,
        {
          params: {
            min_similarity: minSimilarity,
            top_k: topK,
          },
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get resume quality scores (protected)
   */
  async getResumeQuality(resumeId: string): Promise<ResumeQualityScore> {
    try {
      const response = await this.client.get<ResumeQualityScore>(
        `/recommendations/resume-quality/${resumeId}`
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ============ Token Management ============

  /**
   * Set access and refresh tokens
   */
  private setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.saveTokensToStorage();
  }

  /**
   * Clear all tokens
   */
  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem("autointern_access_token");
    localStorage.removeItem("autointern_refresh_token");
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  // ============ Local Storage ============

  /**
   * Save tokens to localStorage
   */
  private saveTokensToStorage(): void {
    if (typeof window !== "undefined" && window.localStorage) {
      if (this.accessToken) {
        localStorage.setItem("autointern_access_token", this.accessToken);
      }
      if (this.refreshToken) {
        localStorage.setItem("autointern_refresh_token", this.refreshToken);
      }
    }
  }

  /**
   * Load tokens from localStorage
   */
  private loadTokensFromStorage(): void {
    if (typeof window !== "undefined" && window.localStorage) {
      const accessToken = localStorage.getItem("autointern_access_token");
      const refreshToken = localStorage.getItem("autointern_refresh_token");

      if (accessToken) {
        this.accessToken = accessToken;
      }
      if (refreshToken) {
        this.refreshToken = refreshToken;
      }
    }
  }

  // ============ Error Handling ============

  /**
   * Handle API errors and return formatted error
   */
  private handleError(error: any): APIError {
    if (error.response?.data) {
      return {
        status: error.response.status,
        detail: error.response.data.detail || error.message,
      };
    }

    return {
      status: error.response?.status || 500,
      detail: error.message || "An error occurred",
    };
  }
}

// Export singleton instance
export const apiClient = new AutoInternClient();

export * from "./types";

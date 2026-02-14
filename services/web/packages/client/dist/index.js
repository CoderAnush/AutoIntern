import axios from "axios";
/**
 * AutoIntern API Client
 * Type-safe TypeScript SDK for the AutoIntern REST API
 */
export class AutoInternClient {
    constructor(baseURL = "http://localhost:8000") {
        this.accessToken = null;
        this.refreshToken = null;
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
        this.client.interceptors.response.use((response) => response, async (error) => {
            const originalRequest = error.config;
            if (error.response?.status === 401 && this.refreshToken && !originalRequest._retry) {
                originalRequest._retry = true;
                try {
                    await this.refreshAccessToken();
                    return this.client(originalRequest);
                }
                catch (refreshError) {
                    this.clearTokens();
                    throw refreshError;
                }
            }
            throw error;
        });
        // Load tokens from localStorage
        this.loadTokensFromStorage();
    }
    // ============ Auth Endpoints ============
    /**
     * Register new user with email and password
     */
    async register(userData) {
        try {
            const response = await this.client.post("/users/register", userData);
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Login user and get access/refresh tokens
     */
    async login(credentials) {
        try {
            const response = await this.client.post("/users/login", credentials);
            const data = response.data;
            // Store tokens
            this.setTokens(data.access_token, data.refresh_token);
            return data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
        if (!this.refreshToken) {
            throw new Error("No refresh token available");
        }
        try {
            const response = await this.client.post("/users/refresh-token", {
                refresh_token: this.refreshToken,
            });
            const data = response.data;
            // Update tokens
            this.setTokens(data.access_token, data.refresh_token);
            return data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Get current user profile (protected)
     */
    async getCurrentUser() {
        try {
            const response = await this.client.get("/users/me");
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Change user password (protected)
     */
    async changePassword(passwordData) {
        try {
            await this.client.post("/users/change-password", passwordData);
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Logout user (clears local tokens)
     */
    async logout() {
        try {
            await this.client.post("/users/logout");
        }
        finally {
            this.clearTokens();
        }
    }
    // ============ Resume Endpoints ============
    /**
     * Upload resume file (protected)
     */
    async uploadResume(file) {
        try {
            const formData = new FormData();
            formData.append("file", file);
            const response = await this.client.post("/resumes/upload", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Get single resume by ID (protected)
     */
    async getResume(resumeId) {
        try {
            const response = await this.client.get(`/resumes/${resumeId}`);
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * List user's resumes (protected)
     */
    async listResumes(limit = 10, offset = 0) {
        try {
            const response = await this.client.get("/resumes", {
                params: { limit, offset },
            });
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Delete resume by ID (protected)
     */
    async deleteResume(resumeId) {
        try {
            await this.client.delete(`/resumes/${resumeId}`);
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    // ============ Job Endpoints ============
    /**
     * List all jobs with pagination
     */
    async listJobs(limit = 20, offset = 0) {
        try {
            const response = await this.client.get("/jobs", {
                params: { limit, offset },
            });
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Search jobs by query
     */
    async searchJobs(query, location, limit = 20) {
        try {
            const response = await this.client.get("/jobs/search", {
                params: { q: query, location, limit },
            });
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Get single job by ID
     */
    async getJob(jobId) {
        try {
            const response = await this.client.get(`/jobs/${jobId}`);
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    // ============ Recommendation Endpoints ============
    /**
     * Get jobs recommended for a resume (protected)
     */
    async getRecommendedJobs(resumeId, minSimilarity = 0.5, topK = 20) {
        try {
            const response = await this.client.get(`/recommendations/jobs-for-resume/${resumeId}`, {
                params: {
                    min_similarity: minSimilarity,
                    top_k: topK,
                },
            });
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Get resumes recommended for a job (protected)
     */
    async getRecommendedResumes(jobId, minSimilarity = 0.5, topK = 20) {
        try {
            const response = await this.client.get(`/recommendations/resumes-for-job/${jobId}`, {
                params: {
                    min_similarity: minSimilarity,
                    top_k: topK,
                },
            });
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    /**
     * Get resume quality scores (protected)
     */
    async getResumeQuality(resumeId) {
        try {
            const response = await this.client.get(`/recommendations/resume-quality/${resumeId}`);
            return response.data;
        }
        catch (error) {
            throw this.handleError(error);
        }
    }
    // ============ Token Management ============
    /**
     * Set access and refresh tokens
     */
    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        this.saveTokensToStorage();
    }
    /**
     * Clear all tokens
     */
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem("autointern_access_token");
        localStorage.removeItem("autointern_refresh_token");
    }
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.accessToken;
    }
    /**
     * Get current access token
     */
    getAccessToken() {
        return this.accessToken;
    }
    // ============ Local Storage ============
    /**
     * Save tokens to localStorage
     */
    saveTokensToStorage() {
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
    loadTokensFromStorage() {
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
    handleError(error) {
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

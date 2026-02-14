import { UserResponse, TokenResponse, UserCreate, UserLogin, PasswordChange, ResumeOut, JobOut, RecommendationResult, ResumeQualityScore } from "./types";
/**
 * AutoIntern API Client
 * Type-safe TypeScript SDK for the AutoIntern REST API
 */
export declare class AutoInternClient {
    private client;
    private accessToken;
    private refreshToken;
    constructor(baseURL?: string);
    /**
     * Register new user with email and password
     */
    register(userData: UserCreate): Promise<UserResponse>;
    /**
     * Login user and get access/refresh tokens
     */
    login(credentials: UserLogin): Promise<TokenResponse>;
    /**
     * Refresh access token using refresh token
     */
    refreshAccessToken(): Promise<TokenResponse>;
    /**
     * Get current user profile (protected)
     */
    getCurrentUser(): Promise<UserResponse>;
    /**
     * Change user password (protected)
     */
    changePassword(passwordData: PasswordChange): Promise<void>;
    /**
     * Logout user (clears local tokens)
     */
    logout(): Promise<void>;
    /**
     * Upload resume file (protected)
     */
    uploadResume(file: File): Promise<ResumeOut>;
    /**
     * Get single resume by ID (protected)
     */
    getResume(resumeId: string): Promise<ResumeOut>;
    /**
     * List user's resumes (protected)
     */
    listResumes(limit?: number, offset?: number): Promise<ResumeOut[]>;
    /**
     * Delete resume by ID (protected)
     */
    deleteResume(resumeId: string): Promise<void>;
    /**
     * List all jobs with pagination
     */
    listJobs(limit?: number, offset?: number): Promise<JobOut[]>;
    /**
     * Search jobs by query
     */
    searchJobs(query: string, location?: string, limit?: number): Promise<JobOut[]>;
    /**
     * Get single job by ID
     */
    getJob(jobId: string): Promise<JobOut>;
    /**
     * Get jobs recommended for a resume (protected)
     */
    getRecommendedJobs(resumeId: string, minSimilarity?: number, topK?: number): Promise<RecommendationResult[]>;
    /**
     * Get resumes recommended for a job (protected)
     */
    getRecommendedResumes(jobId: string, minSimilarity?: number, topK?: number): Promise<RecommendationResult[]>;
    /**
     * Get resume quality scores (protected)
     */
    getResumeQuality(resumeId: string): Promise<ResumeQualityScore>;
    /**
     * Set access and refresh tokens
     */
    private setTokens;
    /**
     * Clear all tokens
     */
    private clearTokens;
    /**
     * Check if user is authenticated
     */
    isAuthenticated(): boolean;
    /**
     * Get current access token
     */
    getAccessToken(): string | null;
    /**
     * Save tokens to localStorage
     */
    private saveTokensToStorage;
    /**
     * Load tokens from localStorage
     */
    private loadTokensFromStorage;
    /**
     * Handle API errors and return formatted error
     */
    private handleError;
}
export declare const apiClient: AutoInternClient;
export * from "./types";

import axios, { type AxiosInstance, type AxiosError } from "axios";
import { useAuthStore } from "@/stores/auth-store";
import { API_BASE_URL } from "./constants";

class APIClient {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: { "Content-Type": "application/json" },
        });

        this.client.interceptors.request.use((config) => {
            const { accessToken } = useAuthStore.getState();
            if (accessToken) {
                config.headers.Authorization = `Bearer ${accessToken}`;
            }
            return config;
        });

        this.client.interceptors.response.use(
            (response) => response,
            async (error: AxiosError) => {
                if (error.response?.status === 401) {
                    useAuthStore.getState().clearAuth();
                    if (typeof window !== "undefined") {
                        window.location.href = "/login";
                    }
                }
                return Promise.reject(error);
            }
        );
    }

    // ── Auth ──────────────────────────────────────────────
    async register(email: string, password: string) {
        const res = await this.client.post("/api/auth/register", { email, password });
        return res.data;
    }

    async login(email: string, password: string) {
        const res = await this.client.post("/api/auth/login", { email, password });
        const { access_token, refresh_token } = res.data;
        useAuthStore.getState().setTokens(access_token, refresh_token);
        // Fetch user profile after login
        try {
            await this.getCurrentUser();
        } catch { }
        return res.data;
    }

    async getCurrentUser() {
        const res = await this.client.get("/api/auth/me");
        useAuthStore.getState().setUser(res.data);
        return res.data;
    }

    async logout() {
        try { await this.client.post("/api/auth/logout"); } finally { useAuthStore.getState().clearAuth(); }
    }

    async changePassword(oldPassword: string, newPassword: string) {
        const res = await this.client.post("/api/auth/change-password", { old_password: oldPassword, new_password: newPassword });
        return res.data;
    }

    // ── Jobs ─────────────────────────────────────────────
    async listJobs(limit = 50, offset = 0) {
        const res = await this.client.get("/api/jobs", { params: { limit, offset } });
        return res.data;
    }

    async searchJobs(query: string, location?: string, jobType?: string, limit = 50) {
        const res = await this.client.get("/api/jobs/search", { params: { q: query, location, job_type: jobType, limit } });
        return res.data;
    }

    async getJob(jobId: string) {
        const res = await this.client.get(`/api/jobs/${jobId}`);
        return res.data;
    }

    async seedJobs() {
        const res = await this.client.post("/api/jobs/seed");
        return res.data;
    }

    // ── Resumes ──────────────────────────────────────────
    async uploadResume(file: File) {
        const fd = new FormData();
        fd.append("file", file);
        const res = await this.client.post("/api/resumes/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
        return res.data;
    }

    async listResumes(limit = 10, offset = 0) {
        const res = await this.client.get("/api/resumes", { params: { limit, offset } });
        return res.data;
    }

    async getResume(resumeId: string) {
        const res = await this.client.get(`/api/resumes/${resumeId}`);
        return res.data;
    }

    async deleteResume(resumeId: string) { await this.client.delete(`/api/resumes/${resumeId}`); }

    // ── Recommendations ──────────────────────────────────
    async getRecommendedJobs(resumeId: string, minSimilarity = 0.3, topK = 20) {
        const res = await this.client.get(`/api/recommendations/jobs-for-resume/${resumeId}`, { params: { min_similarity: minSimilarity, top_k: topK } });
        return res.data;
    }

    async getResumeQuality(resumeId: string) {
        const res = await this.client.get(`/api/recommendations/resume-quality/${resumeId}`);
        return res.data;
    }

    // ── Applications ─────────────────────────────────────
    async listApplications() {
        const res = await this.client.get("/api/applications");
        return res.data;
    }

    async createApplication(data: Record<string, unknown>) {
        const res = await this.client.post("/api/applications", data);
        return res.data;
    }

    async updateApplication(id: string, data: Record<string, unknown>) {
        const res = await this.client.patch(`/api/applications/${id}`, data);
        return res.data;
    }

    async deleteApplication(id: string) { await this.client.delete(`/api/applications/${id}`); }

    // ── Email Preferences ────────────────────────────────
    async getEmailPreferences() {
        const res = await this.client.get("/api/emails/preferences");
        return res.data;
    }

    async updateEmailPreferences(prefs: Record<string, unknown>) {
        const res = await this.client.put("/api/emails/preferences", prefs);
        return res.data;
    }

    async getEmailLogs(limit = 50) {
        const res = await this.client.get("/api/emails/logs", { params: { limit } });
        return res.data;
    }

    async sendTestEmail(email: string) {
        const res = await this.client.post("/api/emails/test", null, { params: { email } });
        return res.data;
    }

    // ── Health ───────────────────────────────────────────
    async healthCheck() {
        const res = await this.client.get("/health");
        return res.data;
    }

    // ── User Preferences ─────────────────────────────────
    async getPreferences() {
        const res = await this.client.get("/api/preferences/");
        return res.data;
    }

    async updatePreferences(data: Record<string, unknown>) {
        const res = await this.client.put("/api/preferences/", data);
        return res.data;
    }

    // ── Scheduler ─────────────────────────────────────────
    async getSchedulerStatus() {
        const res = await this.client.get("/api/scheduler/status");
        return res.data;
    }

    async triggerSchedulerSync() {
        const res = await this.client.post("/api/scheduler/trigger");
        return res.data;
    }

    // ── Saved Jobs ────────────────────────────────────────
    async getSavedJobs() {
        const res = await this.client.get("/api/saved-jobs/");
        return res.data;
    }

    async saveJob(jobId: string) {
        const res = await this.client.post(`/api/saved-jobs/${jobId}`);
        return res.data;
    }

    async unsaveJob(jobId: string) {
        await this.client.delete(`/api/saved-jobs/${jobId}`);
    }

    // ── AI Features ───────────────────────────────────────
    async generateCoverLetter(data: Record<string, unknown>) {
        const res = await this.client.post("/api/ai/cover-letter", data);
        return res.data;
    }

    async generateInterviewPrep(data: Record<string, unknown>) {
        const res = await this.client.post("/api/ai/interview-prep", data);
        return res.data;
    }
}



export const apiClient = new APIClient();

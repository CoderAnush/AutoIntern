/**
 * Type definitions for AutoIntern API responses
 */
export interface UserResponse {
    id: string;
    email: string;
    created_at: string;
}
export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: "bearer";
    expires_in: number;
}
export interface UserCreate {
    email: string;
    password: string;
}
export interface UserLogin {
    email: string;
    password: string;
}
export interface TokenRefresh {
    refresh_token: string;
}
export interface PasswordChange {
    old_password: string;
    new_password: string;
}
export interface ResumeOut {
    id: string;
    user_id: string;
    file_name: string;
    skills: string[];
    storage_url: string;
    created_at: string;
}
export interface JobCreate {
    title: string;
    description: string;
    location: string;
    company?: string;
}
export interface JobOut {
    id: string;
    source: string;
    title: string;
    description: string;
    location: string;
    posted_at: string;
    company_id?: string;
}
export interface RecommendationResult {
    job_id: string;
    job_title: string;
    job_description: string;
    job_location: string;
    resume_id: string;
    similarity_score: number;
    matched_skills: string[];
    skill_gaps: string[];
}
export interface ResumeQualityScore {
    resume_id: string;
    overall_score: number;
    text_length_score: number;
    skill_count_score: number;
    completeness_score: number;
}
export interface APIError {
    status: number;
    detail: string;
}

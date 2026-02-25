export interface User {
    id: string;
    email: string;
    created_at: string;
}

export interface Job {
    id: string;
    source?: string;
    external_id?: string;
    title: string;
    description?: string;
    location?: string;
    posted_at?: string;
    company_name?: string;
    apply_url?: string;
    salary_range?: string;
    job_type?: string;
}

export interface RecommendedJob {
    job_id: string;
    job_title: string;
    job_description?: string;
    job_location?: string;
    resume_id: string;
    similarity_score: number;
    matched_skills: string[];
    skill_gaps: string[];
}

export interface Application {
    id: string;
    user_id: string;
    company_name: string;
    role_title: string;
    status: "applied" | "interview" | "offer" | "rejected";
    applied_at: string;
    updated_at?: string;
    notes?: string;
    job_id?: string;
    resume_id?: string;
    apply_url?: string;
}


export interface ResumeData {
    id: string;
    user_id: string;
    file_name?: string;
    parsed_text?: string;
    skills: string[];
    storage_url?: string;
    created_at: string;
}

export interface ResumeQuality {
    text_length_score: number;
    skill_count_score: number;
    completeness_score: number;
    overall_quality_score: number;
}

export interface ChatMessage {
    id: string;
    text: string;
    sender: "user" | "bot";
    timestamp: Date;
}

export interface EmailPreferences {
    notify_on_new_jobs: boolean;
    notify_on_resume_upload: boolean;
    notify_on_password_change: boolean;
    weekly_digest: boolean;
    email_frequency: "daily" | "weekly" | "never";
}

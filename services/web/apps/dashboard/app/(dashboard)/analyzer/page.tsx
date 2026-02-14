"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Upload, FileText, Loader2, CheckCircle2, XCircle, AlertTriangle,
    TrendingUp, Sparkles, Target, ChevronRight, BadgeCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { ResumeData, ResumeQuality, RecommendedJob } from "@/types";
import toast from "react-hot-toast";

function ScoreGauge({ score = 0, label }: { score: number; label: string }) {
    const parsed = Number.isFinite(score) ? score : Number.parseFloat(String(score));
    const normalized = Number.isFinite(parsed) ? Math.min(Math.max(parsed, 0), 100) : 0;
    const displayScore = Math.round(normalized);
    const r = 60, c = 2 * Math.PI * r, offset = c - (normalized / 100) * c;
    const color = normalized >= 75 ? "#22c55e" : normalized >= 50 ? "#eab308" : "#ef4444";
    return (
        <div className="flex flex-col items-center gap-2">
            <svg width="140" height="140" viewBox="0 0 140 140">
                <circle cx="70" cy="70" r={r} fill="none" stroke="hsl(var(--secondary))" strokeWidth="10" />
                <motion.circle
                    cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="10"
                    strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c}
                    animate={{ strokeDashoffset: offset }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    transform="rotate(-90 70 70)"
                />
                <text x="70" y="68" textAnchor="middle" className="fill-foreground text-2xl font-bold">{displayScore}</text>
                <text x="70" y="88" textAnchor="middle" className="fill-muted-foreground text-xs">/ 100</text>
            </svg>
            <span className="text-sm font-medium text-muted-foreground">{label}</span>
        </div>
    );
}

function buildResumeFeedback(quality: ResumeQuality | null, resume: ResumeData | null): string[] {
    if (!quality) return [];

    const feedback: string[] = [];
    const skillsCount = resume?.skills?.length ?? 0;

    if (quality.text_length_score < 70) {
        feedback.push("Add more detail: include projects, outcomes, and measurable impact.");
    }

    if (skillsCount < 8) {
        feedback.push("List more role-relevant skills and tools that match target job descriptions.");
    }

    if (quality.completeness_score < 100) {
        feedback.push("Add soft-skill keywords like communication, teamwork, leadership, or problem solving.");
    }

    if (skillsCount === 0) {
        feedback.push("Include a clear Skills section so ATS can detect your competencies.");
    }

    if (feedback.length === 0) {
        feedback.push("Great work! To push higher, tailor keywords to a specific role and add quantified results.");
    }

    return feedback;
}

export default function ResumeAnalyzerPage() {
    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [resume, setResume] = useState<ResumeData | null>(null);
    const [quality, setQuality] = useState<ResumeQuality | null>(null);
    const [matchedJobs, setMatchedJobs] = useState<RecommendedJob[]>([]);
    const [loadingMatches, setLoadingMatches] = useState(false);

    // Check existing resumes on load
    useEffect(() => {
        (async () => {
            try {
                const resumes = await apiClient.listResumes(1);
                if (resumes.length > 0) {
                    setResume(resumes[0]);
                    fetchAnalysis(resumes[0].id);
                }
            } catch { }
        })();
    }, []);

    const fetchAnalysis = async (resumeId: string) => {
        // Fetch quality
        try {
            const q = await apiClient.getResumeQuality(resumeId);
            setQuality(q);
        } catch { }
        // Fetch matched jobs
        setLoadingMatches(true);
        try {
            const recs = await apiClient.getRecommendedJobs(resumeId, 0.3, 10);
            setMatchedJobs(recs);
        } catch { }
        setLoadingMatches(false);
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        const f = e.dataTransfer.files?.[0];
        if (f && (f.type === "application/pdf" || f.name.endsWith(".docx") || f.name.endsWith(".txt"))) setFile(f);
        else toast.error("Please upload a PDF, DOCX, or TXT file");
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const f = e.target.files?.[0];
        if (f) setFile(f);
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        try {
            const data = await apiClient.uploadResume(file);
            setResume(data);
            toast.success("Resume uploaded & analyzed!");
            fetchAnalysis(data.id);
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            toast.error(typeof detail === "string" ? detail : "Upload failed");
        }
        setUploading(false);
    };

    const feedback = buildResumeFeedback(quality, resume);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-foreground">Resume Analyzer</h1>
                <p className="text-muted-foreground mt-1">Upload your resume for AI‑powered analysis and job matching</p>
            </div>

            {/* Upload Zone */}
            {!resume && (
                <div
                    onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                    onDragLeave={() => setDragActive(false)}
                    onDrop={handleDrop}
                    className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer
            ${dragActive ? "border-primary bg-primary/5" : "border-border/50 bg-secondary/20 hover:border-primary/40"}`}
                    onClick={() => document.getElementById("resume-input")?.click()}
                >
                    <input id="resume-input" type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={handleFileSelect} />
                    <Upload className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-1">
                        {file ? file.name : "Drag & drop your resume"}
                    </h3>
                    <p className="text-sm text-muted-foreground">Supports PDF, DOCX, TXT</p>
                    {file && (
                        <Button onClick={(e) => { e.stopPropagation(); handleUpload(); }} disabled={uploading} className="mt-4 gap-2">
                            {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing…</> : <><Sparkles className="w-4 h-4" /> Analyze Resume</>}
                        </Button>
                    )}
                </div>
            )}

            {/* Results */}
            {resume && (
                <AnimatePresence>
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                        {/* Resume Info Bar */}
                        <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            <span className="text-foreground font-medium">{resume.file_name || "Resume"}</span>
                            <span className="text-muted-foreground text-sm">• {resume.skills?.length || 0} skills detected</span>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="ml-auto text-muted-foreground"
                                onClick={() => { setResume(null); setQuality(null); setMatchedJobs([]); setFile(null); }}
                            >
                                Upload New
                            </Button>
                        </div>

                        {/* Quality Scores */}
                        {quality && (
                            <div className="border border-border/50 rounded-xl p-6 bg-card/50 backdrop-blur-sm">
                                <h2 className="text-xl font-semibold text-foreground mb-6 flex items-center gap-2">
                                    <Target className="w-5 h-5 text-primary" /> ATS Quality Score
                                </h2>
                                <div className="flex flex-wrap justify-center gap-8">
                                    <ScoreGauge score={quality.overall_quality_score} label="Overall" />
                                    <ScoreGauge score={quality.text_length_score} label="Content Length" />
                                    <ScoreGauge score={quality.skill_count_score} label="Skills" />
                                    <ScoreGauge score={quality.completeness_score} label="Completeness" />
                                </div>
                            </div>
                        )}

                        {/* Improvement Feedback */}
                        {feedback.length > 0 && (
                            <div className="border border-border/50 rounded-xl p-6 bg-card/50 backdrop-blur-sm">
                                <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-primary" /> How to Improve Your Score
                                </h2>
                                <ul className="space-y-2 text-sm text-muted-foreground">
                                    {feedback.map((tip) => (
                                        <li key={tip} className="flex items-start gap-2">
                                            <ChevronRight className="w-4 h-4 text-primary mt-0.5" />
                                            <span>{tip}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Extracted Skills */}
                        {resume.skills && resume.skills.length > 0 && (
                            <div className="border border-border/50 rounded-xl p-6 bg-card/50 backdrop-blur-sm">
                                <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                                    <BadgeCheck className="w-5 h-5 text-emerald-400" /> Detected Skills
                                </h2>
                                <div className="flex flex-wrap gap-2">
                                    {resume.skills.map((s: string) => (
                                        <span key={s} className="px-3 py-1.5 rounded-full bg-emerald-500/15 text-emerald-300 text-sm font-medium border border-emerald-500/20">
                                            {s}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Matched Jobs — Strong / Weak Areas */}
                        <div className="border border-border/50 rounded-xl p-6 bg-card/50 backdrop-blur-sm">
                            <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-primary" /> Job Match Results
                            </h2>
                            {loadingMatches ? (
                                <div className="flex items-center justify-center py-8">
                                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                                    <span className="ml-2 text-muted-foreground">Finding matching jobs…</span>
                                </div>
                            ) : matchedJobs.length === 0 ? (
                                <p className="text-muted-foreground text-center py-6">
                                    No job matches yet. Jobs need embeddings for matching — check back after jobs are indexed.
                                </p>
                            ) : (
                                <div className="space-y-4">
                                    {matchedJobs.map((mj) => (
                                        <div key={mj.job_id} className="border border-border/30 rounded-lg p-4 hover:border-primary/30 transition-colors">
                                            <div className="flex items-start justify-between mb-2">
                                                <div>
                                                    <h4 className="font-medium text-foreground">{mj.job_title}</h4>
                                                    {mj.job_location && <p className="text-xs text-muted-foreground">{mj.job_location}</p>}
                                                </div>
                                                <span className={`text-sm font-bold px-2 py-0.5 rounded ${mj.similarity_score >= 0.7 ? "bg-emerald-500/20 text-emerald-300" :
                                                        mj.similarity_score >= 0.5 ? "bg-amber-500/20 text-amber-300" :
                                                            "bg-red-500/20 text-red-300"
                                                    }`}>
                                                    {Math.round(mj.similarity_score * 100)}% match
                                                </span>
                                            </div>
                                            {/* Strong Skills */}
                                            {mj.matched_skills.length > 0 && (
                                                <div className="mb-2">
                                                    <span className="text-xs text-emerald-400 font-medium flex items-center gap-1 mb-1">
                                                        <CheckCircle2 className="w-3 h-3" /> Strong Skills
                                                    </span>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {mj.matched_skills.map((s) => (
                                                            <span key={s} className="px-2 py-0.5 text-xs rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">{s}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            {/* Skill Gaps */}
                                            {mj.skill_gaps.length > 0 && (
                                                <div>
                                                    <span className="text-xs text-amber-400 font-medium flex items-center gap-1 mb-1">
                                                        <AlertTriangle className="w-3 h-3" /> Skills to Develop
                                                    </span>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {mj.skill_gaps.map((s) => (
                                                            <span key={s} className="px-2 py-0.5 text-xs rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">{s}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </motion.div>
                </AnimatePresence>
            )}
        </div>
    );
}

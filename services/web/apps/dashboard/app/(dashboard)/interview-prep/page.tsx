"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    MessageSquare, Loader2, ChevronDown, ChevronUp, Briefcase,
    FileText, Sparkles, AlertTriangle, RefreshCw, BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import { Job, ResumeData } from "@/types";
import toast from "react-hot-toast";

const TYPE_COLOR: Record<string, string> = {
    Behavioural: "border-blue-500/30 bg-blue-500/5 text-blue-400",
    Technical: "border-violet-500/30 bg-violet-500/5 text-violet-400",
    Situational: "border-amber-500/30 bg-amber-500/5 text-amber-400",
    Motivation: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400",
    Strength: "border-pink-500/30 bg-pink-500/5 text-pink-400",
};

function QuestionCard({ q, idx }: { q: any; idx: number }) {
    const [open, setOpen] = useState(false);
    const colorClass = Object.keys(TYPE_COLOR).find(k => q.type?.includes(k));
    const chip = TYPE_COLOR[colorClass || ""] || "border-border/40 bg-secondary/50 text-muted-foreground";

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.06 }}
            className="border border-border/40 rounded-xl overflow-hidden bg-card/50"
        >
            <button
                onClick={() => setOpen(v => !v)}
                className="w-full flex items-start gap-3 p-4 text-left hover:bg-secondary/30 transition-colors"
            >
                <span className="text-primary font-bold text-sm shrink-0 w-5 mt-0.5">{idx + 1}.</span>
                <div className="flex-1 min-w-0">
                    <span className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full border mb-1.5 ${chip}`}>
                        {q.type || "General"}
                    </span>
                    <p className="text-sm font-medium text-foreground leading-snug">{q.question}</p>
                </div>
                {open ? <ChevronUp className="w-4 h-4 text-muted-foreground shrink-0 mt-1" /> : <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0 mt-1" />}
            </button>
            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="px-4 pb-4 pt-0 border-t border-border/30">
                            <div className="flex items-center gap-1.5 mt-3 mb-2">
                                <BookOpen className="w-3.5 h-3.5 text-primary" />
                                <p className="text-xs font-semibold text-primary uppercase tracking-wide">Model Answer</p>
                            </div>
                            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">{q.answer}</p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

export default function InterviewPrepPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [resumes, setResumes] = useState<ResumeData[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [selectedResume, setSelectedResume] = useState("");
    const [manualTitle, setManualTitle] = useState("");
    const [manualDesc, setManualDesc] = useState("");
    const [mode, setMode] = useState<"job" | "manual">("job");

    const [generating, setGenerating] = useState(false);
    const [questions, setQuestions] = useState<any[]>([]);
    const [prepJobTitle, setPrepJobTitle] = useState("");
    const [noKeyError, setNoKeyError] = useState(false);

    useEffect(() => {
        Promise.allSettled([
            apiClient.listJobs(200, 0),
            apiClient.listResumes(1, 0),
        ]).then(([j, r]) => {
            if (j.status === "fulfilled" && Array.isArray(j.value)) setJobs(j.value);
            if (r.status === "fulfilled" && Array.isArray(r.value)) setResumes(r.value);
        });
    }, []);

    const handleGenerate = async () => {
        setNoKeyError(false);
        setGenerating(true);
        setQuestions([]);
        try {
            const payload: Record<string, unknown> = { resume_id: selectedResume || null };
            if (mode === "job" && selectedJob) {
                payload.job_id = selectedJob;
            } else {
                if (!manualTitle) { toast.error("Enter a job title"); setGenerating(false); return; }
                payload.job_title = manualTitle;
                payload.job_description = manualDesc;
            }
            const res = await apiClient.generateInterviewPrep(payload);
            setQuestions(res.questions || []);
            setPrepJobTitle(res.job_title || manualTitle);
            if ((res.questions || []).length === 0) toast.error("No questions generated — try again");
        } catch (e: any) {
            const detail = e?.response?.data?.detail || "";
            if (detail.includes("GEMINI_API_KEY") || detail.includes("not set")) {
                setNoKeyError(true);
            } else {
                toast.error(detail || "Generation failed. Please try again.");
            }
        }
        setGenerating(false);
    };

    return (
        <div className="space-y-6 max-w-3xl">
            <div>
                <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
                    <MessageSquare className="w-7 h-7 text-primary" /> Interview Prep
                </h1>
                <p className="text-muted-foreground mt-1">
                    AI-generated questions and model answers tailored to any job
                </p>
            </div>

            {/* API key error */}
            <AnimatePresence>
                {noKeyError && (
                    <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                        className="flex items-start gap-3 p-4 rounded-xl border border-amber-500/40 bg-amber-500/10">
                        <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
                        <div>
                            <p className="text-sm font-semibold text-amber-300">Gemini API Key not configured</p>
                            <p className="text-xs text-amber-400/80 mt-0.5">
                                Add <code className="bg-black/30 px-1 rounded">GEMINI_API_KEY=your_key_here</code> to{" "}
                                <code className="bg-black/30 px-1 rounded">services/api/.env</code>.<br />
                                Get a free key at{" "}
                                <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline text-amber-300">aistudio.google.com</a>
                            </p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Input panel */}
            <div className="border border-border/50 rounded-xl p-5 bg-card/50 space-y-4">
                <div className="flex gap-2">
                    {(["job", "manual"] as const).map((m) => (
                        <button key={m} onClick={() => setMode(m)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${mode === m ? "bg-primary text-primary-foreground" : "bg-secondary/50 text-muted-foreground hover:bg-secondary"}`}>
                            {m === "job" ? "Pick from Jobs" : "Enter Manually"}
                        </button>
                    ))}
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                    {mode === "job" ? (
                        <div className="space-y-1.5">
                            <Label className="text-xs">Job</Label>
                            <div className="relative">
                                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                                <select value={selectedJob} onChange={(e) => setSelectedJob(e.target.value)}
                                    className="w-full h-10 pl-9 pr-8 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60 appearance-none">
                                    <option value="">Select a job…</option>
                                    {jobs.map(j => <option key={j.id} value={j.id}>{j.title} — {j.company_name}</option>)}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-1.5">
                            <Label className="text-xs">Job Title *</Label>
                            <input value={manualTitle} onChange={(e) => setManualTitle(e.target.value)}
                                placeholder="e.g. ML Engineer"
                                className="w-full h-10 px-3 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60" />
                        </div>
                    )}

                    <div className="space-y-1.5">
                        <Label className="text-xs">Resume <span className="text-muted-foreground">(optional)</span></Label>
                        <div className="relative">
                            <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                            <select value={selectedResume} onChange={(e) => setSelectedResume(e.target.value)}
                                className="w-full h-10 pl-9 pr-8 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60 appearance-none">
                                <option value="">None</option>
                                {resumes.map((r: any) => <option key={r.id} value={r.id}>{r.file_name || r.id.slice(0, 8)}</option>)}
                            </select>
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                        </div>
                    </div>
                </div>

                {mode === "manual" && (
                    <div className="space-y-1.5">
                        <Label className="text-xs">Job Description <span className="text-muted-foreground">(optional)</span></Label>
                        <textarea value={manualDesc} onChange={(e) => setManualDesc(e.target.value)} rows={3}
                            placeholder="Paste the job description…"
                            className="w-full px-3 py-2 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60 resize-none" />
                    </div>
                )}

                <Button
                    onClick={handleGenerate}
                    disabled={generating || (mode === "job" && !selectedJob) || (mode === "manual" && !manualTitle)}
                    className="gap-2"
                >
                    {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    {generating ? "Generating…" : "Generate Questions"}
                </Button>
            </div>

            {/* Questions list */}
            {generating ? (
                <div className="flex flex-col items-center gap-3 py-12 text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <p className="text-muted-foreground text-sm">Gemini is preparing your interview guide…</p>
                </div>
            ) : questions.length > 0 ? (
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <h2 className="text-base font-semibold text-foreground">
                            {questions.length} questions for <span className="text-primary">{prepJobTitle}</span>
                        </h2>
                        <button onClick={handleGenerate}
                            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
                            <RefreshCw className="w-3.5 h-3.5" /> Regenerate
                        </button>
                    </div>
                    {questions.map((q, i) => <QuestionCard key={i} q={q} idx={i} />)}
                </div>
            ) : null}
        </div>
    );
}

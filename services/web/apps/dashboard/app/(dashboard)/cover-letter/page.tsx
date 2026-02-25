"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles, Loader2, Copy, Download, Check, FileText,
    Briefcase, ChevronDown, AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import { Job, ResumeData } from "@/types";
import toast from "react-hot-toast";

// ── Helpers ────────────────────────────────────────────────────

function Select({ value, onChange, options, placeholder, icon: Icon }: {
    value: string; onChange: (v: string) => void;
    options: { value: string; label: string }[];
    placeholder: string; icon: any;
}) {
    return (
        <div className="relative">
            <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full h-10 pl-9 pr-8 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60 appearance-none"
            >
                <option value="">{placeholder}</option>
                {options.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
        </div>
    );
}

// ── Main Page ─────────────────────────────────────────────────

export default function CoverLetterPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [resumes, setResumes] = useState<ResumeData[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [selectedResume, setSelectedResume] = useState("");
    const [manualTitle, setManualTitle] = useState("");
    const [manualCompany, setManualCompany] = useState("");
    const [manualDesc, setManualDesc] = useState("");
    const [mode, setMode] = useState<"job" | "manual">("job");

    const [generating, setGenerating] = useState(false);
    const [letter, setLetter] = useState("");
    const [jobMeta, setJobMeta] = useState({ title: "", company: "" });
    const [copied, setCopied] = useState(false);
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
        setLetter("");
        try {
            const payload: Record<string, unknown> = { resume_id: selectedResume || null };
            if (mode === "job" && selectedJob) {
                payload.job_id = selectedJob;
            } else {
                if (!manualTitle) { toast.error("Enter a job title"); setGenerating(false); return; }
                payload.job_title = manualTitle;
                payload.company_name = manualCompany;
                payload.job_description = manualDesc;
            }
            const res = await apiClient.generateCoverLetter(payload);
            setLetter(res.cover_letter);
            setJobMeta({ title: res.job_title, company: res.company_name });
            toast.success("Cover letter generated!");
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

    const handleCopy = async () => {
        await navigator.clipboard.writeText(letter);
        setCopied(true);
        toast.success("Copied to clipboard!");
        setTimeout(() => setCopied(false), 2000);
    };

    const handleDownload = () => {
        const blob = new Blob([letter], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `cover-letter-${jobMeta.company || "job"}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const jobOptions = jobs.map((j) => ({
        value: j.id,
        label: `${j.title} — ${j.company_name}`,
    }));

    const resumeOptions = resumes.map((r: any) => ({
        value: r.id,
        label: r.file_name || `Resume ${r.id.slice(0, 8)}`,
    }));

    return (
        <div className="space-y-6 max-w-4xl">
            <div>
                <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
                    <Sparkles className="w-7 h-7 text-primary" /> AI Cover Letter
                </h1>
                <p className="text-muted-foreground mt-1">
                    Select a job and your resume — Gemini writes a tailored cover letter in seconds
                </p>
            </div>

            {/* API Key Error banner */}
            <AnimatePresence>
                {noKeyError && (
                    <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                        className="flex items-start gap-3 p-4 rounded-xl border border-amber-500/40 bg-amber-500/10">
                        <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
                        <div>
                            <p className="text-sm font-semibold text-amber-300">Gemini API Key not configured</p>
                            <p className="text-xs text-amber-400/80 mt-0.5">
                                Add your key to <code className="bg-black/30 px-1 rounded">services/api/.env</code>:
                                <code className="block bg-black/40 px-2 py-1 rounded mt-1 font-mono">GEMINI_API_KEY=your_key_here</code>
                                Get a free key at{" "}
                                <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline text-amber-300">
                                    aistudio.google.com
                                </a>
                            </p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="grid md:grid-cols-2 gap-6">
                {/* Left: Inputs */}
                <div className="border border-border/50 rounded-xl p-5 bg-card/50 space-y-5">
                    {/* Mode toggle */}
                    <div className="flex gap-2">
                        {(["job", "manual"] as const).map((m) => (
                            <button key={m} onClick={() => setMode(m)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${mode === m ? "bg-primary text-primary-foreground" : "bg-secondary/50 text-muted-foreground hover:bg-secondary"}`}>
                                {m === "job" ? "Pick from Jobs" : "Enter Manually"}
                            </button>
                        ))}
                    </div>

                    {mode === "job" ? (
                        <div className="space-y-2">
                            <Label>Job</Label>
                            <Select value={selectedJob} onChange={setSelectedJob}
                                options={jobOptions} placeholder="Select a job…" icon={Briefcase} />
                            {jobs.length === 0 && (
                                <p className="text-xs text-muted-foreground">No jobs loaded — browse jobs first</p>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <div className="space-y-1.5">
                                <Label className="text-xs">Job Title *</Label>
                                <input value={manualTitle} onChange={(e) => setManualTitle(e.target.value)}
                                    placeholder="e.g. Software Engineer Intern"
                                    className="w-full h-9 px-3 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60" />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs">Company</Label>
                                <input value={manualCompany} onChange={(e) => setManualCompany(e.target.value)}
                                    placeholder="e.g. Google"
                                    className="w-full h-9 px-3 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60" />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs">Job Description</Label>
                                <textarea value={manualDesc} onChange={(e) => setManualDesc(e.target.value)}
                                    rows={4} placeholder="Paste the job description here…"
                                    className="w-full px-3 py-2 rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground focus:outline-none focus:border-primary/60 resize-none" />
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label>Resume <span className="text-muted-foreground text-xs">(optional but recommended)</span></Label>
                        <Select value={selectedResume} onChange={setSelectedResume}
                            options={resumeOptions} placeholder="Select a resume…" icon={FileText} />
                    </div>

                    <Button
                        onClick={handleGenerate}
                        disabled={generating || (mode === "job" && !selectedJob) || (mode === "manual" && !manualTitle)}
                        className="w-full gap-2"
                    >
                        {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        {generating ? "Generating…" : "Generate Cover Letter"}
                    </Button>
                </div>

                {/* Right: Output */}
                <div className="border border-border/50 rounded-xl p-5 bg-card/50 flex flex-col gap-4 min-h-[380px]">
                    {generating ? (
                        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                            <p className="text-muted-foreground text-sm">Gemini is writing your cover letter…</p>
                        </div>
                    ) : letter ? (
                        <>
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-semibold text-foreground">{jobMeta.title}</p>
                                    {jobMeta.company && <p className="text-xs text-muted-foreground">{jobMeta.company}</p>}
                                </div>
                                <div className="flex gap-2">
                                    <Button size="sm" variant="outline" onClick={handleCopy} className="gap-1.5">
                                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                                        {copied ? "Copied!" : "Copy"}
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={handleDownload} className="gap-1.5">
                                        <Download className="w-3.5 h-3.5" /> Download
                                    </Button>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto">
                                <pre className="whitespace-pre-wrap text-sm text-foreground/90 leading-relaxed font-sans">
                                    {letter}
                                </pre>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
                            <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
                                <Sparkles className="w-7 h-7 text-primary" />
                            </div>
                            <p className="text-muted-foreground text-sm max-w-[220px]">
                                Your personalised cover letter will appear here
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

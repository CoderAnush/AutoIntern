"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Search, MapPin, Briefcase, ExternalLink, Building2, DollarSign,
    Clock, Loader2, Sparkles, X, ChevronRight, BadgeCheck, AlertCircle,
    Bookmark, BookmarkCheck, Globe, Users, TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api";
import { Job } from "@/types";
import toast from "react-hot-toast";

const JOB_TYPE_COLORS: Record<string, string> = {
    Internship: "bg-violet-500/20 text-violet-300 border-violet-500/30",
    "Full-time": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    "Part-time": "bg-amber-500/20 text-amber-300 border-amber-500/30",
    Contract: "bg-blue-500/20 text-blue-300 border-blue-500/30",
};

const FILTER_TYPES = ["All", "Internship", "Full-time", "Part-time", "Contract"];

function timeAgo(dateStr?: string) {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days < 7) return `${days}d ago`;
    if (days < 30) return `${Math.floor(days / 7)}w ago`;
    return `${Math.floor(days / 30)}mo ago`;
}

function CompanyPanel({ job, onClose }: { job: Job; onClose: () => void }) {
    useEffect(() => {
        const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [onClose]);

    const company = job.company_name || "Company";
    const glassdoorUrl = `https://www.glassdoor.com/Search/results.htm?keyword=${encodeURIComponent(company)}`;
    const linkedinUrl = `https://www.linkedin.com/company/${encodeURIComponent(company.toLowerCase().replace(/\s+/g, "-"))}`;

    return (
        <AnimatePresence>
            <motion.div
                className="fixed inset-0 z-50 flex items-end justify-center sm:items-center p-4"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            >
                <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
                <motion.div
                    className="relative z-10 w-full max-w-md rounded-2xl bg-card border border-border/60 shadow-2xl overflow-hidden"
                    initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }}
                    transition={{ duration: 0.25, ease: "easeOut" }}
                >
                    {/* Gradient header */}
                    <div className="relative bg-gradient-to-br from-primary/30 to-violet-600/20 p-6 pb-8">
                        <button onClick={onClose} className="absolute top-4 right-4 p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/10 transition-colors">
                            <X className="w-4 h-4" />
                        </button>
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/40 to-violet-500/40 flex items-center justify-center border border-primary/20 shadow-lg">
                                <Building2 className="w-8 h-8 text-primary" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-foreground">{company}</h2>
                                <p className="text-sm text-muted-foreground mt-0.5">Hiring now</p>
                            </div>
                        </div>
                    </div>

                    {/* Details */}
                    <div className="px-6 py-5 space-y-3 -mt-2">
                        {job.location && (
                            <div className="flex items-center gap-3 text-sm">
                                <MapPin className="w-4 h-4 text-muted-foreground shrink-0" />
                                <span className="text-foreground">{job.location}</span>
                            </div>
                        )}
                        {job.job_type && (
                            <div className="flex items-center gap-3 text-sm">
                                <Briefcase className="w-4 h-4 text-muted-foreground shrink-0" />
                                <span className="text-foreground">{job.job_type}</span>
                            </div>
                        )}
                        {job.salary_range && (
                            <div className="flex items-center gap-3 text-sm">
                                <DollarSign className="w-4 h-4 text-muted-foreground shrink-0" />
                                <span className="text-foreground">{job.salary_range}</span>
                            </div>
                        )}
                        {job.posted_at && (
                            <div className="flex items-center gap-3 text-sm">
                                <Clock className="w-4 h-4 text-muted-foreground shrink-0" />
                                <span className="text-muted-foreground">Posted {timeAgo(job.posted_at)}</span>
                            </div>
                        )}
                    </div>

                    {/* Quick links */}
                    <div className="px-6 pb-6 flex gap-3">
                        <a href={glassdoorUrl} target="_blank" rel="noopener noreferrer"
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-border/50 bg-secondary/50 hover:bg-secondary text-sm text-muted-foreground hover:text-foreground transition-colors">
                            <TrendingUp className="w-3.5 h-3.5" /> Glassdoor
                        </a>
                        <a href={linkedinUrl} target="_blank" rel="noopener noreferrer"
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-border/50 bg-secondary/50 hover:bg-secondary text-sm text-muted-foreground hover:text-foreground transition-colors">
                            <Users className="w-3.5 h-3.5" /> LinkedIn
                        </a>
                        <a href={job.apply_url || "#"} target="_blank" rel="noopener noreferrer"
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-sm text-primary-foreground font-medium transition-colors">
                            Apply <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}


function JobModal({ job, onClose }: { job: Job; onClose: () => void }) {
    // Close on Escape key
    useEffect(() => {
        const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [onClose]);

    return (
        <AnimatePresence>
            <motion.div
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            >
                {/* Backdrop */}
                <div
                    className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                    onClick={onClose}
                />
                {/* Modal */}
                <motion.div
                    className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-card border border-border/60 shadow-2xl shadow-black/50"
                    initial={{ scale: 0.95, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.95, opacity: 0, y: 20 }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                >
                    {/* Header */}
                    <div className="sticky top-0 z-10 flex items-start justify-between p-6 pb-4 bg-card border-b border-border/40">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                            <div className="w-12 h-12 shrink-0 rounded-xl bg-gradient-to-br from-primary/30 to-violet-500/30 flex items-center justify-center">
                                <Building2 className="w-6 h-6 text-primary" />
                            </div>
                            <div className="min-w-0">
                                <h2 className="text-lg font-bold text-foreground leading-tight pr-2">{job.title}</h2>
                                <p className="text-primary font-semibold text-sm">{job.company_name || "Company"}</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="ml-3 shrink-0 p-2 rounded-lg hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Meta chips */}
                    <div className="flex flex-wrap gap-2 px-6 py-4 border-b border-border/30">
                        {job.job_type && (
                            <span className={`text-xs px-3 py-1.5 rounded-full border font-medium ${JOB_TYPE_COLORS[job.job_type] || "bg-secondary text-muted-foreground"}`}>
                                {job.job_type}
                            </span>
                        )}
                        {job.location && (
                            <span className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-secondary/60 text-muted-foreground border border-border/30">
                                <MapPin className="w-3 h-3" /> {job.location}
                            </span>
                        )}
                        {job.salary_range && (
                            <span className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-secondary/60 text-muted-foreground border border-border/30">
                                <DollarSign className="w-3 h-3" /> {job.salary_range}
                            </span>
                        )}
                        {job.posted_at && (
                            <span className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-secondary/60 text-muted-foreground border border-border/30">
                                <Clock className="w-3 h-3" /> {timeAgo(job.posted_at)}
                            </span>
                        )}
                    </div>

                    {/* Full Description */}
                    <div className="px-6 py-5">
                        <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                            <BadgeCheck className="w-4 h-4 text-primary" /> Job Description
                        </h3>
                        <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                            {job.description || "No description available."}
                        </div>
                    </div>

                    {/* Apply CTA */}
                    <div className="sticky bottom-0 px-6 py-4 bg-card border-t border-border/40">
                        {job.apply_url ? (
                            <a
                                href={job.apply_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={() => toast.success("Opening application page…")}
                            >
                                <Button className="w-full gap-2 h-11 text-base font-semibold shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all">
                                    Apply Now <ExternalLink className="w-4 h-4" />
                                </Button>
                            </a>
                        ) : (
                            <Button disabled variant="secondary" className="w-full gap-2 h-11">
                                <AlertCircle className="w-4 h-4" /> No Application Link Available
                            </Button>
                        )}
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}

export default function JobsPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [companyJob, setCompanyJob] = useState<Job | null>(null);
    const [loading, setLoading] = useState(true);
    const [seeding, setSeeding] = useState(false);
    const [query, setQuery] = useState("");
    const [activeFilter, setActiveFilter] = useState("All");
    const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
    const [savingId, setSavingId] = useState<string | null>(null);

    const fetchJobs = useCallback(async () => {
        setLoading(true);
        try {
            let data: Job[];
            if (query) {
                data = await apiClient.searchJobs(query, undefined, activeFilter === "All" ? undefined : activeFilter);
            } else {
                data = await apiClient.listJobs(200);
            }
            setJobs(data);
        } catch {
            toast.error("Failed to load jobs");
        }
        setLoading(false);
    }, [query, activeFilter]);

    // Load saved job IDs on mount
    useEffect(() => {
        apiClient.getSavedJobs().then((saved: any[]) => {
            setSavedIds(new Set(saved.map((s: any) => s.job_id)));
        }).catch(() => { });
    }, []);

    useEffect(() => { fetchJobs(); }, [fetchJobs]);

    const handleToggleSave = async (e: React.MouseEvent, job: Job) => {
        e.stopPropagation();
        setSavingId(job.id);
        const isSaved = savedIds.has(job.id);
        try {
            if (isSaved) {
                await apiClient.unsaveJob(job.id);
                setSavedIds(prev => { const s = new Set(prev); s.delete(job.id); return s; });
                toast.success("Removed from saved jobs");
            } else {
                await apiClient.saveJob(job.id);
                setSavedIds(prev => new Set(prev).add(job.id));
                toast.success("Job saved! ❤️");
            }
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to save job");
        }
        setSavingId(null);
    };

    const handleSeedJobs = async () => {
        setSeeding(true);
        try {
            const res = await apiClient.seedJobs();
            toast.success(`${res.count} jobs seeded!`);
            fetchJobs();
        } catch {
            toast.error("Failed to seed jobs");
        }
        setSeeding(false);
    };

    const filteredJobs = activeFilter === "All" ? jobs : jobs.filter((j) => j.job_type === activeFilter);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Jobs</h1>
                    <p className="text-muted-foreground mt-1">Discover opportunities at top companies — click any card to see full details</p>
                </div>
                {jobs.length === 0 && !loading && (
                    <Button onClick={handleSeedJobs} disabled={seeding} variant="outline" className="gap-2">
                        {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        Load Sample Jobs
                    </Button>
                )}
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search by title, company, or keyword…"
                    className="pl-10 h-12 bg-secondary/50 text-base"
                />
            </div>

            {/* Filters */}
            <div className="flex gap-2 flex-wrap">
                {FILTER_TYPES.map((f) => (
                    <button
                        key={f}
                        onClick={() => setActiveFilter(f)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all
              ${activeFilter === f
                                ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                                : "bg-secondary/50 text-muted-foreground hover:bg-secondary hover:text-foreground"
                            }`}
                    >
                        {f}
                    </button>
                ))}
            </div>

            {/* Job Count */}
            <p className="text-sm text-muted-foreground">{filteredJobs.length} jobs found — click a card to view full description & apply</p>

            {/* Jobs Grid */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            ) : filteredJobs.length === 0 ? (
                <div className="text-center py-20">
                    <Briefcase className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
                    <h3 className="text-lg font-medium text-foreground">No jobs found</h3>
                    <p className="text-muted-foreground">Try different search terms or load sample jobs.</p>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <AnimatePresence mode="popLayout">
                        {filteredJobs.map((job, i) => (
                            <motion.div
                                key={job.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{ delay: i * 0.02, duration: 0.3 }}
                                onClick={() => setSelectedJob(job)}
                                className="group relative border border-border/50 rounded-xl bg-card/50 backdrop-blur-sm p-5 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 cursor-pointer"
                            >
                                {/* Company + Type */}
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setCompanyJob(job); }}
                                            className="flex items-center gap-2 rounded-lg hover:bg-secondary/80 px-1 py-0.5 transition-colors text-left"
                                            title="View company info"
                                        >
                                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-violet-500/20 flex items-center justify-center">
                                                <Building2 className="w-5 h-5 text-primary" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-foreground hover:text-primary transition-colors">{job.company_name || "Company"}</p>
                                                {job.posted_at && (
                                                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                                                        <Clock className="w-3 h-3" />
                                                        {timeAgo(job.posted_at)}
                                                    </p>
                                                )}
                                            </div>
                                        </button>
                                    </div>
                                    {job.job_type && (
                                        <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${JOB_TYPE_COLORS[job.job_type] || "bg-secondary text-muted-foreground"}`}>
                                            {job.job_type}
                                        </span>
                                    )}
                                </div>

                                {/* Title */}
                                <h3 className="text-base font-semibold text-foreground mb-2 group-hover:text-primary transition-colors line-clamp-2">
                                    {job.title}
                                </h3>

                                {/* Description snippet */}
                                {job.description && (
                                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{job.description.slice(0, 130)}…</p>
                                )}

                                {/* Meta */}
                                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground mb-4">
                                    {job.location && (
                                        <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {job.location}</span>
                                    )}
                                    {job.salary_range && (
                                        <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" /> {job.salary_range}</span>
                                    )}
                                </div>

                                {/* CTA row */}
                                <div className="flex gap-2 items-center">
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        className="flex-1 gap-1.5 text-xs group-hover:bg-primary/10 group-hover:text-primary transition-all"
                                        onClick={(e) => { e.stopPropagation(); setSelectedJob(job); }}
                                    >
                                        <ChevronRight className="w-3.5 h-3.5" /> View Details
                                    </Button>
                                    {job.apply_url && (
                                        <a
                                            href={job.apply_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            <Button variant="default" size="sm" className="gap-1.5 text-xs">
                                                Apply <ExternalLink className="w-3 h-3" />
                                            </Button>
                                        </a>
                                    )}
                                    <button
                                        onClick={(e) => handleToggleSave(e, job)}
                                        disabled={savingId === job.id}
                                        className={`p-2 rounded-lg transition-all border ${savedIds.has(job.id)
                                            ? "bg-amber-500/20 border-amber-500/40 text-amber-400"
                                            : "bg-secondary/50 border-border/40 text-muted-foreground hover:text-amber-400 hover:border-amber-500/40"
                                            }`}
                                        title={savedIds.has(job.id) ? "Unsave" : "Save job"}
                                    >
                                        {savingId === job.id
                                            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                            : savedIds.has(job.id)
                                                ? <BookmarkCheck className="w-3.5 h-3.5" />
                                                : <Bookmark className="w-3.5 h-3.5" />
                                        }
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Full Description Modal */}
            {selectedJob && (
                <JobModal job={selectedJob} onClose={() => setSelectedJob(null)} />
            )}

            {/* Company Info Panel */}
            {companyJob && (
                <CompanyPanel job={companyJob} onClose={() => setCompanyJob(null)} />
            )}
        </div>
    );
}

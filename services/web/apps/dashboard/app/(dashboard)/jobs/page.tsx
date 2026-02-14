"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Search, MapPin, Briefcase, ExternalLink, Building2, DollarSign,
    Clock, Filter, Loader2, Sparkles, BadgeCheck, AlertTriangle
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

export default function JobsPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [seeding, setSeeding] = useState(false);
    const [query, setQuery] = useState("");
    const [activeFilter, setActiveFilter] = useState("All");

    const fetchJobs = useCallback(async () => {
        setLoading(true);
        try {
            let data: Job[];
            if (query) {
                data = await apiClient.searchJobs(query, undefined, activeFilter === "All" ? undefined : activeFilter);
            } else {
                data = await apiClient.listJobs(50);
            }
            setJobs(data);
        } catch {
            toast.error("Failed to load jobs");
        }
        setLoading(false);
    }, [query, activeFilter]);

    useEffect(() => { fetchJobs(); }, [fetchJobs]);

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
                    <p className="text-muted-foreground mt-1">Discover opportunities at top companies</p>
                </div>
                {jobs.length === 0 && !loading && (
                    <Button onClick={handleSeedJobs} disabled={seeding} variant="outline" className="gap-2">
                        {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        Load Sample Jobs
                    </Button>
                )}
            </div>

            {/* Search Bar */}
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
            <p className="text-sm text-muted-foreground">{filteredJobs.length} jobs found</p>

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
                                transition={{ delay: i * 0.03, duration: 0.3 }}
                                className="group relative border border-border/50 rounded-xl bg-card/50 backdrop-blur-sm p-5 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
                            >
                                {/* Company + Type badge */}
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-violet-500/20 flex items-center justify-center">
                                            <Building2 className="w-5 h-5 text-primary" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-foreground">{job.company_name || "Company"}</p>
                                            {job.posted_at && (
                                                <p className="text-xs text-muted-foreground flex items-center gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    {timeAgo(job.posted_at)}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    {job.job_type && (
                                        <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${JOB_TYPE_COLORS[job.job_type] || "bg-secondary text-muted-foreground"}`}>
                                            {job.job_type}
                                        </span>
                                    )}
                                </div>

                                {/* Title */}
                                <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors line-clamp-2">
                                    {job.title}
                                </h3>

                                {/* Description snippet */}
                                {job.description && (
                                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{job.description.slice(0, 150)}…</p>
                                )}

                                {/* Meta Row */}
                                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground mb-4">
                                    {job.location && (
                                        <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {job.location}</span>
                                    )}
                                    {job.salary_range && (
                                        <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" /> {job.salary_range}</span>
                                    )}
                                </div>

                                {/* Apply Button — links to real company career page */}
                                <div className="flex gap-2">
                                    {job.apply_url ? (
                                        <a
                                            href={job.apply_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex-1"
                                        >
                                            <Button variant="default" className="w-full gap-2 group-hover:shadow-lg group-hover:shadow-primary/20 transition-all">
                                                Apply <ExternalLink className="w-3.5 h-3.5" />
                                            </Button>
                                        </a>
                                    ) : (
                                        <Button variant="secondary" disabled className="flex-1 gap-2">
                                            No Link Available
                                        </Button>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
}

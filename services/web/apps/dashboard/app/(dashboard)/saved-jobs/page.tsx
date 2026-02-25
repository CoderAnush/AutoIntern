"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    Bookmark, Loader2, MapPin, Briefcase, ExternalLink,
    Building2, DollarSign, BookmarkX, Sparkles,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import toast from "react-hot-toast";

interface SavedJobItem {
    id: string;
    job_id: string;
    job_title?: string;
    company_name?: string;
    location?: string;
    job_type?: string;
    apply_url?: string;
    salary_range?: string;
    saved_at: string;
}

const JOB_TYPE_COLORS: Record<string, string> = {
    Internship: "bg-violet-500/20 text-violet-300 border-violet-500/30",
    "Full-time": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    "Part-time": "bg-amber-500/20 text-amber-300 border-amber-500/30",
    Contract: "bg-blue-500/20 text-blue-300 border-blue-500/30",
};

export default function SavedJobsPage() {
    const [saved, setSaved] = useState<SavedJobItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [removingId, setRemovingId] = useState<string | null>(null);

    useEffect(() => {
        apiClient.getSavedJobs()
            .then(setSaved)
            .catch(() => toast.error("Failed to load saved jobs"))
            .finally(() => setLoading(false));
    }, []);

    const handleRemove = async (item: SavedJobItem) => {
        setRemovingId(item.job_id);
        try {
            await apiClient.unsaveJob(item.job_id);
            setSaved(prev => prev.filter(s => s.job_id !== item.job_id));
            toast.success("Removed from saved jobs");
        } catch {
            toast.error("Failed to remove");
        }
        setRemovingId(null);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
                    <Bookmark className="w-7 h-7 text-amber-400" /> Saved Jobs
                </h1>
                <p className="text-muted-foreground mt-1">
                    {saved.length > 0 ? `${saved.length} job${saved.length > 1 ? "s" : ""} saved` : "Bookmark jobs from the Find Jobs page to see them here"}
                </p>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-24">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            ) : saved.length === 0 ? (
                <div className="text-center py-24 border border-dashed border-border/40 rounded-xl">
                    <Bookmark className="w-12 h-12 mx-auto text-muted-foreground/30 mb-4" />
                    <p className="text-muted-foreground font-medium">No saved jobs yet</p>
                    <p className="text-sm text-muted-foreground/60 mt-1">
                        Click the <span className="text-amber-400">bookmark icon</span> on any job card to save it here
                    </p>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {saved.map((item, i) => (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ delay: i * 0.04 }}
                            className="group relative border border-amber-500/20 rounded-xl bg-card/50 backdrop-blur-sm p-5 hover:border-amber-500/40 hover:shadow-lg hover:shadow-amber-500/5 transition-all duration-300"
                        >
                            {/* Remove button */}
                            <button
                                onClick={() => handleRemove(item)}
                                disabled={removingId === item.job_id}
                                className="absolute top-3 right-3 p-1.5 rounded-lg bg-secondary/50 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-all opacity-0 group-hover:opacity-100"
                                title="Remove"
                            >
                                {removingId === item.job_id
                                    ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                    : <BookmarkX className="w-3.5 h-3.5" />
                                }
                            </button>

                            {/* Company row */}
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                                    <Building2 className="w-4 h-4 text-amber-400" />
                                </div>
                                <p className="text-sm font-medium text-foreground">{item.company_name || "Company"}</p>
                                {item.job_type && (
                                    <span className={`ml-auto text-xs px-2 py-0.5 rounded-full border font-medium ${JOB_TYPE_COLORS[item.job_type] || "bg-secondary text-muted-foreground"}`}>
                                        {item.job_type}
                                    </span>
                                )}
                            </div>

                            {/* Title */}
                            <h3 className="text-base font-semibold text-foreground mb-2 line-clamp-2">
                                {item.job_title || "Job"}
                            </h3>

                            {/* Meta */}
                            <div className="flex flex-wrap gap-3 text-xs text-muted-foreground mb-4">
                                {item.location && (
                                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{item.location}</span>
                                )}
                                {item.salary_range && (
                                    <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" />{item.salary_range}</span>
                                )}
                            </div>

                            {/* Saved date + Apply */}
                            <div className="flex items-center justify-between">
                                <p className="text-[11px] text-muted-foreground/60">
                                    Saved {new Date(item.saved_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                                </p>
                                {item.apply_url ? (
                                    <a href={item.apply_url} target="_blank" rel="noopener noreferrer">
                                        <button className="flex items-center gap-1.5 text-xs font-medium text-primary border border-primary/40 px-3 py-1.5 rounded-lg hover:bg-primary/10 transition-colors">
                                            Apply <ExternalLink className="w-3 h-3" />
                                        </button>
                                    </a>
                                ) : (
                                    <span className="flex items-center gap-1 text-xs text-muted-foreground/50">
                                        <Briefcase className="w-3 h-3" /> No apply link
                                    </span>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    );
}

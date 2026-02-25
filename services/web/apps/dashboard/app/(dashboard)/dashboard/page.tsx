"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
    Briefcase, FileText, Send, TrendingUp, Sparkles, ArrowRight, Bot, Settings,
    MapPin, RefreshCw, Star, ChevronRight, ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { Job } from "@/types";

interface DashboardStats {
    jobCount: number;
    resumeCount: number;
    applicationCount: number;
}

const QUICK_ACTIONS = [
    { label: "Browse Jobs", href: "/jobs", icon: Briefcase, color: "from-violet-500 to-purple-600" },
    { label: "Analyze Resume", href: "/analyzer", icon: FileText, color: "from-emerald-500 to-teal-600" },
    { label: "AI Assistant", href: "/assistant", icon: Bot, color: "from-blue-500 to-cyan-600" },
    { label: "Settings", href: "/settings", icon: Settings, color: "from-amber-500 to-orange-600" },
];

export default function DashboardPage() {
    const user = useAuthStore((s) => s.user);
    const [stats, setStats] = useState<DashboardStats>({ jobCount: 0, resumeCount: 0, applicationCount: 0 });
    const [personalizedJobs, setPersonalizedJobs] = useState<Job[]>([]);
    const [prefs, setPrefs] = useState<{ target_roles: string[]; preferred_locations: string[]; hasPrefs: boolean }>({
        target_roles: [], preferred_locations: [], hasPrefs: false,
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const [jobs, resumes, apps, userPrefs] = await Promise.allSettled([
                    apiClient.listJobs(200, 0),
                    apiClient.listResumes(1, 0),
                    apiClient.listApplications(),
                    apiClient.getPreferences(),
                ]);

                const allJobs: Job[] = jobs.status === "fulfilled" && Array.isArray(jobs.value) ? jobs.value : [];

                let pRoles: string[] = [];
                let pLocations: string[] = [];
                let matchedJobs: Job[] = [];

                if (userPrefs.status === "fulfilled") {
                    const p = userPrefs.value;
                    pRoles = p.target_roles || [];
                    pLocations = p.preferred_locations || [];
                    const hasPrefs = pRoles.length > 0 || pLocations.length > 0;
                    setPrefs({ target_roles: pRoles, preferred_locations: pLocations, hasPrefs });

                    if (hasPrefs) {
                        matchedJobs = allJobs.filter((j) => {
                            const titleLower = (j.title || "").toLowerCase();
                            const locLower = (j.location || "").toLowerCase();
                            const roleMatch = pRoles.length === 0 || pRoles.some((r) => titleLower.includes(r.toLowerCase()));
                            const locMatch = pLocations.length === 0 || pLocations.some((l) =>
                                locLower.includes(l.toLowerCase()) || l.toLowerCase() === "remote"
                            );
                            return roleMatch || locMatch;
                        }).slice(0, 6);
                    }
                }

                setPersonalizedJobs(matchedJobs);
                setStats({
                    jobCount: allJobs.length,
                    resumeCount: resumes.status === "fulfilled" && Array.isArray(resumes.value) ? resumes.value.length : 0,
                    applicationCount: apps.status === "fulfilled" && Array.isArray(apps.value) ? apps.value.length : 0,
                });
            } catch { }
            setLoading(false);
        })();
    }, []);

    const displayName = user?.email?.split("@")[0] || "there";

    const statCards = [
        { label: "Available Jobs", value: stats.jobCount ? `${stats.jobCount}+` : "—", icon: Briefcase, color: "text-violet-400" },
        { label: "My Resumes", value: stats.resumeCount, icon: FileText, color: "text-emerald-400" },
        { label: "Applications", value: stats.applicationCount, icon: Send, color: "text-blue-400" },
    ];

    return (
        <div className="space-y-8">
            {/* Welcome */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                <h1 className="text-3xl font-bold text-foreground">
                    Welcome back, <span className="bg-gradient-to-r from-primary to-violet-400 bg-clip-text text-transparent">{displayName}</span> 👋
                </h1>
                <p className="text-muted-foreground mt-1">Here&apos;s what&apos;s happening with your career journey.</p>
            </motion.div>

            {/* Stats */}
            <div className="grid gap-4 md:grid-cols-3">
                {statCards.map((s, i) => (
                    <motion.div
                        key={s.label}
                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="border border-border/50 rounded-xl p-5 bg-card/50 backdrop-blur-sm"
                    >
                        <div className="flex items-center justify-between mb-3">
                            <s.icon className={`w-5 h-5 ${s.color}`} />
                            <TrendingUp className="w-4 h-4 text-muted-foreground/50" />
                        </div>
                        <p className="text-2xl font-bold text-foreground">{s.value}</p>
                        <p className="text-sm text-muted-foreground">{s.label}</p>
                    </motion.div>
                ))}
            </div>

            {/* Personalized Matches */}
            {!loading && prefs.hasPrefs && personalizedJobs.length > 0 && (
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                    <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                        <Star className="w-5 h-5 text-amber-400" />
                        Matches Your Preferences
                        <span className="ml-auto text-xs text-muted-foreground flex items-center gap-1">
                            {prefs.target_roles.slice(0, 2).map((r) => (
                                <span key={r} className="px-2 py-0.5 rounded-full bg-primary/10 text-primary">{r}</span>
                            ))}
                            {prefs.preferred_locations.slice(0, 2).map((l) => (
                                <span key={l} className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center gap-0.5">
                                    <MapPin className="w-2.5 h-2.5" />{l}
                                </span>
                            ))}
                        </span>
                    </h2>
                    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                        {personalizedJobs.map((job, i) => (
                            <motion.div
                                key={job.id}
                                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.35 + i * 0.05 }}
                                className="group border border-amber-500/20 rounded-xl p-4 bg-amber-500/5 hover:border-amber-500/40 hover:shadow-lg hover:shadow-amber-500/5 transition-all"
                            >
                                <div className="flex items-start justify-between gap-2 mb-2">
                                    <div>
                                        <p className="font-semibold text-sm text-foreground line-clamp-1">{job.title}</p>
                                        <p className="text-xs text-muted-foreground mt-0.5">{job.company_name}</p>
                                    </div>
                                    <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-medium">Match</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                                    <MapPin className="w-3 h-3 shrink-0" />
                                    <span className="truncate">{job.location || "Remote"}</span>
                                    {job.job_type && <span className="px-1.5 py-0.5 rounded bg-secondary/50">{job.job_type}</span>}
                                </div>
                                {job.apply_url && (
                                    <a
                                        href={job.apply_url} target="_blank" rel="noopener noreferrer"
                                        className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 font-medium transition-colors"
                                    >
                                        Apply Now <ExternalLink className="w-3 h-3" />
                                    </a>
                                )}
                            </motion.div>
                        ))}
                    </div>
                    <Link href="/jobs" className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mt-3 transition-colors w-fit">
                        View all matching jobs <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                </motion.div>
            )}

            {/* No preferences nudge */}
            {!loading && !prefs.hasPrefs && (
                <motion.div
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
                    className="border border-dashed border-primary/30 rounded-xl p-5 flex items-center justify-between bg-primary/5"
                >
                    <div className="flex items-center gap-3">
                        <RefreshCw className="w-5 h-5 text-primary" />
                        <div>
                            <p className="text-sm font-medium text-foreground">Set your job preferences</p>
                            <p className="text-xs text-muted-foreground">Get personalised job matches right here on your dashboard</p>
                        </div>
                    </div>
                    <Link
                        href="/settings"
                        className="flex items-center gap-1.5 text-xs font-medium text-primary border border-primary/40 px-3 py-1.5 rounded-lg hover:bg-primary/10 transition-colors whitespace-nowrap"
                    >
                        Set Preferences <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                </motion.div>
            )}

            {/* Quick Actions */}
            <div>
                <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary" /> Quick Actions
                </h2>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                    {QUICK_ACTIONS.map((a, i) => (
                        <motion.div
                            key={a.label}
                            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.4 + i * 0.05 }}
                        >
                            <Link
                                href={a.href}
                                className="group flex items-center gap-3 p-4 border border-border/50 rounded-xl bg-card/50 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5 transition-all"
                            >
                                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${a.color} flex items-center justify-center text-white`}>
                                    <a.icon className="w-5 h-5" />
                                </div>
                                <span className="font-medium text-foreground group-hover:text-primary transition-colors">{a.label}</span>
                                <ArrowRight className="w-4 h-4 ml-auto text-muted-foreground group-hover:text-primary transition-colors" />
                            </Link>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}

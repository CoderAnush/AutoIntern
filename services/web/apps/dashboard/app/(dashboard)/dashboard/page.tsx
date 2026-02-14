"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
    Briefcase, FileText, Send, TrendingUp, Sparkles, ArrowRight, Bot, Settings
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

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
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const [jobs, resumes, apps] = await Promise.allSettled([
                    apiClient.listJobs(1, 0),
                    apiClient.listResumes(1, 0),
                    apiClient.listApplications(),
                ]);
                setStats({
                    jobCount: jobs.status === "fulfilled" ? (Array.isArray(jobs.value) ? jobs.value.length : 0) : 0,
                    resumeCount: resumes.status === "fulfilled" ? (Array.isArray(resumes.value) ? resumes.value.length : 0) : 0,
                    applicationCount: apps.status === "fulfilled" ? (Array.isArray(apps.value) ? apps.value.length : 0) : 0,
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
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
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

            {/* Quick Actions */}
            <div>
                <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary" /> Quick Actions
                </h2>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                    {QUICK_ACTIONS.map((a, i) => (
                        <motion.div
                            key={a.label}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.2 + i * 0.05 }}
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

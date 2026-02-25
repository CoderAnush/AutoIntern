"use client";

import { useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
    BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { Send, TrendingUp, Trophy, XCircle, Clock, Loader2, Download } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Application } from "@/types";

const STATUS_COLORS: Record<string, string> = {
    applied: "#6366f1",
    interview: "#f59e0b",
    offer: "#10b981",
    rejected: "#ef4444",
};

const RADIAN = Math.PI / 180;
function CustomLabel({ cx, cy, midAngle, outerRadius, percent, name }: any) {
    if (percent < 0.05) return null;
    const r = outerRadius + 24;
    const x = cx + r * Math.cos(-midAngle * RADIAN);
    const y = cy + r * Math.sin(-midAngle * RADIAN);
    return (
        <text x={x} y={y} fill="#94a3b8" textAnchor={x > cx ? "start" : "end"} dominantBaseline="central" fontSize={11}>
            {name} ({(percent * 100).toFixed(0)}%)
        </text>
    );
}

function StatCard({ label, value, icon: Icon, color, sub }: {
    label: string; value: string | number; icon: any; color: string; sub?: string;
}) {
    return (
        <div className="border border-border/50 rounded-xl p-5 bg-card/50 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-3">
                <Icon className={`w-5 h-5 ${color}`} />
                <TrendingUp className="w-4 h-4 text-muted-foreground/30" />
            </div>
            <p className="text-2xl font-bold text-foreground">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
            {sub && <p className="text-xs text-muted-foreground/60 mt-0.5">{sub}</p>}
        </div>
    );
}

function exportToCSV(apps: Application[]) {
    const header = ["Role", "Company", "Status", "Date Applied", "Notes"];
    const rows = apps.map(a => [
        `"${(a.role_title || "").replace(/"/g, "'")}"`,
        `"${(a.company_name || "").replace(/"/g, "'")}"`,
        `"${a.status || ""}"`,
        `"${a.applied_at ? new Date(a.applied_at).toLocaleDateString() : ""}"`,
        `"${(a.notes || "").replace(/"/g, "'")}"`,
    ].join(","));
    const csv = [header.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `autointern-applications-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

export default function AnalyticsPage() {
    const [apps, setApps] = useState<Application[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiClient.listApplications().then(setApps).catch(() => { }).finally(() => setLoading(false));
    }, []);

    const stats = useMemo(() => {
        const total = apps.length;
        const byStatus = {
            applied: apps.filter(a => a.status === "applied").length,
            interview: apps.filter(a => a.status === "interview").length,
            offer: apps.filter(a => a.status === "offer").length,
            rejected: apps.filter(a => a.status === "rejected").length,
        };
        const responseRate = total > 0 ? Math.round(((byStatus.interview + byStatus.offer + byStatus.rejected) / total) * 100) : 0;
        const offerRate = total > 0 ? Math.round((byStatus.offer / total) * 100) : 0;
        return { total, byStatus, responseRate, offerRate };
    }, [apps]);

    // Funnel data
    const funnelData = [
        { stage: "Applied", count: stats.total, fill: STATUS_COLORS.applied },
        { stage: "Heard Back", count: stats.byStatus.interview + stats.byStatus.offer + stats.byStatus.rejected, fill: "#8b5cf6" },
        { stage: "Interview", count: stats.byStatus.interview, fill: STATUS_COLORS.interview },
        { stage: "Offer", count: stats.byStatus.offer, fill: STATUS_COLORS.offer },
    ];

    // Donut chart data
    const pieData = Object.entries(stats.byStatus)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value }));

    // Monthly timeline
    const monthlyData = useMemo(() => {
        const map: Record<string, number> = {};
        apps.forEach(a => {
            const month = new Date(a.applied_at).toLocaleDateString("en-US", { month: "short", year: "2-digit" });
            map[month] = (map[month] || 0) + 1;
        });
        return Object.entries(map).map(([month, count]) => ({ month, count })).slice(-8);
    }, [apps]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-24">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Analytics</h1>
                    <p className="text-muted-foreground mt-1">Track your job search performance and conversion rates</p>
                </div>
                {apps.length > 0 && (
                    <button
                        onClick={() => exportToCSV(apps)}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-border/50 bg-card/50 hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <Download className="w-4 h-4" />
                        Export CSV
                    </button>
                )}
            </div>

            {/* KPI Strip */}
            <div className="grid gap-4 md:grid-cols-4">
                <StatCard label="Total Applications" value={stats.total} icon={Send} color="text-violet-400" />
                <StatCard label="Response Rate" value={`${stats.responseRate}%`} icon={TrendingUp} color="text-blue-400" sub="Applied → heard back" />
                <StatCard label="Offer Rate" value={`${stats.offerRate}%`} icon={Trophy} color="text-emerald-400" sub="Applied → offer" />
                <StatCard label="Rejections" value={stats.byStatus.rejected} icon={XCircle} color="text-red-400" />
            </div>

            {apps.length === 0 ? (
                <div className="text-center py-20 border border-dashed border-border/40 rounded-xl">
                    <Send className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
                    <p className="text-muted-foreground font-medium">No applications yet</p>
                    <p className="text-sm text-muted-foreground/60 mt-1">Add applications in the Applications tab to see analytics</p>
                </div>
            ) : (
                <div className="grid gap-6 md:grid-cols-2">
                    {/* Funnel */}
                    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                        className="border border-border/50 rounded-xl p-5 bg-card/50">
                        <h2 className="text-base font-semibold text-foreground mb-4">Application Funnel</h2>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={funnelData} layout="vertical" margin={{ left: 16, right: 24 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" horizontal={false} />
                                <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} />
                                <YAxis type="category" dataKey="stage" tick={{ fill: "#94a3b8", fontSize: 11 }} width={72} />
                                <Tooltip
                                    contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                    labelStyle={{ color: "#f1f5f9" }}
                                    itemStyle={{ color: "#94a3b8" }}
                                />
                                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                                    {funnelData.map((entry, idx) => (
                                        <Cell key={idx} fill={entry.fill} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </motion.div>

                    {/* Donut */}
                    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
                        className="border border-border/50 rounded-xl p-5 bg-card/50">
                        <h2 className="text-base font-semibold text-foreground mb-4">Status Breakdown</h2>
                        {pieData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={220}>
                                <PieChart>
                                    <Pie
                                        data={pieData} cx="50%" cy="50%"
                                        innerRadius={55} outerRadius={80}
                                        dataKey="value"
                                        labelLine={false}
                                        label={CustomLabel}
                                    >
                                        {pieData.map((entry, idx) => (
                                            <Cell key={idx} fill={STATUS_COLORS[entry.name.toLowerCase()] || "#6366f1"} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                        itemStyle={{ color: "#94a3b8" }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <p className="text-center text-muted-foreground text-sm py-16">No data</p>
                        )}
                    </motion.div>

                    {/* Timeline */}
                    {monthlyData.length > 1 && (
                        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                            className="md:col-span-2 border border-border/50 rounded-xl p-5 bg-card/50">
                            <h2 className="text-base font-semibold text-foreground mb-4">Applications Over Time</h2>
                            <ResponsiveContainer width="100%" height={180}>
                                <LineChart data={monthlyData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                                    <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 11 }} />
                                    <YAxis tick={{ fill: "#64748b", fontSize: 11 }} allowDecimals={false} />
                                    <Tooltip
                                        contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                        itemStyle={{ color: "#94a3b8" }}
                                    />
                                    <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} dot={{ r: 4, fill: "#6366f1" }} name="Applications" />
                                </LineChart>
                            </ResponsiveContainer>
                        </motion.div>
                    )}
                </div>
            )}
        </div>
    );
}

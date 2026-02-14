"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Plus, GripVertical, Trash2, Briefcase, Loader2, X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import { Application } from "@/types";
import toast from "react-hot-toast";

const COLUMNS = [
    { key: "applied", label: "Applied", color: "border-blue-500/40 bg-blue-500/5" },
    { key: "interview", label: "Interview", color: "border-amber-500/40 bg-amber-500/5" },
    { key: "offer", label: "Offer", color: "border-emerald-500/40 bg-emerald-500/5" },
    { key: "rejected", label: "Rejected", color: "border-red-500/40 bg-red-500/5" },
] as const;

export default function ApplicationsPage() {
    const [applications, setApplications] = useState<Application[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [companyName, setCompanyName] = useState("");
    const [roleTitle, setRoleTitle] = useState("");
    const [creating, setCreating] = useState(false);

    useEffect(() => { fetchApps(); }, []);

    const fetchApps = async () => {
        setLoading(true);
        try {
            const data = await apiClient.listApplications();
            setApplications(data);
        } catch { }
        setLoading(false);
    };

    const handleCreate = async () => {
        if (!companyName || !roleTitle) { toast.error("Company & role required"); return; }
        setCreating(true);
        try {
            await apiClient.createApplication({ company_name: companyName, role_title: roleTitle, status: "applied" });
            toast.success("Application added!");
            setCompanyName("");
            setRoleTitle("");
            setShowForm(false);
            fetchApps();
        } catch {
            toast.error("Failed to add application");
        }
        setCreating(false);
    };

    const handleStatusUpdate = async (app: Application, newStatus: string) => {
        try {
            await apiClient.updateApplication(app.id, { status: newStatus });
            setApplications((prev) =>
                prev.map((a) => (a.id === app.id ? { ...a, status: newStatus as any } : a))
            );
        } catch {
            toast.error("Failed to update status");
        }
    };

    const handleDelete = async (id: string) => {
        try {
            await apiClient.deleteApplication(id);
            setApplications((prev) => prev.filter((a) => a.id !== id));
            toast.success("Deleted");
        } catch {
            toast.error("Failed to delete");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Applications</h1>
                    <p className="text-muted-foreground mt-1">Track your job applications</p>
                </div>
                <Button onClick={() => setShowForm(true)} className="gap-2">
                    <Plus className="w-4 h-4" /> Add Application
                </Button>
            </div>

            {/* Add Form */}
            <AnimatePresence>
                {showForm && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="border border-border/50 rounded-xl p-4 bg-card/50 backdrop-blur-sm overflow-hidden"
                    >
                        <div className="flex items-end gap-3">
                            <div className="flex-1 space-y-1">
                                <Label className="text-xs">Company</Label>
                                <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="e.g. Google" className="h-9 bg-secondary/50" />
                            </div>
                            <div className="flex-1 space-y-1">
                                <Label className="text-xs">Role</Label>
                                <Input value={roleTitle} onChange={(e) => setRoleTitle(e.target.value)} placeholder="e.g. SWE Intern" className="h-9 bg-secondary/50" />
                            </div>
                            <Button onClick={handleCreate} disabled={creating} size="sm" className="gap-1">
                                {creating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                                Add
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}><X className="w-4 h-4" /></Button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Kanban Board */}
            {loading ? (
                <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
            ) : (
                <div className="grid gap-4 md:grid-cols-4">
                    {COLUMNS.map((col) => {
                        const items = applications.filter((a) => a.status === col.key);
                        return (
                            <div key={col.key} className={`border rounded-xl p-3 min-h-[200px] ${col.color}`}>
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-sm font-semibold text-foreground">{col.label}</h3>
                                    <span className="text-xs text-muted-foreground bg-secondary/50 px-2 py-0.5 rounded-full">{items.length}</span>
                                </div>
                                <div className="space-y-2">
                                    <AnimatePresence>
                                        {items.map((app) => (
                                            <motion.div
                                                key={app.id}
                                                layout
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, scale: 0.9 }}
                                                className="bg-card border border-border/40 rounded-lg p-3 group"
                                            >
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <p className="font-medium text-sm text-foreground">{app.role_title}</p>
                                                        <p className="text-xs text-muted-foreground">{app.company_name}</p>
                                                    </div>
                                                    <button onClick={() => handleDelete(app.id)} className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-red-400">
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                                {/* Status move buttons */}
                                                <div className="flex gap-1 mt-2">
                                                    {COLUMNS.filter((c) => c.key !== col.key).map((c) => (
                                                        <button
                                                            key={c.key}
                                                            onClick={() => handleStatusUpdate(app, c.key)}
                                                            className="text-[10px] px-1.5 py-0.5 rounded bg-secondary/50 text-muted-foreground hover:text-foreground hover:bg-secondary transition-all"
                                                        >
                                                            → {c.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            </motion.div>
                                        ))}
                                    </AnimatePresence>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

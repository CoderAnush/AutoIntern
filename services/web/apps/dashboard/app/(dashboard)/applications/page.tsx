"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Plus, Trash2, Briefcase, Loader2, X, ExternalLink,
    GripVertical, StickyNote, Calendar, Building2, ChevronDown, Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import { Application } from "@/types";
import toast from "react-hot-toast";

// ── Constants ────────────────────────────────────────────────────────────────

type Status = "applied" | "interview" | "offer" | "rejected";

const COLUMNS: { key: Status; label: string; color: string; dot: string }[] = [
    { key: "applied", label: "Applied", color: "border-blue-500/40 bg-blue-500/5", dot: "bg-blue-400" },
    { key: "interview", label: "Interview", color: "border-amber-500/40 bg-amber-500/5", dot: "bg-amber-400" },
    { key: "offer", label: "Offer", color: "border-emerald-500/40 bg-emerald-500/5", dot: "bg-emerald-400" },
    { key: "rejected", label: "Rejected", color: "border-red-500/40 bg-red-500/5", dot: "bg-red-400" },
];

function timeAgo(dateStr?: string) {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days < 30) return `${days}d ago`;
    return `${Math.floor(days / 30)}mo ago`;
}

// ── Notes Modal ──────────────────────────────────────────────────────────────

function NotesModal({
    app,
    onClose,
    onSave,
}: {
    app: Application;
    onClose: () => void;
    onSave: (id: string, notes: string) => Promise<void>;
}) {
    const [notes, setNotes] = useState(app.notes ?? "");
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        await onSave(app.id, notes);
        setSaving(false);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
            <motion.div
                className="relative z-10 w-full max-w-md rounded-2xl bg-card border border-border/60 shadow-2xl p-6 space-y-4"
                initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            >
                <div className="flex items-center justify-between">
                    <h2 className="font-bold text-foreground">{app.role_title} @ {app.company_name}</h2>
                    <button onClick={onClose} className="text-muted-foreground hover:text-foreground p-1"><X className="w-4 h-4" /></button>
                </div>
                <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={6}
                    placeholder="Add notes about this application — interview tips, contacts, deadlines…"
                    className="w-full rounded-lg bg-secondary/50 border border-border/50 text-sm text-foreground p-3 focus:outline-none focus:border-primary/60 resize-none"
                />
                <div className="flex gap-2 justify-end">
                    <Button variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
                    <Button size="sm" className="gap-1.5" onClick={handleSave} disabled={saving}>
                        {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                        Save Notes
                    </Button>
                </div>
            </motion.div>
        </div>
    );
}

// ── Application Card ─────────────────────────────────────────────────────────

function AppCard({
    app,
    onDelete,
    onStatusChange,
    onEditNotes,
    currentStatus,
}: {
    app: Application;
    onDelete: (id: string) => void;
    onStatusChange: (app: Application, status: Status) => void;
    onEditNotes: (app: Application) => void;
    currentStatus: Status;
}) {
    const [showMove, setShowMove] = useState(false);
    const otherColumns = COLUMNS.filter((c) => c.key !== currentStatus);

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-card border border-border/40 rounded-xl p-3.5 group hover:border-primary/30 hover:shadow-md hover:shadow-primary/5 transition-all duration-200"
        >
            {/* Header row */}
            <div className="flex items-start justify-between gap-2 mb-1.5">
                <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-foreground leading-tight truncate">{app.role_title}</p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                        <Building2 className="w-3 h-3 shrink-0" />
                        <span className="truncate">{app.company_name}</span>
                    </p>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    <button
                        onClick={() => onEditNotes(app)}
                        className="p-1 rounded text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                        title="Edit notes"
                    >
                        <StickyNote className="w-3.5 h-3.5" />
                    </button>
                    <button
                        onClick={() => onDelete(app.id)}
                        className="p-1 rounded text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Delete"
                    >
                        <Trash2 className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Notes snippet */}
            {app.notes && (
                <p className="text-[11px] text-muted-foreground italic line-clamp-1 mb-2 px-0.5">{app.notes}</p>
            )}

            {/* Meta row */}
            <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Calendar className="w-3 h-3" /> {timeAgo(app.applied_at)}
                </span>
                <div className="flex items-center gap-1.5">
                    {app.apply_url && (
                        <a
                            href={app.apply_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-primary hover:text-primary/80 flex items-center gap-0.5 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                        >
                            Apply <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                    )}
                    {/* Move to column */}
                    <div className="relative">
                        <button
                            onClick={() => setShowMove((v) => !v)}
                            className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-secondary/50 hover:bg-secondary transition-all"
                        >
                            Move <ChevronDown className="w-2.5 h-2.5" />
                        </button>
                        <AnimatePresence>
                            {showMove && (
                                <motion.div
                                    initial={{ opacity: 0, y: 4, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 4, scale: 0.95 }}
                                    className="absolute right-0 top-6 z-20 bg-card border border-border/60 rounded-lg shadow-xl shadow-black/30 min-w-[120px] py-1 overflow-hidden"
                                >
                                    {otherColumns.map((c) => (
                                        <button
                                            key={c.key}
                                            onClick={() => { onStatusChange(app, c.key); setShowMove(false); }}
                                            className="w-full text-left px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-secondary/80 flex items-center gap-2 transition-colors"
                                        >
                                            <span className={`w-2 h-2 rounded-full ${c.dot}`} />
                                            {c.label}
                                        </button>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}

// ── Add Application Form ─────────────────────────────────────────────────────

function AddForm({ onAdd, onCancel }: {
    onAdd: (company: string, role: string, applyUrl: string) => Promise<void>;
    onCancel: () => void;
}) {
    const [company, setCompany] = useState("");
    const [role, setRole] = useState("");
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);

    const handle = async () => {
        if (!company || !role) { toast.error("Company & role required"); return; }
        setLoading(true);
        await onAdd(company, role, url);
        setLoading(false);
    };

    return (
        <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border border-primary/30 rounded-xl p-4 bg-primary/5 backdrop-blur-sm overflow-hidden"
        >
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
                <div className="space-y-1">
                    <Label className="text-xs">Company *</Label>
                    <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Flipkart" className="h-9 bg-secondary/50" />
                </div>
                <div className="space-y-1">
                    <Label className="text-xs">Role *</Label>
                    <Input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. SDE Intern" className="h-9 bg-secondary/50" />
                </div>
                <div className="space-y-1">
                    <Label className="text-xs">Apply URL <span className="text-muted-foreground">(optional)</span></Label>
                    <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" className="h-9 bg-secondary/50" />
                </div>
            </div>
            <div className="flex gap-2 justify-end">
                <Button variant="ghost" size="sm" onClick={onCancel}><X className="w-3.5 h-3.5 mr-1" /> Cancel</Button>
                <Button size="sm" onClick={handle} disabled={loading} className="gap-1.5">
                    {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                    Add Application
                </Button>
            </div>
        </motion.div>
    );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function ApplicationsPage() {
    const [applications, setApplications] = useState<Application[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingNotes, setEditingNotes] = useState<Application | null>(null);

    useEffect(() => { fetchApps(); }, []);

    const fetchApps = async () => {
        setLoading(true);
        try {
            const data = await apiClient.listApplications();
            setApplications(data);
        } catch (e: any) {
            toast.error("Failed to load applications");
        }
        setLoading(false);
    };

    const handleAdd = async (company: string, role: string, applyUrl: string) => {
        try {
            const created = await apiClient.createApplication({
                company_name: company,
                role_title: role,
                status: "applied",
                apply_url: applyUrl || null,
            });
            setApplications((prev) => [created, ...prev]);
            setShowForm(false);
            toast.success("Application added!");
        } catch (e: any) {
            const detail = e?.response?.data?.detail || "Failed to add application";
            toast.error(detail);
        }
    };

    const handleStatusChange = async (app: Application, newStatus: Status) => {
        try {
            const updated = await apiClient.updateApplication(app.id, { status: newStatus });
            setApplications((prev) => prev.map((a) => (a.id === app.id ? updated : a)));
        } catch {
            toast.error("Failed to update status");
        }
    };

    const handleSaveNotes = async (id: string, notes: string) => {
        try {
            const updated = await apiClient.updateApplication(id, { notes });
            setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
            toast.success("Notes saved");
        } catch {
            toast.error("Failed to save notes");
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

    const totalCount = applications.length;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Applications</h1>
                    <p className="text-muted-foreground mt-1">
                        {totalCount > 0
                            ? `Tracking ${totalCount} application${totalCount !== 1 ? "s" : ""} across ${COLUMNS.length} stages`
                            : "Track every job application in one place"}
                    </p>
                </div>
                <Button onClick={() => setShowForm((v) => !v)} className="gap-2">
                    <Plus className="w-4 h-4" /> Add Application
                </Button>
            </div>

            {/* Stats strip */}
            {totalCount > 0 && (
                <div className="grid grid-cols-4 gap-3">
                    {COLUMNS.map((col) => {
                        const count = applications.filter((a) => a.status === col.key).length;
                        return (
                            <div key={col.key} className={`border rounded-xl p-3 text-center ${col.color}`}>
                                <p className="text-2xl font-bold text-foreground">{count}</p>
                                <p className="text-xs text-muted-foreground mt-0.5">{col.label}</p>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Add form */}
            <AnimatePresence>
                {showForm && (
                    <AddForm onAdd={handleAdd} onCancel={() => setShowForm(false)} />
                )}
            </AnimatePresence>

            {/* Kanban board */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-4">
                    {COLUMNS.map((col) => {
                        const items = applications.filter((a) => a.status === col.key);
                        return (
                            <div key={col.key} className={`border rounded-xl p-3 min-h-[260px] ${col.color}`}>
                                {/* Column header */}
                                <div className="flex items-center justify-between mb-3 pb-2 border-b border-border/30">
                                    <div className="flex items-center gap-2">
                                        <span className={`w-2 h-2 rounded-full ${col.dot}`} />
                                        <h3 className="text-sm font-semibold text-foreground">{col.label}</h3>
                                    </div>
                                    <span className="text-xs text-muted-foreground bg-secondary/50 px-2 py-0.5 rounded-full">
                                        {items.length}
                                    </span>
                                </div>

                                {/* Cards */}
                                <div className="space-y-2">
                                    <AnimatePresence>
                                        {items.length === 0 ? (
                                            <p className="text-[11px] text-muted-foreground/50 text-center py-8 italic">
                                                No applications here yet
                                            </p>
                                        ) : (
                                            items.map((app) => (
                                                <AppCard
                                                    key={app.id}
                                                    app={app}
                                                    currentStatus={col.key}
                                                    onDelete={handleDelete}
                                                    onStatusChange={handleStatusChange}
                                                    onEditNotes={setEditingNotes}
                                                />
                                            ))
                                        )}
                                    </AnimatePresence>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Empty state */}
            {!loading && totalCount === 0 && !showForm && (
                <div className="text-center py-16">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary/10 flex items-center justify-center">
                        <Briefcase className="w-8 h-8 text-primary" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">Start tracking applications</h3>
                    <p className="text-muted-foreground mb-4 max-w-sm mx-auto text-sm">
                        Add your first application and track its progress from Applied → Interview → Offer.
                    </p>
                    <Button onClick={() => setShowForm(true)} className="gap-2">
                        <Plus className="w-4 h-4" /> Add First Application
                    </Button>
                </div>
            )}

            {/* Notes modal */}
            <AnimatePresence>
                {editingNotes && (
                    <NotesModal
                        app={editingNotes}
                        onClose={() => setEditingNotes(null)}
                        onSave={handleSaveNotes}
                    />
                )}
            </AnimatePresence>
        </div>
    );
}

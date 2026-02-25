"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    User, Lock, Bell, Loader2, Save, X, Plus, Briefcase, MapPin, RefreshCw, Wifi
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { EmailPreferences } from "@/types";
import toast from "react-hot-toast";

const TABS = [
    { key: "profile", label: "Profile", icon: User },
    { key: "preferences", label: "Job Preferences", icon: Briefcase },
    { key: "security", label: "Security", icon: Lock },
    { key: "notifications", label: "Notifications", icon: Bell },
] as const;

type TabKey = typeof TABS[number]["key"];

// ── Reusable helpers ─────────────────────────────────────────────────────────

function Toggle({ checked, onChange, label, desc }: {
    checked: boolean; onChange: (v: boolean) => void; label: string; desc: string;
}) {
    return (
        <div className="flex items-center justify-between py-3 border-b border-border/30 last:border-0">
            <div>
                <p className="text-sm font-medium text-foreground">{label}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
            </div>
            <button
                onClick={() => onChange(!checked)}
                className={`relative w-11 h-6 rounded-full transition-colors ${checked ? "bg-primary" : "bg-secondary"}`}
            >
                <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${checked ? "translate-x-5" : ""}`} />
            </button>
        </div>
    );
}

function TagInput({ label, values, onChange, placeholder }: {
    label: string; values: string[]; onChange: (v: string[]) => void; placeholder: string;
}) {
    const [input, setInput] = useState("");

    const add = () => {
        const v = input.trim();
        if (v && !values.includes(v)) { onChange([...values, v]); }
        setInput("");
    };

    return (
        <div className="space-y-2">
            <Label className="text-sm">{label}</Label>
            <div className="flex gap-2">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
                    placeholder={placeholder}
                    className="h-9 bg-secondary/50 flex-1"
                />
                <Button size="sm" variant="outline" onClick={add} className="gap-1"><Plus className="w-3.5 h-3.5" /></Button>
            </div>
            {values.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-1">
                    {values.map((v) => (
                        <span key={v} className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-primary/15 text-primary text-xs font-medium">
                            {v}
                            <button onClick={() => onChange(values.filter((x) => x !== v))} className="hover:text-red-400 transition-colors">
                                <X className="w-3 h-3" />
                            </button>
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<TabKey>("profile");
    const user = useAuthStore((s) => s.user);

    // Security
    const [oldPass, setOldPass] = useState("");
    const [newPass, setNewPass] = useState("");
    const [changingPass, setChangingPass] = useState(false);

    // Notifications
    const [prefs, setPrefs] = useState<EmailPreferences>({
        notify_on_new_jobs: true, notify_on_resume_upload: true,
        notify_on_password_change: true, weekly_digest: true, email_frequency: "weekly",
    });
    const [loadingPrefs, setLoadingPrefs] = useState(false);
    const [savingPrefs, setSavingPrefs] = useState(false);

    // Job Preferences
    const [jobPrefs, setJobPrefs] = useState({
        target_roles: [] as string[],
        preferred_locations: [] as string[],
        preferred_job_types: [] as string[],
        min_salary: "",
        open_to_remote: true,
    });
    const [loadingJobPrefs, setLoadingJobPrefs] = useState(false);
    const [savingJobPrefs, setSavingJobPrefs] = useState(false);

    // Scheduler status
    const [schedulerStatus, setSchedulerStatus] = useState<any>(null);
    const [triggering, setTriggering] = useState(false);

    useEffect(() => {
        if (activeTab === "notifications") loadNotifPrefs();
        if (activeTab === "preferences") { loadJobPrefs(); loadSchedulerStatus(); }
    }, [activeTab]);

    const loadNotifPrefs = async () => {
        setLoadingPrefs(true);
        try { setPrefs(await apiClient.getEmailPreferences()); } catch { }
        setLoadingPrefs(false);
    };

    const saveNotifPrefs = async () => {
        setSavingPrefs(true);
        try { await apiClient.updateEmailPreferences(prefs as any); toast.success("Saved!"); }
        catch { toast.error("Failed to save"); }
        setSavingPrefs(false);
    };

    const loadJobPrefs = async () => {
        setLoadingJobPrefs(true);
        try {
            const data = await apiClient.getPreferences();
            setJobPrefs({
                target_roles: data.target_roles || [],
                preferred_locations: data.preferred_locations || [],
                preferred_job_types: data.preferred_job_types || [],
                min_salary: data.min_salary || "",
                open_to_remote: data.open_to_remote ?? true,
            });
        } catch { }
        setLoadingJobPrefs(false);
    };

    const saveJobPrefs = async () => {
        setSavingJobPrefs(true);
        try {
            await apiClient.updatePreferences({
                ...jobPrefs,
                min_salary: jobPrefs.min_salary || null,
            });
            toast.success("Job preferences saved!");
        } catch { toast.error("Failed to save preferences"); }
        setSavingJobPrefs(false);
    };

    const loadSchedulerStatus = async () => {
        try { setSchedulerStatus(await apiClient.getSchedulerStatus()); } catch { }
    };

    const triggerSync = async () => {
        setTriggering(true);
        try {
            await apiClient.triggerSchedulerSync();
            toast.success("Sync triggered! Check back in a minute.");
            setTimeout(loadSchedulerStatus, 3000);
        } catch (e: any) {
            toast.error(e?.response?.data?.detail || "Failed to trigger sync");
        }
        setTriggering(false);
    };

    const handleChangePassword = async () => {
        if (!oldPass || !newPass) { toast.error("Both fields required"); return; }
        setChangingPass(true);
        try {
            await apiClient.changePassword(oldPass, newPass);
            toast.success("Password changed!");
            setOldPass(""); setNewPass("");
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to change password");
        }
        setChangingPass(false);
    };

    const JOB_TYPES = ["Full-time", "Part-time", "Internship", "Contract", "Remote"];

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-foreground">Settings</h1>
                <p className="text-muted-foreground mt-1">Manage your account, job preferences, and notifications</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 border-b border-border/50 pb-px overflow-x-auto">
                {TABS.map((t) => (
                    <button
                        key={t.key}
                        onClick={() => setActiveTab(t.key)}
                        className={`flex items-center gap-2 px-4 py-2.5 rounded-t-lg text-sm font-medium whitespace-nowrap transition-all
                            ${activeTab === t.key
                                ? "bg-card border border-border/50 border-b-card text-foreground -mb-px"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        <t.icon className="w-4 h-4" /> {t.label}
                    </button>
                ))}
            </div>

            <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="border border-border/50 rounded-xl p-6 bg-card/50 backdrop-blur-sm"
            >
                {/* ── Profile ── */}
                {activeTab === "profile" && (
                    <div className="space-y-4 max-w-md">
                        <h2 className="text-xl font-semibold">Profile Information</h2>
                        <div className="space-y-2">
                            <Label>Email</Label>
                            <Input value={user?.email || ""} disabled className="h-11 bg-secondary/50" />
                        </div>
                        <div className="space-y-2">
                            <Label>Account ID</Label>
                            <Input value={user?.id || ""} disabled className="h-11 bg-secondary/50 font-mono text-xs" />
                        </div>
                    </div>
                )}

                {/* ── Job Preferences ── */}
                {activeTab === "preferences" && (
                    <div className="space-y-6 max-w-xl">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">Job Preferences</h2>
                            <p className="text-xs text-muted-foreground">Used to personalise your dashboard</p>
                        </div>

                        {loadingJobPrefs ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                            </div>
                        ) : (
                            <div className="space-y-5">
                                <TagInput
                                    label="Target Roles"
                                    values={jobPrefs.target_roles}
                                    onChange={(v) => setJobPrefs({ ...jobPrefs, target_roles: v })}
                                    placeholder="e.g. Software Engineer, Data Scientist"
                                />
                                <TagInput
                                    label="Preferred Locations"
                                    values={jobPrefs.preferred_locations}
                                    onChange={(v) => setJobPrefs({ ...jobPrefs, preferred_locations: v })}
                                    placeholder="e.g. Bangalore, Remote, Mumbai"
                                />

                                <div className="space-y-2">
                                    <Label className="text-sm">Preferred Job Types</Label>
                                    <div className="flex flex-wrap gap-2">
                                        {JOB_TYPES.map((jt) => (
                                            <button
                                                key={jt}
                                                onClick={() => {
                                                    const cur = jobPrefs.preferred_job_types;
                                                    setJobPrefs({
                                                        ...jobPrefs,
                                                        preferred_job_types: cur.includes(jt)
                                                            ? cur.filter((x) => x !== jt)
                                                            : [...cur, jt],
                                                    });
                                                }}
                                                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all border
                                                    ${jobPrefs.preferred_job_types.includes(jt)
                                                        ? "bg-primary text-primary-foreground border-primary"
                                                        : "bg-secondary/50 text-muted-foreground border-border/40 hover:bg-secondary"
                                                    }`}
                                            >
                                                {jt}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-sm">Minimum Salary</Label>
                                    <Input
                                        value={jobPrefs.min_salary}
                                        onChange={(e) => setJobPrefs({ ...jobPrefs, min_salary: e.target.value })}
                                        placeholder="e.g. ₹15L/yr or $80K/yr"
                                        className="h-9 bg-secondary/50 max-w-xs"
                                    />
                                </div>

                                <Toggle
                                    checked={jobPrefs.open_to_remote}
                                    onChange={(v) => setJobPrefs({ ...jobPrefs, open_to_remote: v })}
                                    label="Open to Remote"
                                    desc="Include remote and hybrid positions in recommendations"
                                />

                                <Button onClick={saveJobPrefs} disabled={savingJobPrefs} className="gap-2">
                                    {savingJobPrefs ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Save Preferences
                                </Button>
                            </div>
                        )}

                        {/* Scheduler Status */}
                        <div className="border border-border/40 rounded-xl p-4 bg-secondary/20 space-y-3 mt-4">
                            <div className="flex items-center justify-between">
                                <h3 className="font-semibold text-sm flex items-center gap-2">
                                    <RefreshCw className="w-4 h-4 text-primary" /> Job Sync Scheduler
                                </h3>
                                <Button
                                    size="sm" variant="outline"
                                    onClick={triggerSync}
                                    disabled={triggering || schedulerStatus?.running}
                                    className="gap-1.5 text-xs h-7"
                                >
                                    {triggering ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wifi className="w-3 h-3" />}
                                    {schedulerStatus?.running ? "Syncing…" : "Sync Now"}
                                </Button>
                            </div>
                            {schedulerStatus ? (
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div>
                                        <p className="text-muted-foreground">Last Run</p>
                                        <p className="text-foreground font-medium">
                                            {schedulerStatus.last_run
                                                ? new Date(schedulerStatus.last_run).toLocaleString()
                                                : "Never"}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Status</p>
                                        <p className={`font-medium capitalize ${schedulerStatus.last_run_status === "success" ? "text-emerald-400" : schedulerStatus.last_run_status === "error" ? "text-red-400" : "text-muted-foreground"}`}>
                                            {schedulerStatus.last_run_status}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Jobs Added Last Run</p>
                                        <p className="text-foreground font-medium">{schedulerStatus.jobs_added_last_run}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Frequency</p>
                                        <p className="text-foreground font-medium">Every 24 hours</p>
                                    </div>
                                </div>
                            ) : (
                                <p className="text-xs text-muted-foreground">Loading scheduler status…</p>
                            )}
                        </div>
                    </div>
                )}

                {/* ── Security ── */}
                {activeTab === "security" && (
                    <div className="space-y-4 max-w-md">
                        <h2 className="text-xl font-semibold">Change Password</h2>
                        <div className="space-y-2">
                            <Label>Current Password</Label>
                            <Input type="password" value={oldPass} onChange={(e) => setOldPass(e.target.value)} className="h-11 bg-secondary/50" />
                        </div>
                        <div className="space-y-2">
                            <Label>New Password</Label>
                            <Input type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} className="h-11 bg-secondary/50" />
                        </div>
                        <Button onClick={handleChangePassword} disabled={changingPass} className="gap-2">
                            {changingPass ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                            Change Password
                        </Button>
                    </div>
                )}

                {/* ── Notifications ── */}
                {activeTab === "notifications" && (
                    <div className="space-y-4 max-w-lg">
                        <h2 className="text-xl font-semibold">Email Notifications</h2>
                        {loadingPrefs ? (
                            <div className="flex items-center justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
                        ) : (
                            <>
                                <Toggle checked={prefs.notify_on_new_jobs} onChange={(v) => setPrefs({ ...prefs, notify_on_new_jobs: v })} label="New Job Alerts" desc="Get notified when new jobs matching your profile are posted" />
                                <Toggle checked={prefs.notify_on_resume_upload} onChange={(v) => setPrefs({ ...prefs, notify_on_resume_upload: v })} label="Resume Upload Confirmation" desc="Receive confirmation when a resume is uploaded" />
                                <Toggle checked={prefs.notify_on_password_change} onChange={(v) => setPrefs({ ...prefs, notify_on_password_change: v })} label="Security Alerts" desc="Get notified when your password is changed" />
                                <Toggle checked={prefs.weekly_digest} onChange={(v) => setPrefs({ ...prefs, weekly_digest: v })} label="Weekly Digest" desc="A weekly summary of top matched jobs" />
                                <div className="pt-2">
                                    <Label className="text-sm">Email Frequency</Label>
                                    <div className="flex gap-2 mt-2">
                                        {(["daily", "weekly", "never"] as const).map((f) => (
                                            <button key={f} onClick={() => setPrefs({ ...prefs, email_frequency: f })}
                                                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${prefs.email_frequency === f ? "bg-primary text-primary-foreground" : "bg-secondary/50 text-muted-foreground hover:bg-secondary"}`}>
                                                {f}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <Button onClick={saveNotifPrefs} disabled={savingPrefs} className="mt-4 gap-2">
                                    {savingPrefs ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Save Notifications
                                </Button>
                            </>
                        )}
                    </div>
                )}
            </motion.div>
        </div>
    );
}

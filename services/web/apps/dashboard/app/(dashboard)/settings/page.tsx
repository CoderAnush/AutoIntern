"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    User, Lock, Bell, CreditCard, Loader2, Save, CheckCircle2, Mail
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
    { key: "security", label: "Security", icon: Lock },
    { key: "notifications", label: "Notifications", icon: Bell },
] as const;

type TabKey = typeof TABS[number]["key"];

function Toggle({
    checked, onChange, label, desc,
}: { checked: boolean; onChange: (v: boolean) => void; label: string; desc: string }) {
    return (
        <div className="flex items-center justify-between py-3">
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

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<TabKey>("profile");
    const user = useAuthStore((s) => s.user);

    // Security
    const [oldPass, setOldPass] = useState("");
    const [newPass, setNewPass] = useState("");
    const [changingPass, setChangingPass] = useState(false);

    // Notifications — real API wiring
    const [prefs, setPrefs] = useState<EmailPreferences>({
        notify_on_new_jobs: true,
        notify_on_resume_upload: true,
        notify_on_password_change: true,
        weekly_digest: true,
        email_frequency: "weekly",
    });
    const [loadingPrefs, setLoadingPrefs] = useState(false);
    const [savingPrefs, setSavingPrefs] = useState(false);

    useEffect(() => {
        if (activeTab === "notifications") loadPrefs();
    }, [activeTab]);

    const loadPrefs = async () => {
        setLoadingPrefs(true);
        try {
            const data = await apiClient.getEmailPreferences();
            setPrefs(data);
        } catch { }
        setLoadingPrefs(false);
    };

    const savePrefs = async () => {
        setSavingPrefs(true);
        try {
            await apiClient.updateEmailPreferences(prefs as any);
            toast.success("Preferences saved!");
        } catch {
            toast.error("Failed to save preferences");
        }
        setSavingPrefs(false);
    };

    const handleChangePassword = async () => {
        if (!oldPass || !newPass) { toast.error("Both fields required"); return; }
        setChangingPass(true);
        try {
            await apiClient.changePassword(oldPass, newPass);
            toast.success("Password changed!");
            setOldPass("");
            setNewPass("");
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to change password");
        }
        setChangingPass(false);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-foreground">Settings</h1>
                <p className="text-muted-foreground mt-1">Manage your account and preferences</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-border/50 pb-1">
                {TABS.map((t) => (
                    <button
                        key={t.key}
                        onClick={() => setActiveTab(t.key)}
                        className={`flex items-center gap-2 px-4 py-2.5 rounded-t-lg text-sm font-medium transition-all
              ${activeTab === t.key
                                ? "bg-card border border-border/50 border-b-0 text-foreground -mb-px"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        <t.icon className="w-4 h-4" /> {t.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="border border-border/50 rounded-xl p-6 bg-card/50 backdrop-blur-sm"
            >
                {/* ── Profile ── */}
                {activeTab === "profile" && (
                    <div className="space-y-4 max-w-md">
                        <h2 className="text-xl font-semibold text-foreground">Profile Information</h2>
                        <div className="space-y-2">
                            <Label>Email</Label>
                            <Input value={user?.email || ""} disabled className="h-11 bg-secondary/50" />
                            <p className="text-xs text-muted-foreground">Email cannot be changed.</p>
                        </div>
                        <div className="space-y-2">
                            <Label>Account ID</Label>
                            <Input value={user?.id || ""} disabled className="h-11 bg-secondary/50 font-mono text-xs" />
                        </div>
                    </div>
                )}

                {/* ── Security ── */}
                {activeTab === "security" && (
                    <div className="space-y-4 max-w-md">
                        <h2 className="text-xl font-semibold text-foreground">Change Password</h2>
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
                        <h2 className="text-xl font-semibold text-foreground">Email Notifications</h2>
                        {loadingPrefs ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                            </div>
                        ) : (
                            <>
                                <Toggle
                                    checked={prefs.notify_on_new_jobs}
                                    onChange={(v) => setPrefs({ ...prefs, notify_on_new_jobs: v })}
                                    label="New Job Alerts"
                                    desc="Get notified when new jobs matching your profile are posted"
                                />
                                <Toggle
                                    checked={prefs.notify_on_resume_upload}
                                    onChange={(v) => setPrefs({ ...prefs, notify_on_resume_upload: v })}
                                    label="Resume Upload Confirmation"
                                    desc="Receive confirmation when a resume is uploaded"
                                />
                                <Toggle
                                    checked={prefs.notify_on_password_change}
                                    onChange={(v) => setPrefs({ ...prefs, notify_on_password_change: v })}
                                    label="Security Alerts"
                                    desc="Get notified when your password is changed"
                                />
                                <Toggle
                                    checked={prefs.weekly_digest}
                                    onChange={(v) => setPrefs({ ...prefs, weekly_digest: v })}
                                    label="Weekly Digest"
                                    desc="Receive a weekly summary of top matched jobs"
                                />

                                {/* Frequency Selector */}
                                <div className="pt-2">
                                    <Label className="text-sm">Email Frequency</Label>
                                    <div className="flex gap-2 mt-2">
                                        {(["daily", "weekly", "never"] as const).map((f) => (
                                            <button
                                                key={f}
                                                onClick={() => setPrefs({ ...prefs, email_frequency: f })}
                                                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all
                          ${prefs.email_frequency === f
                                                        ? "bg-primary text-primary-foreground"
                                                        : "bg-secondary/50 text-muted-foreground hover:bg-secondary"
                                                    }`}
                                            >
                                                {f}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <Button onClick={savePrefs} disabled={savingPrefs} className="mt-4 gap-2">
                                    {savingPrefs ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Save Preferences
                                </Button>
                            </>
                        )}
                    </div>
                )}
            </motion.div>
        </div>
    );
}

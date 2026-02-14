"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Eye, EyeOff, Sparkles, Loader2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import toast from "react-hot-toast";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email || !password) { toast.error("Email and password required"); return; }
        setLoading(true);
        try {
            await apiClient.login(email, password);
            toast.success("Welcome back!");
            router.push("/dashboard");
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            toast.error(typeof detail === "string" ? detail : "Login failed");
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen flex bg-background">
            {/* Left — Branding */}
            <div className="hidden lg:flex lg:w-1/2 relative bg-gradient-to-br from-violet-600/20 via-primary/10 to-background items-center justify-center p-12">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,_var(--tw-gradient-stops))] from-violet-600/20 via-transparent to-transparent" />
                <div className="relative z-10 max-w-md">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground"><Sparkles className="w-7 h-7" /></div>
                        <span className="text-3xl font-bold text-foreground">AutoIntern</span>
                    </div>
                    <h2 className="text-4xl font-bold text-foreground leading-tight mb-4">Start Your Career Journey</h2>
                    <p className="text-lg text-muted-foreground">AI‑powered job matching, resume analysis, and career coaching — all in one place.</p>
                </div>
            </div>

            {/* Right — Form */}
            <div className="flex-1 flex items-center justify-center p-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md space-y-8">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">Welcome back</h1>
                        <p className="text-muted-foreground mt-2">Sign in to continue your journey.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="space-y-2">
                            <Label>Email</Label>
                            <Input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="h-11 bg-secondary/50" />
                        </div>
                        <div className="space-y-2">
                            <Label>Password</Label>
                            <div className="relative">
                                <Input id="login-password" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="h-11 bg-secondary/50 pr-10" />
                                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>
                        <Button id="login-submit" type="submit" className="w-full h-11" disabled={loading}>
                            {loading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Signing in…</> : <>Sign In <ArrowRight className="w-4 h-4 ml-2" /></>}
                        </Button>
                    </form>

                    <p className="text-center text-sm text-muted-foreground">
                        Don&apos;t have an account?{" "}
                        <Link href="/register" className="text-primary hover:underline font-medium">Create one</Link>
                    </p>
                </motion.div>
            </div>
        </div>
    );
}

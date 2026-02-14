"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, FileText, Briefcase, Bot, BarChart3, Shield, Zap, ArrowRight, Check, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/stores/auth-store";

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

const features = [
    { icon: FileText, title: "AI Resume Analyzer", desc: "Get instant ATS score and actionable feedback." },
    { icon: Briefcase, title: "Smart Job Matching", desc: "AI-matched jobs tailored to your profile and skills." },
    { icon: BarChart3, title: "Application Tracker", desc: "Kanban board to manage all your applications." },
    { icon: Bot, title: "AI Career Coach", desc: "24/7 career advice powered by AI." },
    { icon: Shield, title: "Secure & Private", desc: "Your data is encrypted and never shared." },
    { icon: Zap, title: "Lightning Fast", desc: "Optimized performance for instant results." },
];

const plans = [
    { name: "Free", price: "$0", period: "/forever", features: ["5 job searches/day", "1 resume upload", "Basic AI tips", "Application tracker"], cta: "Get Started", popular: false },
    { name: "Pro", price: "$9", period: "/month", features: ["Unlimited searches", "Unlimited resumes", "Advanced AI coaching", "Priority support", "Export reports"], cta: "Start Free Trial", popular: true },
    { name: "Team", price: "$29", period: "/month", features: ["Everything in Pro", "5 team members", "Shared dashboard", "Analytics", "API access"], cta: "Contact Sales", popular: false },
];

export default function LandingPage() {
    const router = useRouter();
    const accessToken = useAuthStore((s) => s.accessToken);

    useEffect(() => {
        if (accessToken) {
            router.replace("/dashboard");
        }
    }, [accessToken, router]);

    return (
        <div className="min-h-screen bg-background text-foreground">
            {/* Nav */}
            <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-border">
                <div className="max-w-7xl mx-auto flex items-center justify-between h-16 px-6">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
                            <Sparkles className="w-5 h-5" />
                        </div>
                        <span className="text-xl font-bold">AutoIntern</span>
                    </Link>
                    <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
                        <a href="#features" className="hover:text-foreground transition-colors">Features</a>
                        <a href="#pricing" className="hover:text-foreground transition-colors">Pricing</a>
                    </div>
                    <div className="flex items-center gap-3">
                        <Link href="/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
                        <Link href="/register"><Button size="sm">Get Started</Button></Link>
                    </div>
                </div>
            </nav>

            {/* Hero */}
            <section className="relative pt-32 pb-24 overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-violet-600/15 via-transparent to-transparent" />
                <div className="absolute top-20 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[150px]" />
                <div className="absolute bottom-20 right-1/4 w-72 h-72 bg-indigo-500/15 rounded-full blur-[120px]" />

                <motion.div variants={container} initial="hidden" animate="show" className="relative z-10 max-w-4xl mx-auto text-center px-6">
                    <motion.div variants={item}>
                        <Badge variant="outline" className="mb-6 border-primary/30 text-primary px-4 py-1.5">
                            <Star className="w-3 h-3 mr-1.5 fill-current" /> AI-Powered Career Platform
                        </Badge>
                    </motion.div>

                    <motion.h1 variants={item} className="text-5xl md:text-7xl font-bold leading-tight mb-6">
                        Land Your Dream{" "}
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-violet-400 via-purple-400 to-indigo-400">
                            Internship
                        </span>
                        <br />with AI
                    </motion.h1>

                    <motion.p variants={item} className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
                        Optimize your resume, discover matched opportunities, and track applications — all powered by intelligent automation.
                    </motion.p>

                    <motion.div variants={item} className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link href="/register">
                            <Button size="lg" className="text-base h-12 px-8">
                                Start Free <ArrowRight className="w-4 h-4 ml-2" />
                            </Button>
                        </Link>
                        <a href="#features">
                            <Button variant="outline" size="lg" className="text-base h-12 px-8">
                                See Features
                            </Button>
                        </a>
                    </motion.div>
                </motion.div>
            </section>

            {/* Features */}
            <section id="features" className="py-24 px-6">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <Badge variant="outline" className="mb-4 border-primary/30 text-primary">Features</Badge>
                        <h2 className="text-4xl font-bold mb-4">Everything you need to succeed</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">Powerful tools designed to give you an unfair advantage in your job search.</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {features.map((f, i) => (
                            <motion.div key={f.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}>
                                <Card className="glass-card h-full group hover:border-primary/30">
                                    <CardContent className="p-6">
                                        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:bg-primary/20 transition-colors">
                                            <f.icon className="w-6 h-6" />
                                        </div>
                                        <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
                                        <p className="text-muted-foreground text-sm">{f.desc}</p>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Pricing */}
            <section id="pricing" className="py-24 px-6 bg-secondary/20">
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-16">
                        <Badge variant="outline" className="mb-4 border-primary/30 text-primary">Pricing</Badge>
                        <h2 className="text-4xl font-bold mb-4">Simple, transparent pricing</h2>
                        <p className="text-muted-foreground text-lg">Start free. Upgrade when you need more.</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {plans.map((p, i) => (
                            <motion.div key={p.name} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}>
                                <Card className={`h-full ${p.popular ? "border-primary/50 bg-primary/5 shadow-lg shadow-primary/10" : "glass-card"}`}>
                                    <CardContent className="p-6 flex flex-col h-full">
                                        {p.popular && <Badge className="w-fit mb-4">Most Popular</Badge>}
                                        <h3 className="text-xl font-bold">{p.name}</h3>
                                        <div className="mt-4 mb-6">
                                            <span className="text-4xl font-bold">{p.price}</span>
                                            <span className="text-muted-foreground">{p.period}</span>
                                        </div>
                                        <ul className="space-y-3 flex-1">
                                            {p.features.map((f) => (
                                                <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
                                                    <Check className="w-4 h-4 text-primary shrink-0" /> {f}
                                                </li>
                                            ))}
                                        </ul>
                                        <Link href="/register" className="mt-6">
                                            <Button className="w-full" variant={p.popular ? "default" : "outline"}>{p.cta}</Button>
                                        </Link>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-border py-12 px-6">
                <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-primary-foreground"><Sparkles className="w-4 h-4" /></div>
                        <span className="font-bold">AutoIntern</span>
                    </div>
                    <p className="text-sm text-muted-foreground">&copy; {new Date().getFullYear()} AutoIntern. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
}

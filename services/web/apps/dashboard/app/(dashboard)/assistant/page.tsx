"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Loader2, Sparkles, Lightbulb, MoreVertical, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import type { ChatMessage } from "@/types";

const suggestions = [
    "How do I prepare for a tech interview?",
    "What skills should I highlight for a data science role?",
    "Tips for writing a cover letter",
    "How to negotiate an internship offer?",
    "Help me improve my resume summary",
    "What projects should I build for a software role?",
    "How do I network on LinkedIn effectively?",
    "Create a 2‑week study plan for SQL",
];

export default function AssistantPage() {
    const { user } = useAuthStore();
    const [messages, setMessages] = useState<ChatMessage[]>([
        { id: "1", text: `Hi ${user?.email?.split("@")[0] || "there"}! 👋 I'm your AI career assistant. Ask me anything about job hunting, interviews, resumes, or career growth.`, sender: "bot", timestamp: new Date() },
    ]);
    const [input, setInput] = useState("");
    const [typing, setTyping] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages, typing]);

    const sendMessage = async (text?: string) => {
        const msg = text || input.trim();
        if (!msg) return;

        const userMsg: ChatMessage = { id: Date.now().toString(), text: msg, sender: "user", timestamp: new Date() };
        setMessages((p) => [...p, userMsg]);
        setInput("");
        setTyping(true);

        await new Promise((r) => setTimeout(r, 1200 + Math.random() * 800));

        const responses: Array<{ keywords: string[]; reply: string }> = [
            {
                keywords: ["interview", "behavioral", "technical", "leetcode", "coding"],
                reply: "Great question! Here are my top interview tips:\n\n• **Research the company** thoroughly\n• Practice STAR method for behavioral questions\n• Prepare 2-3 questions to ask them\n• Do mock interviews with peers\n• Review common coding patterns for tech roles",
            },
            {
                keywords: ["resume", "cv", "ats", "bullet", "summary"],
                reply: "Key resume tips for ATS optimization:\n\n• Use standard section headings\n• Include quantifiable achievements (increased X by Y%)\n• Mirror keywords from the job description\n• Keep it to 1 page for internships\n• Use our **Resume Analyzer** for AI feedback!",
            },
            {
                keywords: ["cover", "letter", "motivation"],
                reply: "Cover letter best practices:\n\n• Address the hiring manager by name\n• Open with a compelling hook\n• Show you understand the company's mission\n• Connect your experience to their needs\n• End with a clear call to action",
            },
            {
                keywords: ["negotiate", "offer", "salary", "comp", "stipend"],
                reply: "Negotiation tips for internships:\n\n• Research market rates on Glassdoor/Levels.fyi\n• Frame it as exploring options, not demanding\n• Consider the full package (stipend, housing, perks)\n• Practice your pitch beforehand\n• Be gracious regardless of outcome",
            },
            {
                keywords: ["portfolio", "project", "build", "github"],
                reply: "Project ideas that stand out:\n\n• Build a real‑world CRUD app with auth + deployments\n• Add one data/ML project with a clear problem + metrics\n• Write a clean README with screenshots + architecture\n• Include tests and CI for credibility",
            },
            {
                keywords: ["linkedin", "network", "referral"],
                reply: "Networking on LinkedIn:\n\n• Optimize your headline with your target role\n• Post 1–2 times/week sharing projects or learnings\n• Send short, specific connection requests\n• Ask for advice, not a job (it works better)",
            },
            {
                keywords: ["study plan", "plan", "learning", "roadmap"],
                reply: "Here’s a simple 2‑week plan template:\n\n• Week 1: Fundamentals + daily practice (30–60 min)\n• Week 2: Projects + review weak areas\n• End each day with 3 key takeaways\n\nTell me the topic and your current level, and I’ll tailor it.",
            },
            {
                keywords: ["email", "cold", "message", "reach"],
                reply: "Cold outreach template:\n\nHi [Name],\nI’m a [role/student] interested in [team/area]. I built [project] and would love feedback or advice on breaking into [role]. If you have 10 minutes, I’d appreciate it.\n\nThanks!",
            },
            {
                keywords: ["internship", "apply", "application", "track"],
                reply: "Application strategy:\n\n• Apply early (first 7–10 days)\n• Tailor resume to each role\n• Track outcomes in a simple spreadsheet\n• Follow up after 7–10 days",
            },
            {
                keywords: ["career", "switch", "growth", "promotion"],
                reply: "Career growth basics:\n\n• Build a strong portfolio of outcomes\n• Ask for feedback regularly\n• Find a mentor and learn from peers\n• Invest in one high‑leverage skill at a time",
            },
            {
                keywords: ["productivity", "time management", "focus"],
                reply: "Productivity basics:\n\n• Time‑block your day\n• Use a simple 3‑task priority list\n• Batch similar work together\n• Review each day for small improvements",
            },
            {
                keywords: ["sql", "database", "query"],
                reply: "SQL fast‑start:\n\n• Learn SELECT, WHERE, JOIN, GROUP BY\n• Practice on LeetCode/Mode\n• Build a small project with real data\n• Add query explanations to your notes",
            },
        ];

        const lower = msg.toLowerCase();
        const matched = responses.find((r) => r.keywords.some((k) => lower.includes(k)));
        const botReply: ChatMessage = {
            id: (Date.now() + 1).toString(),
            text: matched ? matched.reply : "Thanks for asking! I can help with career topics or general questions.\n\nIf you want tailored advice, share a bit more context (role, timeline, goals).",
            sender: "bot",
            timestamp: new Date(),
        };

        setTyping(false);
        setMessages((p) => [...p, botReply]);
    };

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col max-w-3xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-3 pb-4 border-b border-border mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-violet-500/20">
                    <Sparkles className="w-5 h-5" />
                </div>
                <div>
                    <h2 className="font-bold text-foreground">AI Career Assistant</h2>
                    <p className="text-xs text-emerald-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Online</p>
                </div>
                <Button variant="ghost" size="icon" className="ml-auto text-muted-foreground"><MoreVertical className="w-5 h-5" /></Button>
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 px-1">
                <AnimatePresence initial={false}>
                    {messages.map((msg) => (
                        <motion.div key={msg.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={cn("flex gap-3 max-w-[85%]", msg.sender === "user" ? "ml-auto flex-row-reverse" : "")}>
                            <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center text-white shrink-0",
                                msg.sender === "user" ? "bg-gradient-to-br from-indigo-500 to-purple-600" : "bg-gradient-to-br from-violet-500 to-indigo-600"
                            )}>
                                {msg.sender === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                            </div>
                            <div className={cn("rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
                                msg.sender === "user" ? "bg-primary text-primary-foreground rounded-tr-md" : "glass-card rounded-tl-md text-foreground"
                            )}>
                                {msg.text}
                                <div className={cn("text-[10px] mt-1.5 opacity-50", msg.sender === "user" ? "text-right" : "")}>
                                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {typing && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white shrink-0">
                            <Bot className="w-4 h-4" />
                        </div>
                        <div className="glass-card rounded-2xl rounded-tl-md px-4 py-3">
                            <div className="flex gap-1.5">
                                {[0, 1, 2].map((i) => (
                                    <motion.div key={i} className="w-2 h-2 bg-muted-foreground rounded-full" animate={{ y: [0, -6, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }} />
                                ))}
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Suggestions */}
                {messages.length <= 1 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-4">
                        {suggestions.map((s) => (
                            <button
                                key={s}
                                onClick={() => sendMessage(s)}
                                className="text-left p-3 rounded-xl border border-border text-sm text-muted-foreground hover:text-foreground hover:border-primary/50 hover:bg-primary/5 transition-all flex items-center gap-2"
                            >
                                <Lightbulb className="w-4 h-4 text-primary shrink-0" />
                                <span>{s}</span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="pt-4 border-t border-border mt-auto">
                <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="flex gap-2">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask me anything about your career…"
                        className="flex-1 h-11 px-4 rounded-xl bg-secondary/50 border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                    <Button type="submit" size="icon" className="h-11 w-11 rounded-xl" disabled={!input.trim() || typing}>
                        <Send className="w-4 h-4" />
                    </Button>
                </form>
            </div>
        </div>
    );
}

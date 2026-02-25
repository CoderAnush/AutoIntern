"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
    LayoutDashboard, Briefcase, FileText, Kanban,
    MessageSquare, Settings, LogOut, Menu, X,
    Bell, Search, Sparkles, BarChart3, Bookmark,
    Mail, GraduationCap, Sun, Moon,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { apiClient } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTheme } from "next-themes";

const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/jobs", label: "Find Jobs", icon: Briefcase },
    { path: "/saved-jobs", label: "Saved Jobs", icon: Bookmark },
    { path: "/analyzer", label: "Resume Analyzer", icon: FileText },
    { path: "/applications", label: "Applications", icon: Kanban },
    { path: "/cover-letter", label: "Cover Letter", icon: Mail },
    { path: "/interview-prep", label: "Interview Prep", icon: GraduationCap },
    { path: "/analytics", label: "Analytics", icon: BarChart3 },
    { path: "/assistant", label: "AI Assistant", icon: MessageSquare },
    { path: "/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, isAuthenticated, accessToken, setUser, clearAuth } = useAuthStore();
    const router = useRouter();
    const pathname = usePathname();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);
    const { theme, setTheme } = useTheme();

    useEffect(() => {
        const init = async () => {
            if (!accessToken) { router.replace("/login"); return; }
            if (!user) {
                try { await apiClient.getCurrentUser(); } catch { clearAuth(); router.replace("/login"); return; }
            }
            setIsInitialized(true);
        };
        init();
    }, [accessToken, user, router, clearAuth, setUser]);

    if (!isInitialized) {
        return (
            <div className="flex items-center justify-center h-screen bg-background">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
            </div>
        );
    }

    const handleLogout = async () => {
        try { await apiClient.logout(); } catch { } finally { clearAuth(); router.push("/login"); }
    };

    return (
        <div className="min-h-screen flex bg-background text-foreground overflow-hidden">
            {/* Sidebar */}
            <aside className={cn(
                "fixed inset-y-0 left-0 z-50 w-64 bg-sidebar border-r border-sidebar-border flex flex-col transform transition-transform duration-300 lg:relative lg:translate-x-0",
                sidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="h-16 flex items-center px-6 border-b border-sidebar-border">
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
                            <Sparkles className="w-5 h-5" />
                        </div>
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">AutoIntern</span>
                    </Link>
                    <button className="ml-auto lg:hidden text-muted-foreground hover:text-foreground" onClick={() => setSidebarOpen(false)}>
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const isActive = pathname === item.path || (item.path !== "/dashboard" && pathname.startsWith(item.path));
                        const Icon = item.icon;
                        return (
                            <Link
                                key={item.path}
                                href={item.path}
                                onClick={() => setSidebarOpen(false)}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group relative overflow-hidden",
                                    isActive ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50"
                                )}
                            >
                                <Icon className={cn("w-5 h-5", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
                                <span>{item.label}</span>
                                {isActive && <div className="absolute right-2 w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(124,58,237,0.8)]" />}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-sidebar-border">
                    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-sidebar-accent/50 transition-colors group">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-medium border border-white/10 shadow-lg shadow-indigo-500/20">
                            {user?.email?.charAt(0)?.toUpperCase() || "U"}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-foreground truncate">{user?.email?.split("@")[0] || "User"}</p>
                            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                        </div>
                        <button onClick={handleLogout} className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors opacity-0 group-hover:opacity-100" title="Logout">
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-16 border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-40 flex items-center justify-between px-4 lg:px-8">
                    <div className="flex items-center gap-4">
                        <button className="lg:hidden p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg" onClick={() => setSidebarOpen(true)}>
                            <Menu className="w-6 h-6" />
                        </button>
                        <h1 className="text-lg font-semibold text-foreground hidden md:block">
                            {navItems.find((i) => pathname === i.path || (i.path !== "/dashboard" && pathname.startsWith(i.path)))?.label || "Dashboard"}
                        </h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="relative hidden md:block">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input type="text" placeholder="Search..." className="h-9 w-64 bg-secondary/50 rounded-full pl-9 pr-4" />
                        </div>
                        {/* Theme toggle */}
                        <button
                            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                            className="p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-full transition-colors"
                            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                        >
                            {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>
                        <button className="relative p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-full transition-colors">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full border-2 border-background" />
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto p-4 lg:p-8">
                    <div className="max-w-7xl mx-auto">{children}</div>
                </main>
            </div>

            {sidebarOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
            )}
        </div>
    );
}

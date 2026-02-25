"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { ThemeProvider } from "next-themes";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: { staleTime: 60 * 1000, refetchOnWindowFocus: false },
                },
            })
    );

    return (
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
            <QueryClientProvider client={queryClient}>
                {children}
                <Toaster
                    position="top-right"
                    toastOptions={{
                        style: {
                            background: "hsl(var(--card))",
                            color: "hsl(var(--foreground))",
                            border: "1px solid hsl(var(--border))",
                        },
                    }}
                />
            </QueryClientProvider>
        </ThemeProvider>
    );
}

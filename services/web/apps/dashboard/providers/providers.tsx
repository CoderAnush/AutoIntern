"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
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
        <QueryClientProvider client={queryClient}>
            {children}
            <Toaster
                position="top-right"
                toastOptions={{
                    style: {
                        background: "hsl(240 10% 3.9%)",
                        color: "hsl(0 0% 98%)",
                        border: "1px solid hsl(240 3.7% 15.9%)",
                    },
                }}
            />
        </QueryClientProvider>
    );
}

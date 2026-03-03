import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/providers/providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const viewport: Viewport = {
    themeColor: "#7c3aed",
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
};

export const metadata: Metadata = {
    title: "AutoIntern — AI Co-pilot for Career Growth",
    description: "Find internships, optimize your resume, and track applications with AI-powered tools.",
    keywords: ["internship", "jobs", "AI", "resume", "career"],
    manifest: "/manifest.json",
    appleWebApp: {
        capable: true,
        statusBarStyle: "black-translucent",
        title: "AutoIntern",
        startupImage: "/icons/icon-512x512.png",
    },
    icons: {
        icon: "/icons/icon-192x192.png",
        apple: "/icons/apple-touch-icon.png",
    },
    openGraph: {
        title: "AutoIntern — AI Co-pilot for Career Growth",
        description: "Find internships, optimize your resume, and track applications with AI.",
        type: "website",
    },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={`${inter.variable} font-sans`}>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/providers/providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
    title: "AutoIntern — AI Co-pilot for Career Growth",
    description: "Find internships, optimize your resume, and track applications with AI-powered tools.",
    keywords: ["internship", "jobs", "AI", "resume", "career"],
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

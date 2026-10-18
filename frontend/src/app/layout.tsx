import type { Metadata, Viewport } from "next";
import { Manrope, Newsreader } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@descope/nextjs-sdk";
import { cn } from "@/lib/utils";

const sans = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
});

const heading = Newsreader({
  subsets: ["latin"],
  variable: "--font-heading",
});

export const metadata: Metadata = {
  title: "Concierge — Meeting Assistant",
  description: "Your private calendar concierge: schedule, reschedule and brief your day.",
};

export const viewport: Viewport = {
  themeColor: "#f8f4e7",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  const projectId = process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID ?? "";

  const cookieOptions = {
    sameSite: "Lax" as const,
    secure: process.env.NODE_ENV !== "development",
  };

  return (
    <AuthProvider
      projectId={projectId}
      sessionTokenViaCookie={cookieOptions}
      refreshTokenViaCookie={cookieOptions}
    >
      <html lang="en" className={cn(sans.variable, heading.variable)}>
        <body className="min-h-svh bg-background font-sans text-foreground antialiased">
          {children}
        </body>
      </html>
    </AuthProvider>
  );
}

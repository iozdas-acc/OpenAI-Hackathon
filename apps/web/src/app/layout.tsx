import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Oracle to Supabase Migration Review Workspace",
  description:
    "Production-style migration review workspace with human checkpoint controls, graph evidence, and persistent Codex side panel.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}

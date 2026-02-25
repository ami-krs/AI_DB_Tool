import type { Metadata } from "next";
import "./globals.css";
import { AuthGuard } from "@/components/AuthGuard";
import { Nav } from "@/components/Nav";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "AI Database Copilot",
  description: "AI-powered database management and SQL assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <Providers>
          <Nav />
          <main className="container mx-auto px-4 py-6">
            <AuthGuard>{children}</AuthGuard>
          </main>
        </Providers>
      </body>
    </html>
  );
}

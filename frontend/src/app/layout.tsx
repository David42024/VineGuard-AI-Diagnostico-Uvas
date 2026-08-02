import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { StoreHydrator } from "@/components/store-hydrator";
import { Toaster } from "@/components/ui/toast";
import { Chatbot } from "@/components/Chatbot/Chatbot";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VineGuard AI - Diagnóstico Inteligente de Cultivos de Vid",
  description:
    "Plataforma de diagnóstico inteligente para la protección temprana de cultivos de vid usando inteligencia artificial.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <StoreHydrator />
          <Toaster />
          <Chatbot />
        </ThemeProvider>
      </body>
    </html>
  );
}

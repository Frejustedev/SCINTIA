import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";

// Display, UI and data fonts (charte §4). All open-source.
const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});
const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Scintia — Aide à la décision en médecine nucléaire",
  description:
    "Analyse SPECT/CT : segmentation, quantification, dosimétrie et brouillon de " +
    "compte-rendu — toujours relu et validé par le médecin. Prototype de recherche.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // lang=fr / dir=ltr by default. Arabic (RTL) toggles `dir` in a later phase.
  return (
    <html
      lang="fr"
      dir="ltr"
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
    >
      <body className="min-h-screen bg-bg font-sans text-text antialiased">
        {children}
      </body>
    </html>
  );
}

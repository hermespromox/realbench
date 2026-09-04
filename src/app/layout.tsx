import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://realbench.vercel.app"),
  title: "RealBench — Frontend Capability Benchmark",
  description: "Compare one-shot animated frontend builds from frontier AI models. Same prompt, no repair, rendered side by side.",
  openGraph: {
    title: "RealBench — See what models can actually build",
    description: "A visual one-shot frontend benchmark for frontier AI models.",
    type: "website",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}><body>{children}</body></html>;
}

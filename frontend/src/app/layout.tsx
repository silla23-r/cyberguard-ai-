import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CyberGuard AI — Multimodal Fraud & Scam Defense",
  description: "Real-time AI verification against Digital Arrest, UPI scams, and phishing intimidation.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "CyberGuard",
  },
  icons: {
    icon: "https://cdn-icons-png.flaticon.com/512/1067/1067256.png",
    apple: "https://cdn-icons-png.flaticon.com/512/1067/1067256.png",
  },
};

export const viewport = {
  themeColor: "#ffffff",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-zinc-50 text-zinc-900 min-h-screen antialiased selection:bg-zinc-900 selection:text-white">
        {children}
      </body>
    </html>
  );
}

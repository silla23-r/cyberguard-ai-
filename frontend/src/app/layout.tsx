import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CyberGuard AI — Multimodal Fraud & Scam Defense Agent",
  description: "Real-time AI protection against Digital Arrest, UPI scams, and phishing intimidation.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "CyberGuard",
  },
  icons: {
    icon: "https://cdn-icons-png.flaticon.com/512/1067/1067256.png",
    apple: "https://cdn-icons-png.flaticon.com/512/1067/1067256.png",
  },
};

export const viewport = {
  themeColor: "#0B1120",
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
    <html lang="en" className="dark">
      <body className="bg-guard-900 text-slate-100 min-h-screen antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}

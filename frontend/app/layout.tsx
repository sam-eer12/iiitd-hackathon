import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: {
    default: "TenderLens — Find the tender worth your time",
    template: "%s · TenderLens",
  },
  description:
    "A clearer view of your next opportunity. Discover relevant tenders, check your readiness, and keep every amendment in sight.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

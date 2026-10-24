import type { Metadata } from "next";

export const metadata: Metadata = { title: "Amendments" };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

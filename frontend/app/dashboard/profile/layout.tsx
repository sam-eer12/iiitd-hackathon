import type { Metadata } from "next";

export const metadata: Metadata = { title: "Supplier profile" };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

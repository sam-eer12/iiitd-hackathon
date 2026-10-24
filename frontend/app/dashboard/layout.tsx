import type { Metadata } from "next";
import { WorkspaceProvider } from "@/components/workspace-provider";
import { DashboardShell } from "@/components/dashboard-shell";

// Nested dashboard pages keep the site-wide " · TenderLens" suffix.
export const metadata: Metadata = {
  title: { default: "Workspace", template: "%s · TenderLens" },
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WorkspaceProvider>
      <DashboardShell>{children}</DashboardShell>
    </WorkspaceProvider>
  );
}

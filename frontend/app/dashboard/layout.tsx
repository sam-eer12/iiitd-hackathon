import type { Metadata } from "next";
import { WorkspaceProvider } from "@/components/workspace-provider";
import { DashboardShell } from "@/components/dashboard-shell";

export const metadata: Metadata = { title: "Workspace" };

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

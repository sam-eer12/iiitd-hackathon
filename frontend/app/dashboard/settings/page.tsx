"use client";

import Link from "next/link";
import { Icon } from "@/components/icon";
import { AuthProfile } from "@/components/auth-profile";
import { useWorkspace } from "@/components/workspace-provider";
import { useAuth } from "@/lib/auth-context";

export default function SettingsPage() {
  const { collapsed, toggleSidebar } = useWorkspace();
  const { user, loading } = useAuth();
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">MAKE YOURSELF AT HOME</div>
          <h1>Your workspace, your way.</h1>
          <p>Manage your local workspace preferences and discovery setup.</p>
        </div>
      </div>
      <section className="settings-panel">
        <div className="settings-row">
          <div>
            <h2>Account</h2>
            <p>
              {loading
                ? "Checking your sign-in status…"
                : user
                  ? `Signed in as ${user.email ?? user.displayName ?? "your Google account"}. Your supplier profile and bookmarks are stored in this browser.`
                  : "Sign in with Google to identify this workspace. Your supplier profile and bookmarks are stored in this browser either way."}
            </p>
          </div>
          <AuthProfile />
        </div>
        <div className="settings-row">
          <div>
            <h2>Navigation sidebar</h2>
            <p>
              Keep the sidebar open for labels, or collapse it to give your
              workspace more room. Your preference is saved in this browser.
            </p>
          </div>
          <button
            className="button button-secondary button-small"
            onClick={toggleSidebar}
          >
            <Icon name="panel" size={15} />
            {collapsed ? "Expand sidebar" : "Collapse sidebar"}
          </button>
        </div>
        <div className="settings-row">
          <div>
            <h2>Live discovery</h2>
            <p>
              Configure the server-side TinyFish integration and inspect your
              latest source run.
            </p>
          </div>
          <Link
            className="button button-secondary button-small"
            href="/dashboard/sources"
          >
            Manage source <Icon name="arrowRight" size={15} />
          </Link>
        </div>
      </section>
    </>
  );
}

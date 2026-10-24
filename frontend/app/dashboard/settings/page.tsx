"use client";

import { useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icon";
import { useWorkspace } from "@/components/workspace-provider";

export default function SettingsPage() {
  const { collapsed, toggleSidebar, clearLiveResults, job } = useWorkspace();
  const [confirm, setConfirm] = useState(false);
  const running = !!job && ["running", "submitting"].includes(job.status);
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
            <h2>Navigation sidebar</h2>
            <p>
              Keep the sidebar open for labels, or collapse it to give your
              workspace more room. Your preference is saved in this browser.
            </p>
          </div>
          <button
            className="button button-outline button-small"
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
            className="button button-outline button-small"
            href="/dashboard/sources"
          >
            Manage source <Icon name="arrowRight" size={15} />
          </Link>
        </div>
        <div className="settings-row">
          <div>
            <h2>Return to the sample workspace</h2>
            <p>
              Clear this browser’s live results and display the illustrative
              sample notices. Your supplier profile and bookmarks stay saved.
              The server’s run history is retained.
            </p>
          </div>
          <button
            className="button button-outline button-small"
            disabled={running}
            onClick={() => {
              if (confirm) {
                clearLiveResults();
                setConfirm(false);
              } else setConfirm(true);
            }}
          >
            {confirm ? "Confirm sample view" : "Show sample data"}
          </button>
        </div>
      </section>
    </>
  );
}

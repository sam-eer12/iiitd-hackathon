"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Brand } from "./brand";
import { Icon, type IconName } from "./icon";
import { useWorkspace } from "./workspace-provider";
import { AuthProfile } from "./auth-profile";

const navigation: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard", label: "Overview", icon: "grid" },
  { href: "/dashboard/tenders", label: "Discover tenders", icon: "search" },
  { href: "/dashboard/saved", label: "Saved tenders", icon: "bookmark" },
  { href: "/dashboard/amendments", label: "Amendments", icon: "history" },
];
const workspaceNavigation: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard/profile", label: "Supplier profile", icon: "building" },
  { href: "/dashboard/sources", label: "Connected sources", icon: "globe" },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const {
    collapsed,
    toggleSidebar,
    profile,
    savedIds,
    job,
    tenders,
    collectionMode,
  } = useWorkspace();
  const [mobileOpen, setMobileOpen] = useState(false);
  const pageName =
    [...navigation, ...workspaceNavigation].find(
      (item) => item.href === pathname,
    )?.label ?? "Workspace";
  const initials = profile.company
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("");

  function navItem(item: (typeof navigation)[number]) {
    const active = pathname === item.href;
    return (
      <Link
        key={item.href}
        href={item.href}
        title={collapsed ? item.label : undefined}
        aria-current={active ? "page" : undefined}
        className={`sidebar-link ${active ? "active" : ""}`}
        onClick={() => setMobileOpen(false)}
      >
        <Icon name={item.icon} size={19} />
        <span className="sidebar-label">{item.label}</span>
        {item.label === "Saved tenders" && (
          <span className="nav-count">
            {tenders.filter((tender) => savedIds.includes(tender.id)).length}
          </span>
        )}
        {item.label === "Amendments" && (
          <span className="nav-count nav-count-green">
            {tenders.filter((tender) => tender.amended).length}
          </span>
        )}
      </Link>
    );
  }

  return (
    <div
      className={`dashboard-shell ${collapsed ? "sidebar-collapsed" : ""} ${mobileOpen ? "mobile-sidebar-open" : ""}`}
    >
      <a className="skip-link" href="#workspace-main">
        Skip to workspace
      </a>
      {mobileOpen && (
        <button
          className="sidebar-scrim"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside className="sidebar" aria-label="Workspace navigation">
        <div className="sidebar-brand">
          <Brand compact={collapsed} />
          <button
            className="icon-button sidebar-collapse"
            onClick={toggleSidebar}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
          >
            <Icon name="panel" size={18} />
          </button>
          <button
            className="icon-button mobile-close"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          >
            <Icon name="close" />
          </button>
        </div>
        <Link href="/dashboard/profile" className="workspace-switcher">
          <span className="workspace-avatar">{initials}</span>
          <span className="sidebar-label">
            <strong>{profile.company}</strong>
            <small>Supplier workspace</small>
          </span>
          <Icon name="chevronDown" size={15} />
        </Link>
        <div className="sidebar-group-label">WORKSPACE</div>
        <nav>{navigation.map(navItem)}</nav>
        <div className="sidebar-group-label sidebar-group-second">
          YOUR BUSINESS
        </div>
        <nav>{workspaceNavigation.map(navItem)}</nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="note-icon">
              <Icon name="leaf" size={22} />
            </span>
            <strong>
              A little preparation.
              <br />A better opportunity.
            </strong>
            <p>
              Keep your supplier profile up to date for a clearer shortlist.
            </p>
            <Link href="/dashboard/profile">
              Review your profile <Icon name="arrowRight" size={15} />
            </Link>
          </div>
          <Link href="/architecture" className="sidebar-link">
            <Icon name="code" size={18} />
            <span className="sidebar-label">Project architecture</span>
            <Icon name="arrow" size={13} />
          </Link>
          <Link href="/dashboard/help" className="sidebar-link">
            <Icon name="help" size={18} />
            <span className="sidebar-label">Help & getting started</span>
          </Link>
          <div className="sidebar-user">
            <span className="user-avatar">
              {profile.contact
                .split(" ")
                .map((word) => word[0])
                .slice(0, 2)
                .join("")}
            </span>
            <span className="sidebar-label">
              <strong>{profile.contact}</strong>
              <small>Workspace owner</small>
            </span>
            <Link
              href="/dashboard/settings"
              className="icon-button"
              aria-label="Workspace settings"
            >
              <Icon name="settings" size={17} />
            </Link>
          </div>
        </div>
      </aside>
      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="breadcrumbs">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMobileOpen(true)}
            >
              <Icon name="menu" />
            </button>
            <span>Workspace</span>
            <Icon name="chevron" size={13} />
            <strong>{pageName}</strong>
          </div>
          <div className="topbar-right">
            <span className="workspace-mode">
              <span className="live-dot" />
              {collectionMode === "live"
                ? "Live discovery"
                : "Sample workspace"}
            </span>
            <AuthProfile />
            <Link
              className="icon-button notification-button"
              href="/dashboard/amendments"
              aria-label="View amendments"
            >
              <Icon name="bell" size={19} />
              <i />
            </Link>
            <Link
              href="/dashboard/profile"
              className="topbar-avatar"
              aria-label="Open supplier profile"
            >
              {initials}
            </Link>
          </div>
        </header>
        {job && ["running", "submitting"].includes(job.status) && (
          <div className="running-banner" role="status">
            <Icon name="refresh" size={15} className="spin" /> TinyFish is
            reading the public source. Your current workspace stays available.
          </div>
        )}
        <main id="workspace-main" className="workspace-content">
          {children}
        </main>
        <footer className="workspace-footer">
          <span>
            <span className="live-dot" /> A clearer view. A more considered bid.
          </span>
          <span>TenderLens · Built with TinyFish</span>
        </footer>
      </div>
    </div>
  );
}

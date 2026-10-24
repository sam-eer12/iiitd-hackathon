"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AuthProfile } from "./auth-profile";
import { Brand } from "./brand";
import { Icon } from "./icon";

const links = [
  { href: "/#how-it-works", label: "How it works" },
  { href: "/#why-tenderlens", label: "Why TenderLens" },
  { href: "/dashboard/sources", label: "Our source" },
  { href: "/architecture", label: "Architecture" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        toggle.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const navLinks = links.map((link) => (
    <Link
      key={link.href}
      href={link.href}
      className="nav-pill-link"
      aria-current={pathname === link.href ? "page" : undefined}
      onClick={() => setOpen(false)}
    >
      {link.label}
    </Link>
  ));

  return (
    <header className="site-header">
      <div className="site-header-inner page-width">
        <Brand />
        <nav className="nav-pill" aria-label="Main navigation">
          {navLinks}
        </nav>
        <div className="site-header-actions">
          <span className="auth-slot">
            <AuthProfile />
          </span>
          <Link
            className="button button-primary button-small"
            href="/dashboard"
          >
            Open workspace <Icon name="arrowRight" size={15} />
          </Link>
          <button
            ref={toggle}
            type="button"
            className="icon-button site-menu-toggle"
            aria-expanded={open}
            aria-controls="site-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen(!open)}
          >
            <Icon name={open ? "close" : "menu"} size={19} />
          </button>
        </div>
      </div>
      <nav
        id="site-menu"
        className="site-menu"
        aria-label="Menu"
        hidden={!open}
      >
        {navLinks}
        <div className="site-menu-footer">
          <AuthProfile />
          <Link
            className="button button-primary"
            href="/dashboard"
            onClick={() => setOpen(false)}
          >
            Open workspace <Icon name="arrowRight" size={16} />
          </Link>
        </div>
      </nav>
    </header>
  );
}

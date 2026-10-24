"use client";

import { useEffect, useRef, useState } from "react";

export function ArchitectureDiagram({ diagram }: { diagram: string }) {
  const container = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let cancelled = false;
    async function render() {
      try {
        const { default: mermaid } = await import("mermaid");
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: "base",
          themeVariables: {
            fontFamily: "Arial, sans-serif",
            primaryColor: "#edf4e5",
            primaryTextColor: "#23452e",
            primaryBorderColor: "#9fb58b",
            lineColor: "#91a97b",
            clusterBkg: "#f9fbf5",
            clusterBorder: "#dce6ce",
            fontSize: "13px",
          },
          flowchart: {
            htmlLabels: false,
            curve: "basis",
            nodeSpacing: 35,
            rankSpacing: 55,
          },
        });
        const result = await mermaid.render(
          "tenderlens-system-diagram",
          diagram,
        );
        if (!cancelled && container.current)
          container.current.innerHTML = result.svg;
      } catch {
        if (!cancelled) setError(true);
      }
    }
    void render();
    return () => {
      cancelled = true;
    };
  }, [diagram]);
  return (
    <div
      className="architecture-render"
      ref={container}
      role="img"
      aria-label="TenderLens system architecture: landing page and dashboard connect through Next.js and the planned FastAPI API to TinyFish discovery, PDF evidence extraction, deterministic readiness checks, amendment tracking, and AWS storage."
    >
      {error ? (
        "The diagram could not render. The complete Mermaid source is available below."
      ) : (
        <span>Rendering the complete system architecture…</span>
      )}
    </div>
  );
}

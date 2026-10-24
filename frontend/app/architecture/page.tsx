import { SiteHeader } from "@/components/site-header";
import { Icon } from "@/components/icon";
import { ArchitectureDiagram } from "@/components/architecture-diagram";
import { ARCHITECTURE_DIAGRAM } from "@/lib/architecture";

export const metadata = { title: "Project architecture" };
export default function ArchitecturePage() {
  return (
    <div className="architecture-page">
      <SiteHeader />
      <main className="page-width">
        <div className="architecture-heading">
          <div className="eyebrow reveal">The whole picture</div>
          <h1 className="reveal reveal-1">
            From opportunity
            <br />
            to evidence. <span className="serif-accent">Connected.</span>
          </h1>
          <p className="reveal reveal-2">
            The complete TenderLens target architecture, generated with Mermaid
            Charts. The current build includes the landing page, interactive
            dashboard, browser-persisted sample workspace, deterministic sample
            checks, and a server-side TinyFish discovery adapter. FastAPI,
            document extraction, durable workers, PostgreSQL, and AWS deployment
            are planned.
          </p>
        </div>
        <div className="architecture-summary reveal reveal-3">
          {[
            {
              number: "01 / EXPERIENCE",
              title: "A focused workspace",
              text: "Landing page → dashboard → supplier profile, tenders, evidence, and changes.",
            },
            {
              number: "02 / DISCOVERY",
              title: "TinyFish, connected",
              text: "Read approved public pages, submit bounded runs, validate structured results, and preserve source links.",
            },
            {
              number: "03 / INTELLIGENCE",
              title: "Evidence before certainty",
              text: "Version PDFs, extract exact clauses, compare five readiness checks, and explain amendments.",
            },
            {
              number: "04 / INFRASTRUCTURE",
              title: "A planned AWS foundation",
              text: "Amplify, EC2, RDS PostgreSQL, private S3, Secrets Manager, and CloudWatch.",
            },
          ].map((layer) => (
            <section className="architecture-layer" key={layer.number}>
              <span>{layer.number}</span>
              <h2>{layer.title}</h2>
              <p>{layer.text}</p>
            </section>
          ))}
        </div>
        <p className="architecture-scroll-hint">
          <Icon name="arrowRight" size={14} /> Scroll sideways to see the full
          diagram.
        </p>
        <ArchitectureDiagram diagram={ARCHITECTURE_DIAGRAM} />
        <div className="architecture-caption">
          <span>
            Full target architecture · operational backend and AWS components
            are planned
          </span>
          <a href="/architecture.mmd" download className="text-link">
            <Icon name="download" size={15} />
            Download Mermaid source
          </a>
        </div>
        <details className="architecture-source">
          <summary>View the diagram source</summary>
          <pre className="architecture-code">{ARCHITECTURE_DIAGRAM}</pre>
        </details>
      </main>
    </div>
  );
}

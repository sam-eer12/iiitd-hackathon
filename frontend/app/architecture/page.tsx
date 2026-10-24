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
            to demo purchase. <span className="serif-accent">Connected.</span>
          </h1>
          <p className="reveal reveal-2">
            The simplified supplier journey: Google sign-in, a saved business
            profile, DigiLocker, TinyFish discovery, official document review
            and demo checkout. FastAPI saves account-owned demo orders and
            receipts in PostgreSQL. The existing identity and discovery
            integrations stay connected.
          </p>
        </div>
        <div className="architecture-summary reveal reveal-3">
          {[
            {
              number: "01 / EXPERIENCE",
              title: "A focused workspace",
              text: "Google sign-in → supplier profile → DigiLocker → discover and review tenders.",
            },
            {
              number: "02 / DISCOVERY",
              title: "TinyFish, connected",
              text: "Read approved public pages, submit bounded runs, validate structured results, and preserve source links.",
            },
            {
              number: "03 / CHECKOUT",
              title: "A clear demo purchase",
              text: "Review the source, acknowledge the demo, simulate payment and recover a receipt in My tenders.",
            },
            {
              number: "04 / PERSISTENCE",
              title: "Your supplier account",
              text: "Existing Firebase identity, FastAPI workspace isolation and durable PostgreSQL demo orders.",
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
            Simplified supplier workflow · simulated checkout with no real
            charge
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

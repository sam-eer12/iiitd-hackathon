import Link from "next/link";
import { Brand } from "@/components/brand";
import { Icon } from "@/components/icon";
import { HeroPreview } from "@/components/hero-preview";
import { SiteHeader } from "@/components/site-header";
import "./styles/background-grain.css";

export default function Home() {
  return (
    <div className="landing">
      <div className="background-grain" aria-hidden="true">
        <svg width="100%" height="100%" focusable="false">
          <filter id="landing-grain">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.92"
              numOctaves="3"
              stitchTiles="stitch"
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter="url(#landing-grain)" />
        </svg>
      </div>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <SiteHeader />
      <main id="main">
        <section className="hero page-width">
          <div className="hero-copy">
            <span className="hero-badge reveal">
              <span className="hero-badge-dot" aria-hidden="true" />
              Big opportunities. Small teams.
            </span>
            <h1 className="reveal reveal-1">
              Find the tender <br className="hero-break" />
              worth <span className="serif-accent">your time.</span>
            </h1>
            <p className="hero-lede reveal reveal-2">
              Sign in, find official tenders with TinyFish, review the documents
              and try a demo purchase. One clear supplier workflow.
            </p>
            <div className="hero-actions reveal reveal-3">
              <Link className="button button-primary" href="/dashboard">
                Find your next opportunity <Icon name="arrowRight" size={17} />
              </Link>
              <a className="button button-secondary" href="#how-it-works">
                See how it works
              </a>
            </div>
            <p className="hero-reassurance reveal reveal-4">
              <Icon name="shield" size={15} />
              Your decision. Supported by evidence.
            </p>
          </div>
          <HeroPreview />
        </section>

        <section
          className="principles-strip page-width reveal-on-scroll"
          aria-label="Product principles"
        >
          <p>
            Built for suppliers.
            <br />
            <strong>Designed for confidence.</strong>
          </p>
          <ul>
            <li>
              <Icon name="search" size={20} />
              Relevant discovery
            </li>
            <li>
              <Icon name="document" size={20} />
              Official tender documents
            </li>
            <li>
              <Icon name="history" size={20} />
              Simple demo checkout
            </li>
            <li>
              <Icon name="shield" size={20} />
              You stay in control
            </li>
          </ul>
        </section>

        <section className="how-section page-width" id="how-it-works">
          <div className="section-heading reveal-on-scroll">
            <div>
              <div className="eyebrow">From notice to knowing</div>
              <h2>
                A simpler path to
                <br />
                your next <span className="serif-accent">good fit.</span>
              </h2>
            </div>
            <p>
              Set up once, review the source and complete a simulated purchase.
              Keep your demo receipts together in My tenders.
            </p>
          </div>
          <div className="steps-grid">
            <article className="reveal-on-scroll">
              <div className="step-top">
                <span className="step-icon">
                  <Icon name="building" size={22} />
                </span>
                <span>01 / Your business</span>
              </div>
              <h3>One profile. A better starting point.</h3>
              <p>
                Sign in with Google and save your business details. Keep
                DigiLocker verification connected to your supplier profile.
              </p>
              <Link className="text-link" href="/dashboard/profile">
                Build your profile <Icon name="arrowRight" size={15} />
              </Link>
            </article>
            <article className="reveal-on-scroll">
              <div className="step-top">
                <span className="step-icon">
                  <Icon name="document" size={22} />
                </span>
                <span>02 / Your evidence</span>
              </div>
              <h3>Find a tender. Review the source.</h3>
              <p>
                Fetch official notices with TinyFish. Check the closing date,
                open the tender documents and read any amendments.
              </p>
              <Link className="text-link" href="/dashboard">
                Explore the workspace <Icon name="arrowRight" size={15} />
              </Link>
            </article>
            <article className="reveal-on-scroll">
              <div className="step-top">
                <span className="step-icon">
                  <Icon name="history" size={22} />
                </span>
                <span>03 / Your demo purchase</span>
              </div>
              <h3>Complete checkout. Keep the receipt.</h3>
              <p>
                Try a simulated payment, retry a failure and download your demo
                receipt. No real money is charged or bid submitted.
              </p>
              <Link className="text-link" href="/dashboard/purchases">
                View My tenders <Icon name="arrowRight" size={15} />
              </Link>
            </article>
          </div>
        </section>

        <section className="clarity-section" id="why-tenderlens">
          <div className="page-width clarity-grid">
            <div className="reveal-on-scroll">
              <div className="eyebrow">Less guesswork. More grounding.</div>
              <h2>
                A relevant tender
                <br />
                is only the <span className="serif-accent">beginning.</span>
              </h2>
              <p>
                Check the details that make a difference before you spend hours
                preparing a bid. Missing or ambiguous information stays visible
                for your review.
              </p>
              <Link href="/dashboard" className="text-link">
                Take a closer look <Icon name="arrowRight" size={16} />
              </Link>
            </div>
            <div className="clarity-checks reveal-on-scroll">
              {[
                {
                  label: "Google sign-in & supplier profile",
                  icon: "building" as const,
                },
                {
                  label: "DigiLocker & official documents",
                  icon: "shield" as const,
                },
                {
                  label: "Demo checkout & saved receipt",
                  icon: "checkCircle" as const,
                },
              ].map((item) => (
                <div key={item.label}>
                  <span>
                    <Icon name={item.icon} size={19} />
                  </span>
                  <strong>{item.label}</strong>
                  <Icon name="check" size={17} />
                </div>
              ))}
              <p>
                <Icon name="link" size={14} /> Review the issuer’s documents for
                actual fees, eligibility and submission instructions.
              </p>
            </div>
          </div>
        </section>

        <section className="landing-cta page-width reveal-on-scroll">
          <div className="eyebrow">Make room for the right opportunity</div>
          <h2>
            Your next bid starts
            <br />
            with a <span className="serif-accent">clearer view.</span>
          </h2>
          <Link className="button button-primary" href="/dashboard">
            Step into your workspace <Icon name="arrowRight" size={17} />
          </Link>
          <p>
            Explore real IIIT-Delhi notices collected with TinyFish. Refresh the
            source when you’re ready.
          </p>
        </section>
      </main>
      <footer className="landing-footer page-width">
        <Brand />
        <span>A clearer view. A more considered bid.</span>
        <div>
          <span>Built with TinyFish</span>
          <Link href="/architecture">
            System architecture <Icon name="arrow" size={14} />
          </Link>
        </div>
        <small>© 2026 TenderLens · Team IDK</small>
      </footer>
    </div>
  );
}

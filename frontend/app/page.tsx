import Link from "next/link";
import { Brand } from "@/components/brand";
import { Icon } from "@/components/icon";
import { AuthProfile } from "@/components/auth-profile";

function ProductPreview() {
  return (
    <div
      className="hero-product"
      aria-label="Illustrative TenderLens readiness preview"
    >
      <div className="orbit orbit-one" />
      <div className="orbit orbit-two" />
      <div className="preview-caption">
        <span className="live-dot" /> A little clarity goes a long way.
      </div>
      <div className="preview-document">
        <div className="document-topline">
          <span className="mini-document">
            <Icon name="document" size={19} />
          </span>
          <span>YOUR NEXT OPPORTUNITY</span>
          <Icon name="bookmark" size={16} />
        </div>
        <div className="preview-issuer">
          <span className="institution-symbol">II</span> INSTITUTIONAL
          PROCUREMENT
        </div>
        <h3>
          Supply & installation of
          <br />
          digital oscilloscopes
        </h3>
        <div className="preview-tags">
          <span>Electronics</span>
          <span>Open tender</span>
        </div>
        <div className="preview-divider" />
        <div className="preview-facts">
          <div>
            <small>Estimated value</small>
            <strong>₹12.5 lakh</strong>
          </div>
          <div>
            <small>Closing date</small>
            <strong>06 Nov 2026</strong>
          </div>
        </div>
        <div className="preview-condition">
          <Icon name="checkCircle" size={17} />
          <span>Turnover requirement</span>
          <b>Meets</b>
        </div>
        <div className="preview-condition">
          <Icon name="checkCircle" size={17} />
          <span>Past experience</span>
          <b>Meets</b>
        </div>
        <div className="preview-condition">
          <Icon name="checkCircle" size={17} />
          <span>Required certificates</span>
          <b>Meets</b>
        </div>
        <div className="preview-source">
          <Icon name="link" size={13} /> Every check, linked to its source.
        </div>
      </div>
      <div className="preview-amendment">
        <span className="amendment-icon">
          <Icon name="history" size={20} />
        </span>
        <div>
          <strong>A change. Already in sight.</strong>
          <p>Closing date extended by 7 days</p>
          <span>
            30 Oct <Icon name="arrowRight" size={12} /> <b>06 Nov</b>
          </span>
        </div>
        <span className="notification-dot" />
      </div>
      <div className="preview-readiness">
        <span className="readiness-check">
          <Icon name="check" size={19} />
        </span>
        <div>
          <strong>Looks like a good fit.</strong>
          <small>All 5 checked conditions meet</small>
        </div>
        <span className="tiny-leaf">
          <Icon name="leaf" size={20} />
        </span>
      </div>
      <span className="preview-sample">
        Illustrative sample · always verify the source
      </span>
    </div>
  );
}

export default function Home() {
  return (
    <div className="landing">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="landing-nav page-width">
        <Brand />
        <nav aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#why-tenderlens">Why TenderLens</a>
          <Link href="/dashboard/sources">Our source</Link>
        </nav>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <AuthProfile />
          <Link className="button button-small button-dark" href="/dashboard">
            Open workspace <Icon name="arrowRight" size={16} />
          </Link>
        </div>
      </header>
      <main id="main">
        <section className="hero page-width">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="eyebrow-line" /> BIG OPPORTUNITIES. SMALL TEAMS.
            </div>
            <h1>
              Find the tender
              <br />
              worth <em>your time.</em>
            </h1>
            <p>
              Less searching. Fewer surprises. A clearer view of the tenders
              that fit your business—with the evidence to back it up.
            </p>
            <div className="hero-actions">
              <Link className="button button-dark" href="/dashboard">
                Find your next opportunity <Icon name="arrowRight" size={18} />
              </Link>
              <a className="text-link" href="#how-it-works">
                See how it works <span className="play-icon">↗</span>
              </a>
            </div>
            <div className="hero-reassurance">
              <Icon name="shield" size={15} />
              <span>Your decision. Supported by evidence.</span>
            </div>
          </div>
          <ProductPreview />
        </section>
        <section
          className="principles-strip page-width"
          aria-label="Product principles"
        >
          <span>
            Built for suppliers.
            <br />
            <strong>Designed for confidence.</strong>
          </span>
          <div>
            <Icon name="search" size={22} />
            <span>Relevant discovery</span>
          </div>
          <div>
            <Icon name="document" size={22} />
            <span>Clause-level evidence</span>
          </div>
          <div>
            <Icon name="history" size={22} />
            <span>Every amendment in view</span>
          </div>
          <div>
            <Icon name="shield" size={22} />
            <span>You stay in control</span>
          </div>
        </section>
        <section className="how-section page-width" id="how-it-works">
          <div className="section-heading">
            <div>
              <div className="eyebrow">FROM NOTICE TO KNOWING</div>
              <h2>
                A simpler path to
                <br />
                your next good fit.
              </h2>
            </div>
            <p>
              The right tender is more than a keyword match.
              <br />
              Know what fits, what blocks you, and what changed.
            </p>
          </div>
          <div className="steps-grid">
            <article>
              <div className="step-top">
                <span className="step-icon">
                  <Icon name="building" size={25} />
                </span>
                <span>01 / YOUR BUSINESS</span>
              </div>
              <h3>One profile. A better starting point.</h3>
              <p>
                Add your categories, experience, turnover, and certificates. Let
                your capabilities guide your shortlist.
              </p>
              <Link href="/dashboard/profile">
                Build your profile <Icon name="arrowRight" size={16} />
              </Link>
            </article>
            <article>
              <div className="step-top">
                <span className="step-icon">
                  <Icon name="document" size={25} />
                </span>
                <span>02 / YOUR EVIDENCE</span>
              </div>
              <h3>
                Readiness you can
                <br />
                trace back.
              </h3>
              <p>
                See each requirement beside your supplier facts. Open the exact
                clause behind every check.
              </p>
              <Link href="/dashboard">
                Explore the workspace <Icon name="arrowRight" size={16} />
              </Link>
            </article>
            <article>
              <div className="step-top">
                <span className="step-icon">
                  <Icon name="history" size={25} />
                </span>
                <span>03 / YOUR NEXT MOVE</span>
              </div>
              <h3>
                Changes don’t have
                <br />
                to be surprises.
              </h3>
              <p>
                Keep the original notice and its amendments together. See the
                before, the after, and what it means for you.
              </p>
              <Link href="/dashboard/amendments">
                See amendment tracking <Icon name="arrowRight" size={16} />
              </Link>
            </article>
          </div>
        </section>
        <section className="clarity-section" id="why-tenderlens">
          <div className="page-width clarity-grid">
            <div>
              <div className="eyebrow">LESS GUESSWORK. MORE GROUNDING.</div>
              <h2>
                A relevant tender
                <br />
                is only the beginning.
              </h2>
              <p>
                Check the details that make a difference before you spend hours
                preparing a bid. Missing or ambiguous information stays visible
                for your review.
              </p>
              <Link href="/dashboard" className="text-link">
                Take a closer look <Icon name="arrowRight" size={17} />
              </Link>
            </div>
            <div className="clarity-checks">
              {[
                {
                  label: "Turnover & financial period",
                  icon: "building" as const,
                },
                { label: "Experience & certificates", icon: "shield" as const },
                { label: "Deposit & closing deadline", icon: "clock" as const },
              ].map((item) => (
                <div key={item.label}>
                  <span>
                    <Icon name={item.icon} size={21} />
                  </span>
                  <strong>{item.label}</strong>
                  <Icon name="check" size={18} />
                </div>
              ))}
              <p>
                <Icon name="link" size={14} /> Every extracted condition
                includes its source and page.
              </p>
            </div>
          </div>
        </section>
        <section className="landing-cta page-width">
          <div className="cta-leaf">
            <Icon name="leaf" size={32} />
          </div>
          <div className="eyebrow">MAKE ROOM FOR THE RIGHT OPPORTUNITY</div>
          <h2>
            Your next bid starts
            <br />
            with a clearer view.
          </h2>
          <Link className="button button-lime" href="/dashboard">
            Step into your workspace <Icon name="arrowRight" size={18} />
          </Link>
          <p>
            Explore the sample workspace. Connect live discovery when you’re
            ready.
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

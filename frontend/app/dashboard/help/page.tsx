import Link from "next/link";
import { Icon } from "@/components/icon";

export default function HelpPage() {
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">A LITTLE GUIDANCE GOES A LONG WAY</div>
          <h1>Find your feet. Then your next fit.</h1>
          <p>Here’s how to get the most from your TenderLens workspace.</p>
        </div>
      </div>
      <div className="help-grid">
        <article className="help-card">
          <Icon name="building" size={25} />
          <h2>Start with your supplier profile.</h2>
          <p>
            Add your annual turnover, completed supply orders, available deposit
            funds, and certificate status. Leave unknown facts blank. Saving a
            profile immediately updates the sample readiness checks.
          </p>
          <Link className="text-link" href="/dashboard/profile">
            Open supplier profile <Icon name="arrowRight" size={15} />
          </Link>
        </article>
        <article className="help-card">
          <Icon name="shield" size={25} />
          <h2>Read the readiness labels.</h2>
          <p>
            Meets checked conditions means all five supported checks passed.
            Blocked means a known mandatory check failed. Review needed means
            information or evidence is missing or uncertain. Always inspect the
            complete source before bidding.
          </p>
          <Link className="text-link" href="/dashboard">
            Review your shortlist <Icon name="arrowRight" size={15} />
          </Link>
        </article>
        <article className="help-card">
          <Icon name="document" size={25} />
          <h2>Open the evidence.</h2>
          <p>
            Select a tender, expand a readiness check, and follow its clause
            reference. Sample documents are synthetic and labelled. Live
            discovery provides source links; its PDF clause processing is still
            pending.
          </p>
          <Link className="text-link" href="/dashboard/tenders">
            Discover tenders <Icon name="arrowRight" size={15} />
          </Link>
        </article>
        <article className="help-card">
          <Icon name="globe" size={25} />
          <h2>Try live discovery with TinyFish.</h2>
          <p>
            Configure your server-side API key and start a source run.
            TenderLens shows progress and preserves your previous results on
            failure. The developer’s MCP connection and the application’s API
            key configuration are separate.
          </p>
          <Link className="text-link" href="/dashboard/sources">
            Check connected sources <Icon name="arrowRight" size={15} />
          </Link>
        </article>
      </div>
    </>
  );
}

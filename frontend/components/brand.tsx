import Link from "next/link";

export function Brand({
  compact = false,
  light = false,
}: {
  compact?: boolean;
  light?: boolean;
}) {
  return (
    <Link
      href="/"
      className={`brand ${light ? "brand-light" : ""}`}
      aria-label="TenderLens home"
    >
      <span className="brand-mark" aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
      {!compact && (
        <span>
          Tender<span className="brand-lightweight">Lens</span>
          <span className="brand-period">.</span>
        </span>
      )}
    </Link>
  );
}

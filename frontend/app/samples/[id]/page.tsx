import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { SAMPLE_TENDERS } from "@/lib/demo-data";
import Link from "next/link";
import { Brand } from "@/components/brand";
import { Icon } from "@/components/icon";

export function generateStaticParams() {
  return SAMPLE_TENDERS.map((tender) => ({ id: tender.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const tender = SAMPLE_TENDERS.find((item) => item.id === id);
  return {
    title: tender ? `${tender.title} · Sample document` : "Sample document",
  };
}

export default async function SampleDocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const tender = SAMPLE_TENDERS.find((item) => item.id === id);
  if (!tender) notFound();
  return (
    <main className="sample-document">
      <div className="sample-document-top">
        <Brand />
        <Link className="text-link" href="/dashboard/tenders">
          <Icon
            name="arrowRight"
            size={14}
            style={{ transform: "rotate(180deg)" }}
          />
          Back to tenders
        </Link>
      </div>
      <h1>{tender.title}</h1>
      <div className="inline-notice">
        Illustrative sample document. These clauses and page references are
        synthetic and do not represent an actual IIIT-Delhi procurement notice.
        This view demonstrates clause-level evidence navigation.
      </div>
      {[...tender.conditions]
        .sort((a, b) => a.page - b.page)
        .map((condition) => (
          <article
            className="sample-paper"
            key={condition.type}
            id={`page-${condition.page}`}
          >
            <div className="eyebrow">
              SYNTHETIC TENDER · {tender.reference} · PAGE {condition.page}
            </div>
            <h2>
              {condition.clause} — {condition.label}
            </h2>
            <p>{condition.quote}</p>
            <footer>
              Sample evidence only · TenderLens · Physical page {condition.page}
            </footer>
          </article>
        ))}
    </main>
  );
}

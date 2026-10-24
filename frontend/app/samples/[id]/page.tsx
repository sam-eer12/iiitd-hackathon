import { notFound } from "next/navigation";
import { SAMPLE_TENDERS } from "@/lib/demo-data";
import { Brand } from "@/components/brand";

export function generateStaticParams() {
  return SAMPLE_TENDERS.map((tender) => ({ id: tender.id }));
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
      <Brand />
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

import type { Condition, SupplierProfile, Tender } from "./types";

export const DEMO_CLOCK = "2026-10-24T09:00:00+05:30";
export const DEFAULT_PROFILE: SupplierProfile = {
  company: "Acme Lab Supplies",
  contact: "Sameer Gupta",
  email: "sameer@example.com",
  categories: ["Lab equipment", "Electronics", "IT equipment"],
  turnover: [
    { year: "2023–24", amount: 3200000 },
    { year: "2024–25", amount: 3500000 },
    { year: "2025–26", amount: 3800000 },
  ],
  completedOrders: 4,
  depositCapacity: 150000,
  certificates: { gst: true, iso: true, manufacturer: null },
};

function conditions({
  turnover = 2500000,
  certificate = "gst",
  deposit = 50000,
  orders = 3,
  deadline = "2026-11-06T15:00:00+05:30",
}: {
  turnover?: number;
  certificate?: "gst" | "iso" | "manufacturer";
  deposit?: number;
  orders?: number;
  deadline?: string;
} = {}): Condition[] {
  const certificateName = {
    gst: "GST registration",
    iso: "ISO 9001 certificate",
    manufacturer: "Manufacturer authorization",
  }[certificate];
  return [
    {
      type: "turnover",
      label: "Annual turnover",
      requirement: `Average turnover ≥ ₹${turnover / 100000} lakh`,
      threshold: turnover,
      years: ["2023–24", "2024–25", "2025–26"],
      quote: `The bidder shall have an average annual turnover of not less than INR ${turnover.toLocaleString("en-IN")} during financial years 2023–24, 2024–25 and 2025–26.`,
      page: 4,
      clause: "3.2",
    },
    {
      type: "experience",
      label: "Past experience",
      requirement: `At least ${orders} completed supply orders`,
      threshold: orders,
      quote: `The bidder must have successfully completed at least ${orders} supply orders in the specified equipment category.`,
      page: 5,
      clause: "3.3",
    },
    {
      type: "certificate",
      label: "Required certificate",
      requirement: certificateName,
      certificate,
      quote: `A copy of the bidder's ${certificateName} is mandatory and must accompany the technical bid.`,
      page: 6,
      clause: "3.5",
    },
    {
      type: "deposit",
      label: "Earnest money deposit",
      requirement: `EMD of ₹${deposit.toLocaleString("en-IN")}`,
      threshold: deposit,
      quote: `An earnest money deposit of INR ${deposit.toLocaleString("en-IN")} is required. No exemption has been applied in this sample.`,
      page: 3,
      clause: "2.1",
    },
    {
      type: "deadline",
      label: "Submission deadline",
      requirement: `${new Date(deadline).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Kolkata" })}, 3:00 PM IST`,
      deadline,
      quote: `The last date and time for submission is ${deadline}. Late submissions will not be accepted.`,
      page: 1,
      clause: "1.4",
    },
  ];
}

const definitions = [
  {
    title: "Supply & installation of digital oscilloscopes",
    category: "Electronics",
    value: "₹12.5 lakh",
    relevance: 98,
    turnover: 2500000,
    amended: true,
  },
  {
    title: "Laboratory microscopes and imaging systems",
    category: "Lab equipment",
    value: "₹8.2 lakh",
    relevance: 96,
    turnover: 2000000,
    certificate: "manufacturer" as const,
  },
  {
    title: "High-performance computing workstations",
    category: "IT equipment",
    value: "₹24.0 lakh",
    relevance: 94,
    turnover: 5000000,
  },
  {
    title: "Precision digital multimeters for teaching labs",
    category: "Electronics",
    value: "₹4.8 lakh",
    relevance: 92,
    turnover: 1500000,
    deposit: 25000,
  },
  {
    title: "Network switches and structured cabling",
    category: "IT equipment",
    value: "₹9.6 lakh",
    relevance: 89,
    turnover: 3000000,
    certificate: "manufacturer" as const,
    amended: true,
  },
  {
    title: "Benchtop centrifuges and laboratory accessories",
    category: "Lab equipment",
    value: "₹6.3 lakh",
    relevance: 87,
    turnover: 2000000,
    certificate: "iso" as const,
  },
  {
    title: "Advanced spectrum analyzer and RF equipment",
    category: "Electronics",
    value: "₹32.0 lakh",
    relevance: 85,
    turnover: 7500000,
    deposit: 200000,
  },
  {
    title: "Supply of laboratory power supply units",
    category: "Electronics",
    value: "₹3.2 lakh",
    relevance: 83,
    turnover: 1500000,
    certificate: "manufacturer" as const,
  },
];

export const SAMPLE_TENDERS: Tender[] = definitions.map((item, index) => {
  const rules = conditions(item);
  const deadline = rules.find((condition) => condition.type === "deadline")!;
  return {
    id: `sample-${index + 1}`,
    reference: `DEMO/2026/${String(41 + index).padStart(3, "0")}`,
    title: item.title,
    description:
      "Supply, installation, and commissioning of equipment, including documentation and standard warranty support.",
    issuer: "IIIT-Delhi · Sample notice",
    category: item.category,
    value: item.value,
    deadline: deadline.deadline!,
    deadlineText: deadline.requirement,
    relevance: item.relevance,
    sourceUrl: "https://iiitd.ac.in/tenders",
    pdfUrls: [],
    amendmentUrls: [],
    provenance: "sample",
    retrievedAt: DEMO_CLOCK,
    amended: item.amended ?? false,
    conditions: rules,
  };
});

export const SAMPLE_CHANGES = [
  {
    id: "deadline-extension",
    tenderId: "sample-1",
    field: "Submission deadline extended",
    before: "30 Oct 2026, 3:00 PM IST",
    after: "6 Nov 2026, 3:00 PM IST",
    date: "24 Oct 2026",
    clause: "Corrigendum 01 · page 1",
    detail:
      "Seven additional days to prepare your bid. Other checked conditions are unchanged.",
    type: "deadline",
  },
  {
    id: "certificate-clarification",
    tenderId: "sample-5",
    field: "Manufacturer authorization clarified",
    before: "Authorization from OEM / distributor",
    after: "Authorization directly from OEM",
    date: "23 Oct 2026",
    clause: "Corrigendum 01 · page 2",
    detail:
      "Review your authorization letter. A distributor letter alone is no longer sufficient in this sample.",
    type: "certificate",
  },
];

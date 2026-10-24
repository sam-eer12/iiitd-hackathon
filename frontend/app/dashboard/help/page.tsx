import Link from "next/link";
import { Icon, type IconName } from "@/components/icon";

export const metadata = { title: "Help & getting started" };

export default function HelpPage() {
  const steps: {
    title: string;
    text: string;
    href: string;
    action: string;
    icon: IconName;
  }[] = [
    {
      title: "1. Sign in and save your profile",
      text: "Use Google sign-in. Save your business name, contact, email and supply categories so checkout has the right supplier details.",
      href: "/dashboard/profile",
      action: "Open supplier profile",
      icon: "building",
    },
    {
      title: "2. Connect DigiLocker",
      text: "Verify the contact person’s PAN through DigiLocker. GST verification uses EntityLocker. Test checks and unverified identities remain clearly labelled; verification is optional for the demo checkout.",
      href: "/dashboard/profile#document-verification",
      action: "Open document verification",
      icon: "shield",
    },
    {
      title: "3. Fetch and review tenders",
      text: "Fetch notices from the official IIIT-Delhi listing with TinyFish. Open a tender, check the deadline and review the official PDFs and any amendments. Actual fees and eligibility come from the issuer’s documents.",
      href: "/dashboard/tenders",
      action: "Find a tender",
      icon: "search",
    },
    {
      title: "4. Buy in the demo",
      text: "Acknowledge your review and the demo, then simulate a successful or failed payment. A successful attempt saves a downloadable demo receipt in My tenders. ₹499 is a demo amount; nothing is charged, reserved or submitted to the issuer.",
      href: "/dashboard/purchases",
      action: "View My tenders",
      icon: "checkCircle",
    },
  ];
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">THE SUPPLIER WORKFLOW</div>
          <h1>From sign-in to demo purchase.</h1>
          <p>
            Four steps, with the official tender documents always within reach.
          </p>
        </div>
      </div>
      <div className="help-grid">
        {steps.map((step) => (
          <article className="help-card" key={step.title}>
            <Icon name={step.icon} size={25} />
            <h2>{step.title}</h2>
            <p>{step.text}</p>
            <Link className="text-link" href={step.href}>
              {step.action}
              <Icon name="arrowRight" size={15} />
            </Link>
          </article>
        ))}
      </div>
    </>
  );
}

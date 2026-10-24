import { TenderExplorer } from "@/components/tender-explorer";

export const metadata = { title: "Saved tenders" };
export default function SavedPage() {
  return <TenderExplorer mode="saved" />;
}

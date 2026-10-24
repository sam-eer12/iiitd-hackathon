import { TenderExplorer } from "@/components/tender-explorer";

export const metadata = { title: "Discover tenders" };
export default function DiscoverPage() {
  return <TenderExplorer mode="discover" />;
}

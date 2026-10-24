import { Icon } from "./icon";
import { STATUS_LABELS } from "@/lib/rules";
import type { Readiness } from "@/lib/types";

export function StatusBadge({
  status,
  short = false,
}: {
  status: Readiness;
  short?: boolean;
}) {
  return (
    <span className={`status-badge status-${status}`}>
      <Icon
        name={
          status === "meets"
            ? "checkCircle"
            : status === "blocked"
              ? "minus"
              : "clock"
        }
        size={13}
      />
      {short && status === "meets" ? "Meets checks" : STATUS_LABELS[status]}
    </span>
  );
}

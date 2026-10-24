import { Icon, type IconName } from "./icon";

/* Full-page message for not-found and error screens. */
export function StatePanel({
  icon,
  eyebrow,
  title,
  children,
  actions,
}: {
  icon: IconName;
  eyebrow: string;
  title: string;
  children: React.ReactNode;
  actions: React.ReactNode;
}) {
  return (
    <section className="state-panel" aria-labelledby="state-panel-title">
      <span className="state-panel-icon">
        <Icon name={icon} size={24} />
      </span>
      <div className="eyebrow">{eyebrow}</div>
      <h1 id="state-panel-title">{title}</h1>
      <p>{children}</p>
      <div className="state-panel-actions">{actions}</div>
    </section>
  );
}

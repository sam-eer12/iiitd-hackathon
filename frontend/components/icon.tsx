import type { CSSProperties } from "react";

const paths = {
  arrow: "M7 17 17 7M7 7h10v10",
  arrowRight: "M5 12h14m-6-6 6 6-6 6",
  chevron: "m9 5 7 7-7 7",
  chevronDown: "m6 9 6 6 6-6",
  search: "m21 21-4.3-4.3M19 10.5a8.5 8.5 0 1 1-17 0 8.5 8.5 0 0 1 17 0",
  grid: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
  document:
    "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6ZM14 2v6h6M8 13h8M8 17h5",
  bookmark: "M6 3h12a1 1 0 0 1 1 1v18l-7-4-7 4V4a1 1 0 0 1 1-1Z",
  history: "M3 11a9 9 0 1 1 2.4 7.1M3 4v7h7m2-5v6l4 2",
  building: "M4 22V3h12v19M16 9h4v13M1 22h22M8 7h4M8 11h4M8 15h4M9 22v-3h2v3",
  globe:
    "M21 12H3m9-9a16 16 0 0 1 0 18 16 16 0 0 1 0-18Zm9 9a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  settings:
    "m12 3 2 3 3-.2.8 3.1L21 11l-1.5 2.7.2 3-3.1.8L15 21l-3-1-3 1-1.6-3.5-3.1-.8.2-3L3 11l3.2-2.1L7 5.8l3 .2 2-3Zm3 9a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z",
  help: "M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3m.1 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  panel: "M3 3h18v18H3zM9 3v18m6-14-3 5 3 5",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4",
  refresh: "M20 7a9 9 0 0 0-15-1L2 9m0-6v6h6m-4 8a9 9 0 0 0 15 1l3-3m0 6v-6h-6",
  check: "m5 12 4 4L19 6",
  checkCircle: "m8 12 3 3 5-6M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  alert: "m12 3 10 18H2L12 3Zm0 6v4m0 4h.01",
  clock: "M12 7v5l3 2m6-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  close: "m6 6 12 12M6 18 18 6",
  filter: "M4 6h16M7 12h10m-6 6h2M8 3v6m8 0v6m-4 0v6",
  download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
  link: "m10 13 4-4m-6 6-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m2 3 2-2a4 4 0 1 1 6 6l-5 5a4 4 0 0 1-6 0",
  leaf: "M20 3C8 1 1 8 5 16s18 5 15-13ZM4 21 15 10",
  shield: "M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6l-9-4Zm-4 10 3 3 5-6",
  spark: "m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5L12 2Z",
  code: "m8 5-7 7 7 7m8-14 7 7-7 7m-3-17-2 20",
  activity: "M2 12h5l3-9 4 18 3-9h5",
  menu: "M4 6h16M4 12h16M4 18h16",
  mail: "M3 5h18v14H3zM3 5l9 8 9-8",
  minus: "M5 12h14",
  plus: "M5 12h14m-7-7v14",
  pause: "M9 5v14M15 5v14",
  play: "m8 5 11 7-11 7V5Z",
} as const;

export type IconName = keyof typeof paths;

export function Icon({
  name,
  size = 20,
  className = "",
  style,
}: {
  name: IconName;
  size?: number;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={style}
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}

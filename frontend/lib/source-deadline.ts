const MONTHS = [
  "jan",
  "feb",
  "mar",
  "apr",
  "may",
  "jun",
  "jul",
  "aug",
  "sep",
  "oct",
  "nov",
  "dec",
];

// The IIIT-Delhi portal publishes local campus times. Preserve the original
// text separately; unsupported or ambiguous formats remain unresolved.
export function parseIiitdDeadline(text: string | null): string | null {
  if (!text) return null;
  const match = text
    .trim()
    .match(
      /^(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)\s+(\d{4})\s+at\s+(\d{1,2}):(\d{2})\s*(AM|PM|Noon)(?:\s+IST)?$/i,
    );
  if (!match) return null;
  const [, dayText, monthText, yearText, hourText, minuteText, periodText] =
    match;
  const month = MONTHS.indexOf(monthText.slice(0, 3).toLowerCase());
  const day = Number(dayText);
  const year = Number(yearText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const period = periodText.toLowerCase();
  if (
    month < 0 ||
    hour < 1 ||
    hour > 12 ||
    minute > 59 ||
    (period === "noon" && (hour !== 12 || minute !== 0))
  )
    return null;
  const calendar = new Date(Date.UTC(year, month, day));
  if (
    calendar.getUTCFullYear() !== year ||
    calendar.getUTCMonth() !== month ||
    calendar.getUTCDate() !== day
  )
    return null;
  const hours24 = (hour % 12) + (period === "am" ? 0 : 12);
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${year}-${pad(month + 1)}-${pad(day)}T${pad(hours24)}:${pad(minute)}:00+05:30`;
}

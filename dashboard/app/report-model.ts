import { DASHBOARD_TIME_ZONE, type Period } from "./dashboard-model.ts";

// Calendar midnight in the dashboard timezone; no hardcoded UTC offset.
export function periodBounds(period: Period, now = Date.now()) {
  const formatter = new Intl.DateTimeFormat("en-CA", { timeZone: DASHBOARD_TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" });
  const partsAt = (timestamp: number) => {
    const parts = formatter.formatToParts(timestamp);
    const value = (type: string) => Number(parts.find(part => part.type === type)?.value);
    return Date.UTC(value("year"), value("month") - 1, value("day"), value("hour"), value("minute"), value("second"));
  };
  const calendar = new Date(partsAt(now));
  calendar.setUTCHours(0, 0, 0, 0);
  calendar.setUTCDate(calendar.getUTCDate() - (period === "7d" ? 6 : period === "30d" ? 29 : 0));
  let start = calendar.getTime();
  for (let attempt = 0; attempt < 3; attempt++) start += calendar.getTime() - partsAt(start);
  return { start: new Date(start).toISOString(), end: new Date(now).toISOString() };
}

export function csvText(rows: Array<Array<string | number | null>>) {
  const cell = (value: string | number | null) => {
    let text = value === null ? "" : String(value);
    if (/^\s*[=+@-]/.test(text) || (text.length > 0 && text.charCodeAt(0) < 32)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  };
  return "\uFEFF" + rows.map(row => row.map(cell).join(";")).join("\r\n");
}

export function downloadCsv(filename: string, rows: Array<Array<string | number | null>>) {
  const url = URL.createObjectURL(new Blob([csvText(rows)], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; document.body.append(anchor); anchor.click(); anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

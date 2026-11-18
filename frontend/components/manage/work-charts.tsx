import { categoryColor } from "@/lib/work-summary";
import type { WorkSummary, YearSummary } from "@/lib/work-summary";
import { formatScore } from "@/lib/backend/labels";

/** What each colour means, with the total for the shown years so the colour never stands alone */
export function CategoryLegend({
  summary,
  years,
}: {
  summary: WorkSummary;
  years: YearSummary[];
}) {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-2 text-sm">
      {summary.categories.map((category) => {
        const total = years.reduce(
          (sum, y) =>
            sum +
            (y.categories.find((c) => c.code === category.code)?.score ?? 0),
          0,
        );
        return (
          <li key={category.code} className="flex items-center gap-2">
            <span
              aria-hidden
              className="h-3 w-3 shrink-0 rounded-sm"
              style={{
                background: categoryColor(category.code, summary.categories),
              }}
            />
            <span className="text-ink">{category.name}</span>
            <span className="text-ink-muted">{formatScore(total)}</span>
          </li>
        );
      })}
    </ul>
  );
}

/**
 * Score per academic year, stacked by rubric category. Plain SVG that scales to its box; the
 * year totals are written above the bars, and a table of the same numbers is there for
 * screen readers.
 */
export function YearStackedChart({
  summary,
  selected,
}: {
  summary: WorkSummary;
  selected?: number;
}) {
  const years = summary.years.filter((y) => y.total > 0).slice(-8);
  const max = Math.max(...years.map((y) => y.total), 1);
  const W = 420;
  const H = 240;
  const top = 26;
  const bottom = 30;
  const plot = H - top - bottom;
  const slot = W / years.length;
  const bar = Math.min(64, slot * 0.58);

  return (
    <figure>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="คะแนนภาระงานรายปีการศึกษา แยกตามหมวด"
        className="mx-auto h-auto w-full max-w-lg"
      >
        <line
          x1="0"
          x2={W}
          y1={H - bottom}
          y2={H - bottom}
          stroke="var(--color-line)"
        />
        {years.map((year, i) => {
          const x = i * slot + (slot - bar) / 2;
          let y = H - bottom;
          const dim = selected !== undefined && selected !== year.year;
          return (
            <g key={year.year} opacity={dim ? 0.4 : 1}>
              {year.categories.map((category) => {
                const h = (category.score / max) * plot;
                y -= h;
                return (
                  <rect
                    key={category.code}
                    x={x}
                    y={y}
                    width={bar}
                    height={Math.max(h, 0)}
                    fill={categoryColor(category.code, summary.categories)}
                    stroke="var(--color-surface)"
                    strokeWidth="1"
                  />
                );
              })}
              <text
                x={x + bar / 2}
                y={y - 6}
                textAnchor="middle"
                fontSize="12"
                fontWeight="600"
                fill="var(--color-ink)"
              >
                {formatScore(year.total)}
              </text>
              <text
                x={x + bar / 2}
                y={H - 10}
                textAnchor="middle"
                fontSize="12"
                fill="var(--color-ink-muted)"
              >
                {year.year}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="sr-only">
        <table>
          <caption>คะแนนภาระงานรายปีการศึกษา แยกตามหมวด</caption>
          <thead>
            <tr>
              <th>ปี</th>
              {summary.categories.map((c) => (
                <th key={c.code}>{c.name}</th>
              ))}
              <th>รวม</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => (
              <tr key={year.year}>
                <td>{year.year}</td>
                {summary.categories.map((c) => (
                  <td key={c.code}>
                    {formatScore(
                      year.categories.find((x) => x.code === c.code)?.score ??
                        0,
                    )}
                  </td>
                ))}
                <td>{formatScore(year.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

/** One year's categories as horizontal bars, longest first, with the value and its share */
export function CategoryBars({
  summary,
  year,
}: {
  summary: WorkSummary;
  year: YearSummary;
}) {
  const rows = [...year.categories].sort((a, b) => b.score - a.score);
  return (
    <ul className="space-y-3">
      {rows.map((row) => (
        <li key={row.code}>
          <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
            <span className="text-ink">{row.name}</span>
            <span className="shrink-0 font-semibold text-ink">
              {formatScore(row.score)}
              <span className="ml-1.5 font-normal text-ink-muted">
                {year.total > 0
                  ? Math.round((row.score / year.total) * 100)
                  : 0}
                %
              </span>
            </span>
          </div>
          <div className="h-2.5 rounded-full bg-surface-alt">
            <div
              className="h-full rounded-full"
              style={{
                width: `${year.total > 0 ? (row.score / year.total) * 100 : 0}%`,
                background: categoryColor(row.code, summary.categories),
              }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

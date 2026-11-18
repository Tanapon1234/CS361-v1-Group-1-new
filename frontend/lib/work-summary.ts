import type { LecturerWork, WorkEntry, WorkPublication } from '@/types/backend';

/** A sheet counts once it was sent: drafts and returned sheets are still being worked on */
const NOT_COUNTED = new Set(['draft', 'returned']);

export interface CategoryScore {
  code: string;
  name: string;
  score: number;
  entries: WorkEntry[];
}

export interface YearSummary {
  year: number;
  total: number;
  entryCount: number;
  categories: CategoryScore[];
  publications: WorkPublication[];
}

export interface WorkSummary {
  /** Oldest first, ready to draw left to right */
  years: YearSummary[];
  /** Every category seen, by code, so colours stay the same across years */
  categories: { code: string; name: string }[];
}

/** Totals recomputed from the entries that count, per academic year and rubric category */
export function summarizeWork(work: LecturerWork): WorkSummary {
  const names = new Map<string, string>();
  const years: YearSummary[] = work.years.map((group) => {
    const categories: CategoryScore[] = [];
    for (const category of group.categories) {
      const entries = category.entries.filter((e) => !NOT_COUNTED.has(e.submission_status));
      if (entries.length === 0) continue;
      names.set(category.code, category.name_th);
      categories.push({
        code: category.code,
        name: category.name_th,
        score: entries.reduce((sum, e) => sum + e.score, 0),
        entries,
      });
    }
    return {
      year: group.academic_year,
      total: categories.reduce((sum, c) => sum + c.score, 0),
      entryCount: categories.reduce((sum, c) => sum + c.entries.length, 0),
      categories,
      publications: group.publications,
    };
  });
  return {
    years: years
      .filter((y) => y.entryCount > 0 || y.publications.length > 0)
      .sort((a, b) => a.year - b.year),
    categories: [...names].map(([code, name]) => ({ code, name })).sort((a, b) => a.code.localeCompare(b.code)),
  };
}

/** One colour per rubric category, fixed by position so a category keeps its colour everywhere */
const PALETTE = ['#c3002f', '#1f6f8b', '#b7791f', '#4d7c0f', '#6d4c9f', '#52525b'];
export const categoryColor = (code: string, all: { code: string }[]) =>
  PALETTE[Math.max(0, all.findIndex((c) => c.code === code)) % PALETTE.length];

import Link from 'next/link';
import type { ReactNode } from 'react';

import { SUBMISSION_STATUS_LABEL } from '@/lib/backend/labels';
import type { SubmissionStatus } from '@/types/backend';

/**
 * Building blocks for the /manage pages. Same tokens as the public site
 * (brand red, ink, line) so both areas look like one product.
 */

export const inputClass =
  'w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted/60 focus:border-brand focus:outline-none disabled:bg-surface-alt disabled:text-ink-muted';

export const buttonClass =
  'inline-flex items-center justify-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-60';

export const secondaryButtonClass =
  'inline-flex items-center justify-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm font-semibold text-ink transition-colors hover:border-brand hover:text-brand disabled:cursor-not-allowed disabled:opacity-60';

export const dangerButtonClass =
  'inline-flex items-center justify-center gap-1.5 rounded-lg border border-brand/30 bg-surface px-3 py-1.5 text-sm font-semibold text-brand transition-colors hover:bg-brand-soft disabled:cursor-not-allowed disabled:opacity-60';

export const linkClass = 'font-semibold text-brand hover:underline';

export function PageHeader({
  title,
  description,
  back,
  actions,
}: {
  title: ReactNode;
  description?: ReactNode;
  back?: { href: string; label: string };
  actions?: ReactNode;
}) {
  return (
    <header className="mb-8">
      {back ? (
        <Link href={back.href} className="mb-3 inline-block text-sm font-medium text-ink-muted hover:text-brand">
          ← {back.label}
        </Link>
      ) : null}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2.5 text-2xl font-bold text-ink">
            <span className="h-6 w-1.5 rounded-full bg-brand" aria-hidden="true" />
            {title}
          </h1>
          {description ? <p className="mt-2 text-sm text-ink-muted">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
    </header>
  );
}

export function Section({
  title,
  description,
  actions,
  children,
  id,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  id?: string;
}) {
  return (
    <section id={id} className="rounded-xl border border-line bg-surface p-5 shadow-sm sm:p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-ink">{title}</h2>
          {description ? <p className="mt-1 text-xs text-ink-muted">{description}</p> : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

export function Field({
  label,
  hint,
  children,
  className = '',
}: {
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={`block text-sm ${className}`}>
      <span className="mb-1 block font-medium text-ink">{label}</span>
      {children}
      {hint ? <span className="mt-1 block text-xs text-ink-muted">{hint}</span> : null}
    </label>
  );
}

export function Checkbox({
  name,
  label,
  defaultChecked,
}: {
  name: string;
  label: string;
  defaultChecked?: boolean;
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-ink">
      <input
        type="checkbox"
        name={name}
        defaultChecked={defaultChecked}
        className="h-4 w-4 rounded border-line accent-brand"
      />
      {label}
    </label>
  );
}

export function Notice({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'error' | 'success';
  children: ReactNode;
}) {
  const tones = {
    info: 'border-line bg-surface-alt text-ink-muted',
    error: 'border-brand/30 bg-brand-soft text-brand',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  };
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`rounded-lg border px-4 py-3 text-sm ${tones[tone]}`}>
      {children}
    </div>
  );
}

export function EmptyNote({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed border-line px-4 py-6 text-center text-sm text-ink-muted">
      {children}
    </p>
  );
}

const STATUS_TONE: Record<SubmissionStatus, string> = {
  draft: 'bg-surface-alt text-ink-muted border-line',
  submitted: 'bg-sky-50 text-sky-800 border-sky-200',
  assessing: 'bg-amber-50 text-amber-800 border-amber-200',
  dept_review: 'bg-violet-50 text-violet-800 border-violet-200',
  returned: 'bg-brand-soft text-brand border-brand/30',
  dept_approved: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  sent_to_faculty: 'bg-emerald-100 text-emerald-900 border-emerald-300',
};

export function StatusBadge({ status }: { status: SubmissionStatus }) {
  return <Badge className={STATUS_TONE[status]}>{SUBMISSION_STATUS_LABEL[status]}</Badge>;
}

export function Badge({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${
        className || 'border-line bg-surface-alt text-ink-muted'
      }`}
    >
      {children}
    </span>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface-alt px-4 py-3">
      <p className="text-xs font-medium text-ink-muted">{label}</p>
      <p className="mt-1 text-xl font-bold text-ink">{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-ink-muted">{hint}</p> : null}
    </div>
  );
}

/** Horizontal scroll on small screens instead of squeezing columns */
export function Table({ head, children }: { head: ReactNode[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <thead className="bg-surface-alt text-xs font-semibold text-ink-muted">
          <tr>
            {head.map((cell, index) => (
              <th key={index} scope="col" className="px-3 py-2.5">
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line-soft">{children}</tbody>
      </table>
    </div>
  );
}

export function Td({ children, className = '' }: { children?: ReactNode; className?: string }) {
  return <td className={`px-3 py-2.5 align-top ${className}`}>{children}</td>;
}

export function Tabs({ items, current }: { items: { href: string; label: string }[]; current: string }) {
  return (
    <nav aria-label="แท็บ" className="mb-6 flex gap-1 overflow-x-auto border-b border-line">
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          aria-current={item.href === current ? 'page' : undefined}
          className={
            item.href === current
              ? '-mb-px border-b-2 border-brand px-4 py-2 text-sm font-bold whitespace-nowrap text-brand'
              : 'px-4 py-2 text-sm font-medium whitespace-nowrap text-ink-muted hover:text-brand'
          }
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}

export function Pager({
  total,
  limit,
  offset,
  hrefFor,
}: {
  total: number;
  limit: number;
  offset: number;
  hrefFor: (offset: number) => string;
}) {
  if (total <= limit) return null;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  return (
    <nav aria-label="เปลี่ยนหน้า" className="mt-4 flex items-center justify-between text-sm">
      <span className="text-ink-muted">
        หน้า {page} / {pages} (ทั้งหมด {total} รายการ)
      </span>
      <span className="flex gap-2">
        {offset > 0 ? (
          <Link className={secondaryButtonClass} href={hrefFor(Math.max(offset - limit, 0))}>
            ก่อนหน้า
          </Link>
        ) : null}
        {offset + limit < total ? (
          <Link className={secondaryButtonClass} href={hrefFor(offset + limit)}>
            ถัดไป
          </Link>
        ) : null}
      </span>
    </nav>
  );
}

/** Builds `/path?a=1&b=2`, skipping empty values */
export function withQuery(path: string, query: Record<string, string | number | undefined | null>) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value));
  }
  const search = params.toString();
  return search ? `${path}?${search}` : path;
}

/** First value of a search param */
export function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export function intParam(value: string | string[] | undefined): number | undefined {
  const parsed = Number.parseInt(param(value) ?? '', 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}

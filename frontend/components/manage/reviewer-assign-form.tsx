'use client';

import { startTransition, useCallback, useMemo, useState } from 'react';

import { ActionForm, type ActionState, type FormAction } from '@/components/manage/action-form';
import { Notice, inputClass } from '@/components/manage/ui';

export interface PickLecturer {
  id: string;
  name: string;
  email: string | null;
}

export interface PickRound {
  id: number;
  name: string;
  /** Shown under the name: the period, then the submit deadline */
  period: string;
  deadline: string;
}

function matches(lecturer: PickLecturer, query: string): boolean {
  const q = query.trim().toLowerCase();
  return !q || lecturer.name.toLowerCase().includes(q) || (lecturer.email ?? '').toLowerCase().includes(q);
}

/** Whole row is the tap target (about 44-48px), not just the radio or checkbox */
const ROW = 'flex min-h-12 cursor-pointer items-center gap-3 px-3 py-2 text-sm';

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <fieldset className="space-y-2">
      <legend className="flex items-center gap-2 text-sm font-semibold text-ink">
        <span className="flex size-6 items-center justify-center rounded-full bg-brand text-xs text-white">{n}</span>
        {title}
      </legend>
      {children}
    </fieldset>
  );
}

/**
 * Assign one reviewer to several lecturers in one round, built for a phone: searchable
 * lists with full-row tap targets, the reviewer left out of the reviewee list, and a
 * button that says how many pairs it will create.
 */
export function ReviewerAssignForm({
  lecturers,
  rounds,
  action,
}: {
  lecturers: PickLecturer[];
  rounds: PickRound[];
  action: FormAction;
}) {
  const [roundId, setRoundId] = useState<number | null>(rounds[0]?.id ?? null);
  const [reviewerId, setReviewerId] = useState<string | null>(null);
  const [reviewees, setReviewees] = useState<Set<string>>(new Set());
  const [reviewerQuery, setReviewerQuery] = useState('');
  const [revieweeQuery, setRevieweeQuery] = useState('');

  const reviewerChoices = useMemo(
    () => lecturers.filter((lecturer) => matches(lecturer, reviewerQuery)),
    [lecturers, reviewerQuery]
  );
  // The reviewer is never offered as a reviewee, so "same person" cannot be sent
  const revieweeChoices = useMemo(
    () => lecturers.filter((lecturer) => lecturer.id !== reviewerId && matches(lecturer, revieweeQuery)),
    [lecturers, reviewerId, revieweeQuery]
  );
  const reviewer = lecturers.find((lecturer) => lecturer.id === reviewerId);
  const round = rounds.find((candidate) => candidate.id === roundId);

  function chooseReviewer(id: string) {
    setReviewerId(id);
    // If they were ticked as a reviewee, drop them
    setReviewees((current) => {
      const next = new Set(current);
      next.delete(id);
      return next;
    });
  }

  function toggle(id: string) {
    setReviewees((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const submit = useCallback<FormAction>(
    async (previous, data) => {
      const result: ActionState = await action(previous, data);
      if (result?.ok) startTransition(() => setReviewees(new Set()));
      return result;
    },
    [action]
  );

  if (rounds.length === 0) {
    return <Notice>ไม่มีรอบประเมินที่เปิดรับอยู่ ต้องเปิดรอบ (หรือขยายกำหนดส่ง) ก่อนจึงจะมอบหมายผู้ตรวจได้</Notice>;
  }

  const count = reviewees.size;
  const ready = roundId !== null && reviewerId !== null && count > 0;

  return (
    <ActionForm
      action={submit}
      submitLabel={count > 0 ? `มอบหมาย ${count} คน` : 'มอบหมาย'}
      submitDisabled={!ready}
      large
      className="space-y-6"
    >
      {roundId !== null ? <input type="hidden" name="round_id" value={roundId} /> : null}
      {reviewerId !== null ? <input type="hidden" name="reviewer_id" value={reviewerId} /> : null}
      {[...reviewees].map((id) => (
        <input key={id} type="hidden" name="reviewee_id" value={id} />
      ))}

      <Step n={1} title="รอบประเมิน">
        <div
          role="radiogroup"
          aria-label="รอบประเมิน"
          className="max-h-60 divide-y divide-line-soft overflow-y-auto rounded-lg border border-line"
        >
          {rounds.map((candidate) => (
            <label key={candidate.id} className={`${ROW} ${roundId === candidate.id ? 'bg-brand-soft' : ''}`}>
              <input
                type="radio"
                checked={roundId === candidate.id}
                onChange={() => setRoundId(candidate.id)}
                className="size-5 accent-brand"
              />
              <span className="min-w-0">
                <span className="block truncate text-ink">{candidate.name}</span>
                <span className="block text-xs text-ink-muted">{candidate.period}</span>
                <span className="block text-xs text-ink-muted">{candidate.deadline}</span>
              </span>
            </label>
          ))}
        </div>
      </Step>

      <Step n={2} title="ผู้ตรวจสอบ (เลือก 1 คน)">
        <input
          type="search"
          value={reviewerQuery}
          onChange={(event) => setReviewerQuery(event.target.value)}
          placeholder="ค้นหาชื่อหรืออีเมล"
          aria-label="ค้นหาผู้ตรวจสอบ"
          className={`${inputClass} min-h-11`}
        />
        <div role="radiogroup" className="max-h-64 divide-y divide-line-soft overflow-y-auto rounded-lg border border-line">
          {reviewerChoices.length === 0 ? (
            <p className="px-3 py-4 text-sm text-ink-muted">ไม่พบอาจารย์</p>
          ) : (
            reviewerChoices.map((lecturer) => (
              <label key={lecturer.id} className={`${ROW} ${reviewerId === lecturer.id ? 'bg-brand-soft' : ''}`}>
                <input
                  type="radio"
                  checked={reviewerId === lecturer.id}
                  onChange={() => chooseReviewer(lecturer.id)}
                  className="size-5 accent-brand"
                />
                <span className="min-w-0">
                  <span className="block truncate text-ink">{lecturer.name}</span>
                  {lecturer.email ? <span className="block truncate text-xs text-ink-muted">{lecturer.email}</span> : null}
                </span>
              </label>
            ))
          )}
        </div>
      </Step>

      <Step n={3} title="อาจารย์ที่ต้องถูกตรวจ (เลือกได้หลายคน)">
        {!reviewer ? (
          <p className="rounded-lg bg-surface-alt px-3 py-3 text-sm text-ink-muted">เลือกผู้ตรวจสอบก่อน</p>
        ) : (
          <>
            <input
              type="search"
              value={revieweeQuery}
              onChange={(event) => setRevieweeQuery(event.target.value)}
              placeholder="ค้นหาชื่อหรืออีเมล"
              aria-label="ค้นหาอาจารย์ที่ต้องถูกตรวจ"
              className={`${inputClass} min-h-11`}
            />
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
              <p aria-live="polite" className="text-ink-muted">
                เลือกแล้ว <strong className="text-ink">{count}</strong> คน · ผู้ตรวจ: {reviewer.name}{round ? ` · ${round.name}` : ''}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setReviewees((current) => new Set([...current, ...revieweeChoices.map((l) => l.id)]))}
                  className="min-h-11 rounded-lg border border-line px-3 font-semibold text-ink hover:border-brand hover:text-brand"
                >
                  เลือกทั้งหมดที่แสดง
                </button>
                <button
                  type="button"
                  onClick={() => setReviewees(new Set())}
                  disabled={count === 0}
                  className="min-h-11 rounded-lg border border-line px-3 font-semibold text-ink hover:border-brand hover:text-brand disabled:opacity-50"
                >
                  ล้าง
                </button>
              </div>
            </div>
            <div className="max-h-80 divide-y divide-line-soft overflow-y-auto rounded-lg border border-line">
              {revieweeChoices.length === 0 ? (
                <p className="px-3 py-4 text-sm text-ink-muted">ไม่พบอาจารย์</p>
              ) : (
                revieweeChoices.map((lecturer) => (
                  <label key={lecturer.id} className={`${ROW} ${reviewees.has(lecturer.id) ? 'bg-brand-soft' : ''}`}>
                    <input
                      type="checkbox"
                      checked={reviewees.has(lecturer.id)}
                      onChange={() => toggle(lecturer.id)}
                      className="size-5 accent-brand"
                    />
                    <span className="min-w-0">
                      <span className="block truncate text-ink">{lecturer.name}</span>
                      {lecturer.email ? (
                        <span className="block truncate text-xs text-ink-muted">{lecturer.email}</span>
                      ) : null}
                    </span>
                  </label>
                ))
              )}
            </div>
          </>
        )}
      </Step>
    </ActionForm>
  );
}

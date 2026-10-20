'use client';

import { useRef, useState, type FormEvent } from 'react';

import { buttonClass, inputClass } from '@/components/manage/ui';
import type { ActionState } from '@/components/manage/action-form';

export type UploadStart =
  | { ok: true; url: string; fields: Record<string, string>; token: string }
  | { ok: false; message: string };

export interface FileInfo {
  name: string;
  type: string;
  size: number;
  label: string | null;
}

async function sha256(file: File): Promise<string | null> {
  try {
    const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
    return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('');
  } catch {
    return null; // crypto.subtle needs a secure context; the checksum is optional
  }
}

/**
 * Presigned S3 upload: 1) `start` asks the backend for a presigned POST,
 * 2) the browser sends the file straight to S3, 3) `finish` tells the backend it is there.
 * The file never passes through Next.js or the API.
 */
export function FileUpload({
  start,
  finish,
  accept,
  withLabel = false,
  submitLabel = 'อัปโหลด',
}: {
  start: (file: FileInfo) => Promise<UploadStart>;
  finish: (token: string, checksum: string | null) => Promise<ActionState>;
  accept?: string;
  withLabel?: boolean;
  submitLabel?: string;
}) {
  const [state, setState] = useState<ActionState>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get('file');
    if (!(file instanceof File) || file.size === 0) {
      setState({ ok: false, message: 'เลือกไฟล์ก่อน' });
      return;
    }
    setState(null);
    try {
      setBusy('กำลังขอสิทธิ์อัปโหลด…');
      const label = typeof form.get('label') === 'string' ? String(form.get('label')).trim() : '';
      const started = await start({
        name: file.name,
        type: file.type || 'application/octet-stream',
        size: file.size,
        label: label || null,
      });
      if (!started.ok) {
        setState({ ok: false, message: started.message });
        return;
      }

      setBusy('กำลังอัปโหลดไปที่ S3…');
      const body = new FormData();
      for (const [key, value] of Object.entries(started.fields)) body.append(key, value);
      body.append('file', file); // S3 requires the file to be the last field
      const response = await fetch(started.url, { method: 'POST', body });
      if (!response.ok) {
        setState({ ok: false, message: `อัปโหลดไป S3 ไม่สำเร็จ (HTTP ${response.status})` });
        return;
      }

      setBusy('กำลังยืนยันกับระบบ…');
      const finished = await finish(started.token, await sha256(file));
      setState(finished);
      if (finished?.ok) formRef.current?.reset();
    } catch {
      setState({
        ok: false,
        message: 'อัปโหลดไม่สำเร็จ: เชื่อมต่อ S3 ไม่ได้ (ตรวจสอบ DATA_BUCKET_NAME และ CORS ของ bucket)',
      });
    } finally {
      setBusy(null);
    }
  }

  return (
    <form ref={formRef} onSubmit={upload} className="flex flex-wrap items-center gap-2">
      <input type="file" name="file" accept={accept} required className="text-sm" aria-label="ไฟล์" />
      {withLabel ? (
        <input name="label" placeholder="คำอธิบายไฟล์ (ไม่บังคับ)" maxLength={255} className={`${inputClass} sm:w-56`} aria-label="คำอธิบายไฟล์" />
      ) : null}
      <button type="submit" disabled={busy !== null} className={buttonClass}>
        {busy ?? submitLabel}
      </button>
      {state ? (
        <p role={state.ok ? 'status' : 'alert'} className={`w-full text-xs ${state.ok ? 'text-emerald-700' : 'text-brand'}`}>
          {state.message}
        </p>
      ) : null}
    </form>
  );
}

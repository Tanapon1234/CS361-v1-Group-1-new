'use client';

import {
  startTransition,
  useActionState,
  useEffect,
  useRef,
  type FormEvent,
  type ReactNode,
} from 'react';

import { buttonClass, dangerButtonClass, secondaryButtonClass } from '@/components/manage/ui';

export type ActionState = { ok: boolean; message: string } | null;
export type FormAction = (state: ActionState, formData: FormData) => Promise<ActionState>;

const VARIANT = {
  primary: buttonClass,
  secondary: secondaryButtonClass,
  danger: dangerButtonClass,
};

/**
 * A form bound to a Server Action. Shows the action's message (the backend's error
 * text on failure), disables the button while it runs, and can ask for confirmation.
 *
 * It submits through onSubmit instead of `<form action>`: React 19 resets a form after
 * every `action` run, which would wipe what the user typed whenever the backend rejects
 * it. Here the inputs are only cleared on success, and only when `resetOnSuccess` is set.
 */
export function ActionForm({
  action,
  children,
  submitLabel = 'บันทึก',
  variant = 'primary',
  confirmText,
  resetOnSuccess = false,
  className = 'space-y-4',
  inline = false,
}: {
  action: FormAction;
  children?: ReactNode;
  submitLabel?: ReactNode;
  variant?: keyof typeof VARIANT;
  confirmText?: string;
  resetOnSuccess?: boolean;
  className?: string;
  /** Just a button (plus hidden inputs) on one line, message underneath */
  inline?: boolean;
}) {
  const [state, formAction, pending] = useActionState(action, null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state?.ok && resetOnSuccess) formRef.current?.reset();
  }, [state, resetOnSuccess]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    if (confirmText && !window.confirm(confirmText)) return;
    const data = new FormData(event.currentTarget);
    startTransition(() => formAction(data));
  }

  const button = (
    <button type="submit" disabled={pending} className={VARIANT[variant]}>
      {pending ? 'กำลังบันทึก…' : submitLabel}
    </button>
  );
  const message = state ? (
    <p
      role={state.ok ? 'status' : 'alert'}
      className={`text-xs ${state.ok ? 'text-emerald-700' : 'text-brand'} ${inline ? 'mt-1' : ''}`}
    >
      {state.message}
    </p>
  ) : null;

  if (inline) {
    return (
      <form ref={formRef} onSubmit={submit} className="inline-block">
        {children}
        {button}
        {state && !state.ok ? message : null}
      </form>
    );
  }

  return (
    <form ref={formRef} onSubmit={submit} className={className}>
      {children}
      <div className="flex flex-wrap items-center gap-3">
        {button}
        {message}
      </div>
    </form>
  );
}

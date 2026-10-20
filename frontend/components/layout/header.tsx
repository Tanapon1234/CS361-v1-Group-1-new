'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import csTuLogo from '@/public/cs-tu-logo.png';

interface NavItem {
  label: string;
  /** null = no destination page yet in V1 */
  href: string | null;
}

/**
 * Main nav per design #30 — ships "Faculties" (public directory) and "ระบบจัดการ"
 * (/manage: workload and lecturer data, backed by the FastAPI backend).
 * Items without a page render as <button aria-disabled>, which stays
 * Tab-reachable, instead of a <span> that looks like a link but is
 * unreachable by keyboard.
 */
const NAV_ITEMS: readonly NavItem[] = [
  { label: 'เกี่ยวกับเรา', href: null },
  { label: 'หลักสูตร', href: null },
  { label: 'วิจัย', href: null },
  { label: 'คณาจารย์', href: '/faculties' },
  { label: 'ข่าวสาร', href: null },
  { label: 'ติดต่อ', href: null },
  { label: 'ระบบจัดการ', href: '/manage' },
];

const COMING_SOON = 'อยู่ระหว่างพัฒนา';

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg
      className="h-6 w-6"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d={open ? 'M6 18 18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'}
      />
    </svg>
  );
}

/** A not-yet-enabled nav button — focusable, and screen readers announce it as disabled */
function DisabledNavButton({ label, className }: { label: string; className: string }) {
  return (
    <button type="button" aria-disabled="true" title={COMING_SOON} className={className}>
      {label}
    </button>
  );
}

export function Header() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  // Escape closes the mobile menu
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsMenuOpen(false);
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-surface shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:h-20">
        {/* Department logo — replaces the old text-only department name */}
        <Link href="/faculties" className="flex shrink-0 items-center" aria-label="ไปหน้าคณาจารย์">
          <Image
            src={csTuLogo}
            alt="Computer Science, Thammasat University"
            priority
            sizes="(min-width: 1024px) 128px, 104px"
            className="h-9 w-auto lg:h-11"
          />
        </Link>

        <nav aria-label="เมนูหลัก" className="hidden items-center gap-5 lg:flex xl:gap-8">
          {NAV_ITEMS.map((item) =>
            item.href ? (
              <Link
                key={item.label}
                href={item.href}
                aria-current={isActive(item.href) ? 'page' : undefined}
                className={
                  isActive(item.href)
                    ? 'relative py-7 text-sm font-bold text-brand after:absolute after:inset-x-0 after:bottom-0 after:h-[3px] after:rounded-full after:bg-brand after:content-[""]'
                    : 'py-7 text-sm font-semibold text-ink-muted transition-colors hover:text-brand'
                }
              >
                {item.label}
              </Link>
            ) : (
              <DisabledNavButton
                key={item.label}
                label={item.label}
                className="cursor-not-allowed py-7 text-sm font-medium text-ink-muted/50"
              />
            )
          )}
        </nav>

        <button
          type="button"
          onClick={() => setIsMenuOpen((open) => !open)}
          aria-expanded={isMenuOpen}
          aria-controls="mobile-menu"
          aria-label={isMenuOpen ? 'ปิดเมนู' : 'เปิดเมนู'}
          className="-mr-2 shrink-0 rounded-full p-2 text-brand transition-colors hover:bg-brand-soft lg:hidden"
        >
          <MenuIcon open={isMenuOpen} />
        </button>
      </div>

      {/* Red divider line under the navbar */}
      <div className="h-[3px] w-full bg-brand" aria-hidden="true" />

      {isMenuOpen ? (
        <nav
          id="mobile-menu"
          aria-label="เมนูหลัก (อุปกรณ์พกพา)"
          className="absolute inset-x-0 top-full flex flex-col border-b border-line-soft bg-surface px-4 py-1 shadow-xl lg:hidden"
        >
          {NAV_ITEMS.map((item) =>
            item.href ? (
              <Link
                key={item.label}
                href={item.href}
                onClick={() => setIsMenuOpen(false)}
                aria-current={isActive(item.href) ? 'page' : undefined}
                className="flex items-center gap-2 border-b border-line-soft py-3 text-sm font-bold text-brand last:border-b-0"
              >
                <span className="h-4 w-1 rounded-full bg-brand" aria-hidden="true" />
                {item.label}
              </Link>
            ) : (
              <DisabledNavButton
                key={item.label}
                label={item.label}
                className="cursor-not-allowed border-b border-line-soft py-3 pl-3 text-left text-sm font-medium text-ink-muted/50 last:border-b-0"
              />
            )
          )}
        </nav>
      ) : null}
    </header>
  );
}

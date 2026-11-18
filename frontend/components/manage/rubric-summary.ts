import { POSITION_LABEL, UNIT_LABEL, formatNumber } from '@/lib/backend/labels';
import type { RubricItem } from '@/types/backend';

/** One line describing how an item is scored: weight, unit and student tier */
export function itemSummary(item: RubricItem): string {
  const weight =
    item.weight_mode === 'fixed'
      ? `น้ำหนัก ${formatNumber(item.weight)}`
      : `${item.assessor_position ? POSITION_LABEL[item.assessor_position] : ''} ให้ค่า ${formatNumber(item.weight_min)}–${formatNumber(item.weight_max)}${item.range_basis === 'points' ? ' คะแนน' : ''}`;
  const divisor = item.unit_divisor !== 1 ? ` ÷ ${formatNumber(item.unit_divisor)}` : '';
  const tier =
    item.tier_min !== null || item.tier_max !== null
      ? ` · นศ. ${item.tier_min ?? 0}–${item.tier_max ?? '∞'}`
      : '';
  return `${weight} · ต่อ${UNIT_LABEL[item.unit]}${divisor}${tier}`;
}

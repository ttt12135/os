import { clampScore } from './utils';

export function levelFromScore(score: number | undefined, explicit?: string): string {
  if (explicit) {
    const value = explicit.trim();
    if (/^[A-E]$/i.test(value)) return value.toUpperCase();
    const normalized = value.toLowerCase();
    if (['excellent', 'top', 'benchmark'].includes(normalized)) return 'A';
    if (['good', 'strong'].includes(normalized)) return 'B';
    if (['medium', 'qualified', 'pass'].includes(normalized)) return 'C';
    if (['basic', 'weak'].includes(normalized)) return 'D';
    if (['poor', 'low', 'risk'].includes(normalized)) return 'E';
  }
  const normalizedScore = clampScore(score);
  if (normalizedScore === undefined) return '暂无数据';
  if (normalizedScore >= 90) return 'A';
  if (normalizedScore >= 80) return 'B';
  if (normalizedScore >= 70) return 'C';
  if (normalizedScore >= 60) return 'D';
  return 'E';
}

export function levelLabel(level: string) {
  switch (level) {
    case 'A': return '标杆级';
    case 'B': return '优秀';
    case 'C': return '合格';
    case 'D': return '基础完成';
    case 'E': return '证据不足';
    default: return '暂无数据';
  }
}

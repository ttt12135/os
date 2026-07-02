export const EMPTY_TEXT = '暂无数据';

export function cx(...classes: Array<string | false | undefined | null>) {
  return classes.filter(Boolean).join(' ');
}

export function asArray<T = unknown>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (!value || typeof value !== 'object') return [];
  const record = value as Record<string, unknown>;
  const candidates = ['items', 'repositories', 'repos', 'works', 'history', 'data', 'ranking', 'results', 'comparisons'];
  for (const key of candidates) {
    if (Array.isArray(record[key])) return record[key] as T[];
  }
  return [];
}

export function firstPresent(record: unknown, keys: string[], fallback: unknown = undefined): unknown {
  if (!record || typeof record !== 'object') return fallback;
  const source = record as Record<string, unknown>;
  for (const key of keys) {
    if (source[key] !== undefined && source[key] !== null && source[key] !== '') return source[key];
  }
  return fallback;
}

export function toDisplay(value: unknown, fallback = EMPTY_TEXT): string {
  if (value === undefined || value === null || value === '') return fallback;
  if (Array.isArray(value)) return value.length ? value.map((item) => toDisplay(item, '')).filter(Boolean).join('、') : fallback;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export function toNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const normalized = value.replace('%', '').trim();
    const parsed = Number(normalized);
    if (Number.isFinite(parsed)) return parsed;
  }
  return undefined;
}

export function toList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map((item) => toDisplay(item, '')).filter(Boolean);
  if (typeof value === 'string') return value.split(/\n|；|;|、/).map((item) => item.trim()).filter(Boolean);
  return [];
}

export function clampScore(score: number | undefined): number | undefined {
  if (score === undefined) return undefined;
  if (score <= 10) return Math.round(score * 10 * 10) / 10;
  return Math.max(0, Math.min(100, Math.round(score * 10) / 10));
}

export function encodedName(name: string) {
  return encodeURIComponent(name);
}

export function downloadText(filename: string, content: string, mime = 'text/plain;charset=utf-8') {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function looksLikeMojibake(text: string) {
  if (!text.trim()) return false;
  const suspicious = text.match(/[�ÃÂ]|璇|涓|銆|鍓|湪|槸|殑|妗|瀹|绋|€/g)?.length ?? 0;
  return suspicious >= 3 || suspicious / Math.max(text.length, 1) > 0.08;
}

export function cleanMarkdownText(text: string) {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/^\s{0,3}>\s?/gm, '')
    .replace(/^\s{0,3}#{1,6}\s*/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/[|`*_\[\]]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function extractReportOverview(text: string, maxLength = 520) {
  if (!text.trim()) return '';
  const withoutCode = text.replace(/```[\s\S]*?```/g, '');
  const lines = withoutCode.split(/\r?\n/).map((line) => line.trim());
  const headingIndex = lines.findIndex((line) => /^#{1,4}\s+/.test(line) && /(报告摘要|摘要|overview|summary)/i.test(line));
  let start = headingIndex >= 0 ? headingIndex + 1 : lines.findIndex((line) => line && !/^#{1,6}\s+/.test(line) && !/^[-*_]{3,}$/.test(line));
  if (start < 0) start = 0;
  const collected: string[] = [];
  for (let index = start; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line || /^[-*_]{3,}$/.test(line) || /^>/.test(line)) continue;
    if (/^#{1,4}\s+/.test(line) && collected.length) break;
    if (/^\|/.test(line)) continue;
    collected.push(line);
    const cleaned = cleanMarkdownText(collected.join(' '));
    if (cleaned.length >= maxLength) break;
  }
  const cleaned = cleanMarkdownText(collected.join(' '));
  if (looksLikeMojibake(cleaned)) return '';
  return cleaned.length > maxLength ? `${cleaned.slice(0, maxLength)}...` : cleaned;
}

export function truncateMarkdown(text: string, maxLength = 520) {
  const plain = cleanMarkdownText(text);
  if (looksLikeMojibake(plain)) return '';
  return plain.length > maxLength ? `${plain.slice(0, maxLength)}...` : plain;
}

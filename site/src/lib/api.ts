import { asArray } from './utils';

export async function safeFetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export async function safeFetchText(path: string, fallback = ''): Promise<string> {
  try {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) return fallback;
    const text = await response.text();
    const contentType = response.headers.get('content-type')?.toLowerCase() ?? '';
    const trimmed = text.trimStart().toLowerCase();
    const looksLikeHtmlFallback =
      contentType.includes('text/html') ||
      trimmed.startsWith('<!doctype html') ||
      trimmed.startsWith('<html') ||
      trimmed.includes('<div id="root"');
    return looksLikeHtmlFallback ? fallback : text;
  } catch {
    return fallback;
  }
}

export async function loadSummary(path: string) {
  const raw = await safeFetchJson<unknown>(path, []);
  return asArray<Record<string, unknown>>(raw);
}

export async function loadRepoDetail(repoName: string, scope?: string) {
  const encoded = encodeURIComponent(repoName);
  const targets = scope === 'history'
    ? [`/data/history/${encoded}.json`, `/data/works/${encoded}.json`]
    : [`/data/works/${encoded}.json`, `/data/history/${encoded}.json`];
  for (const path of targets) {
    const detail = await safeFetchJson<Record<string, unknown> | null>(path, null);
    if (detail) return detail;
  }
  return null;
}

export async function loadReports(repoName: string) {
  const encoded = encodeURIComponent(repoName);
  const [description, final] = await Promise.all([
    safeFetchText(`/reports/${encoded}_description.md`, ''),
    safeFetchText(`/reports/${encoded}_final_report.md`, '')
  ]);
  return { description, final };
}

export async function fetchJson(path, fallback) {
  try {
    const res = await fetch(path)
    if (!res.ok) return fallback
    return await res.json()
  } catch (err) {
    console.warn('fetchJson failed:', path, err)
    return fallback
  }
}

export async function fetchText(path, fallback = '') {
  try {
    const res = await fetch(path)
    if (!res.ok) return fallback
    return await res.text()
  } catch (err) {
    console.warn('fetchText failed:', path, err)
    return fallback
  }
}

export function normalizeRepoUrl(value) {
  if (!value) return ''
  let text = String(value).trim().toLowerCase()
  if (text.endsWith('.git')) text = text.slice(0, -4)
  while (text.endsWith('/')) text = text.slice(0, -1)
  return text
}

export function matchWorkByRepoInput(works, input) {
  const normalized = normalizeRepoUrl(input)
  if (!normalized) return null
  return (works || []).find((item) => {
    const repoName = String(item.repo_name || '').toLowerCase()
    return normalizeRepoUrl(item.repo_url) === normalized
      || normalizeRepoUrl(item.normalized_repo_url) === normalized
      || repoName === normalized
      || normalized.endsWith('/' + repoName)
  }) || null
}

export function toNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

export function formatNumber(value, fallback = '暂无数据') {
  if (value === null || value === undefined || value === '') return fallback
  const number = Number(value)
  if (!Number.isFinite(number)) return fallback
  return Number.isInteger(number) ? String(number) : number.toFixed(2).replace(/\.?0+$/, '')
}

export function safeText(value, fallback = '暂无数据') {
  if (value === null || value === undefined) return fallback
  const text = String(value).trim()
  return text ? text : fallback
}

export function scoreLevelLabel(value) {
  const map = {
    high: '高分',
    medium: '中等',
    low: '待完善',
    excellent: '优秀',
    good: '良好',
  }
  return map[String(value || '').toLowerCase()] || safeText(value)
}

export function scoreItems(score) {
  const scores = score?.scores || {}
  return [
    { key: 'originality', name: '原创性', value: toNumber(scores.originality) },
    { key: 'novelty', name: '新颖性', value: toNumber(scores.novelty) },
    { key: 'practicality', name: '可实践性', value: toNumber(scores.practicality) },
    { key: 'difficulty', name: '技术难度', value: toNumber(scores.difficulty) },
    { key: 'completion', name: '完成度', value: toNumber(scores.completion) },
  ]
}

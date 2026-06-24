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

export function scoreItems(score) {
  const scores = score?.scores || {}
  return [
    { key: 'originality', name: '原创性', value: Number(scores.originality || 0) },
    { key: 'novelty', name: '新颖性', value: Number(scores.novelty || 0) },
    { key: 'practicality', name: '可实践性', value: Number(scores.practicality || 0) },
    { key: 'difficulty', name: '技术难度', value: Number(scores.difficulty || 0) },
    { key: 'completion', name: '完成度', value: Number(scores.completion || 0) },
  ]
}

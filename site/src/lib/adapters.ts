import { clampScore, firstPresent, looksLikeMojibake, toDisplay, toList, toNumber } from './utils';
import { levelFromScore } from './score';

export type RepoRecord = Record<string, unknown>;

const repoNameKeys = ['repo_name', 'name', 'id', 'repository', 'repo', 'history_repo_name', 'target_repo_name'];
const teamNameKeys = ['team_name', 'team', '队伍名称'];
const teamCodeKeys = ['team_code', '队伍编号'];
const schoolKeys = ['school', '学校'];
const yearKeys = ['year', '年份'];
const repoUrlKeys = ['repo_url', 'fork_url', 'url', 'normalized_repo_url', 'Fork地址', '仓库地址'];
const scoreKeys = ['overall_score', 'final_score', 'score', 'quality_score', '综合评分'];
const levelKeys = ['level', 'grade', 'score_level', '等级'];
const strengthsKeys = ['strengths', 'advantages', 'target_advantages', '主要优势'];
const weaknessesKeys = ['weaknesses', 'risks', 'target_weaknesses', '主要短板'];
const descriptionKeys = ['description', 'project_description', 'project_summary', '简介', 'summary'];

export function getRepoName(repo: RepoRecord | null | undefined) {
  return toDisplay(firstPresent(repo, repoNameKeys));
}

export function getTeamName(repo: RepoRecord | null | undefined) {
  return toDisplay(firstPresent(repo, teamNameKeys, getRepoName(repo)));
}

export function getTeamCode(repo: RepoRecord | null | undefined) {
  return toDisplay(firstPresent(repo, teamCodeKeys, getRepoName(repo)));
}

export function getSchool(repo: RepoRecord | null | undefined) {
  return toDisplay(firstPresent(repo, schoolKeys));
}

export function getYear(repo: RepoRecord | null | undefined) {
  return toDisplay(firstPresent(repo, yearKeys));
}

export function getScope(repo: RepoRecord | null | undefined) {
  const scope = firstPresent(repo, ['scope', 'dataset', 'type']);
  if (scope) return String(scope);
  const status = String(firstPresent(repo, ['status'], '')).toLowerCase();
  if (status.includes('history')) return 'history';
  return 'target';
}

export function getTrack(repo: RepoRecord | null | undefined) {
  return toDisplay(firstPresent(repo, ['track', '赛道']));
}

export function getRepoUrl(repo: RepoRecord | null | undefined) {
  return toDisplay(firstPresent(repo, repoUrlKeys));
}

export function getScore(repo: RepoRecord | null | undefined) {
  return clampScore(toNumber(firstPresent(repo, scoreKeys)));
}

export function getLevel(repo: RepoRecord | null | undefined) {
  return levelFromScore(getScore(repo), toDisplay(firstPresent(repo, levelKeys), ''));
}

export function getStrengths(repo: RepoRecord | null | undefined) {
  return toList(firstPresent(repo, strengthsKeys));
}

export function getWeaknesses(repo: RepoRecord | null | undefined) {
  return toList(firstPresent(repo, weaknessesKeys));
}

export function getDescription(repo: RepoRecord | null | undefined) {
  const value = firstPresent(repo, descriptionKeys);
  if (typeof value !== 'string') return '暂无项目描述';
  const normalized = value.trim();
  if (!normalized || normalized.length < 12 || looksLikeMojibake(normalized)) return '暂无项目描述';
  return normalized;
}

export function getReportPath(repo: RepoRecord | null | undefined) {
  const name = getRepoName(repo);
  return `/reports/${encodeURIComponent(name)}`;
}

export function getMetric(repo: RepoRecord | null | undefined, keys: string[], fallback = '暂无数据') {
  return toDisplay(firstPresent(repo, keys), fallback);
}

export function getMetricNumber(repo: RepoRecord | null | undefined, keys: string[]) {
  return toNumber(firstPresent(repo, keys));
}

export function normalizeRepo(repo: RepoRecord, scope?: 'target' | 'history'): RepoRecord {
  return { ...repo, scope: scope ?? getScope(repo) };
}

export function hasUsableScore(repo: RepoRecord) {
  return getScore(repo) !== undefined;
}

export function mergeByRepoName(primary: RepoRecord, secondary?: RepoRecord) {
  if (!secondary) return primary;
  return { ...secondary, ...primary };
}

import { levelLabel } from '../../lib/score';
import { cx } from '../../lib/utils';

export function ScoreBadge({ level }: { level: string }) {
  return <span className={cx('badge', `badge--${level.toLowerCase()}`)}>{level} {levelLabel(level)}</span>;
}

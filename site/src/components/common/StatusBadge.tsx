import { cx } from '../../lib/utils';

export function StatusBadge({ status }: { status: string }) {
  return <span className={cx('status-badge', `status-badge--${status}`)}>{status}</span>;
}

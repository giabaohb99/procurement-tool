import type { DataTableColumn } from '@/shared/data-table'

import type { FeatureRow } from '../../types/feature-usage'
import { abandonRate, actionName, formName, screenName, userShare } from '../../utils/feature-usage-format'
import { formatCount, formatDurationMs, formatRatio } from '../../utils/usage-format'

const num = (width = 110) => ({ width, align: 'right' as const, sortable: false })

function usersCell(activeUsers: number) {
  return (r: FeatureRow) => {
    const share = userShare(r.users, activeUsers)
    return (
      <span className="tabular-nums">
        {formatCount(r.users)}
        {share != null && <span className="ml-1 text-xs text-muted-foreground">({formatRatio(share)})</span>}
      </span>
    )
  }
}

/** Cột "Chức năng" (bấm nút): tên · màn · người dùng · lượt. */
export function buildActionColumns(activeUsers: number): DataTableColumn<FeatureRow>[] {
  return [
    { key: 'name', header: 'Chức năng', hideable: false, wrap: true, cell: (r) => actionName(r.code) },
    { key: 'route', header: 'Màn hình', wrap: true, cell: (r) => (r.route ? screenName(r.route) : '') },
    { key: 'users', header: 'Số người dùng', ...num(150), cell: usersCell(activeUsers) },
    { key: 'uses', header: 'Số lần', ...num(), cell: (r) => <span className="tabular-nums">{formatCount(r.uses)}</span> },
  ]
}

/** Cột "Biểu mẫu": mở · gửi · bỏ dở · tỷ lệ bỏ dở · thời gian gửi trung bình. */
export function buildFormColumns(activeUsers: number): DataTableColumn<FeatureRow>[] {
  return [
    { key: 'name', header: 'Biểu mẫu', hideable: false, wrap: true, cell: (r) => formName(r.code) },
    { key: 'users', header: 'Số người dùng', ...num(150), cell: usersCell(activeUsers) },
    { key: 'opens', header: 'Lượt mở', ...num(), cell: (r) => <span className="tabular-nums">{formatCount(r.uses)}</span> },
    { key: 'submits', header: 'Đã gửi', ...num(), cell: (r) => <span className="tabular-nums">{formatCount(r.completes)}</span> },
    { key: 'abandons', header: 'Bỏ dở', ...num(), cell: (r) => <span className="tabular-nums">{formatCount(r.abandons)}</span> },
    {
      key: 'abandon_rate',
      header: 'Tỷ lệ bỏ dở',
      ...num(),
      cell: (r) => <span className="tabular-nums">{formatRatio(abandonRate(r))}</span>,
    },
    {
      key: 'avg_submit',
      header: 'Thời gian gửi (TB)',
      ...num(150),
      cell: (r) => (r.completes > 0 ? formatDurationMs(r.duration_ms / r.completes) : ''),
    },
  ]
}

/** Cột "Màn hình": lượt xem · người xem · thời gian ở lại trung bình. */
export function buildScreenColumns(activeUsers: number): DataTableColumn<FeatureRow>[] {
  return [
    { key: 'route', header: 'Màn hình', hideable: false, wrap: true, cell: (r) => screenName(r.route) },
    { key: 'users', header: 'Số người xem', ...num(150), cell: usersCell(activeUsers) },
    { key: 'uses', header: 'Lượt xem', ...num(), cell: (r) => <span className="tabular-nums">{formatCount(r.uses)}</span> },
    {
      key: 'dwell',
      header: 'Ở lại (TB)',
      ...num(),
      cell: (r) => (r.uses > 0 && r.duration_ms > 0 ? formatDurationMs(r.duration_ms / r.uses) : ''),
    },
  ]
}

/** Cột "Lỗi giao diện" theo màn: số lỗi · số người gặp. */
export function buildErrorColumns(): DataTableColumn<FeatureRow>[] {
  return [
    { key: 'route', header: 'Màn hình', hideable: false, wrap: true, cell: (r) => screenName(r.route) },
    { key: 'users', header: 'Số người gặp lỗi', ...num(150), cell: (r) => <span className="tabular-nums">{formatCount(r.users)}</span> },
    { key: 'uses', header: 'Số lỗi', ...num(), cell: (r) => <span className="tabular-nums">{formatCount(r.uses)}</span> },
  ]
}

/** Cột "Tìm kiếm" theo màn: lượt tìm · lượt không ra kết quả. */
export function buildSearchColumns(): DataTableColumn<FeatureRow>[] {
  return [
    { key: 'route', header: 'Màn hình', hideable: false, wrap: true, cell: (r) => screenName(r.route) },
    { key: 'users', header: 'Số người tìm', ...num(150), cell: (r) => <span className="tabular-nums">{formatCount(r.users)}</span> },
    { key: 'uses', header: 'Lượt tìm', ...num(), cell: (r) => <span className="tabular-nums">{formatCount(r.uses)}</span> },
    {
      key: 'empty',
      header: 'Không ra kết quả',
      ...num(150),
      cell: (r) => <span className="tabular-nums">{r.uses > 0 ? formatRatio(r.fails / r.uses) : ''}</span>,
    },
  ]
}

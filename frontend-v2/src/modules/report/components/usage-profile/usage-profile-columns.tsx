import { Badge } from '@/shared/ui/badge'
import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'

import { styleLabel } from '../../config/usage-style-hints'
import type { UsageProfileRow } from '../../types/usage-profile'
import { formatCount, formatRatio } from '../../utils/usage-format'

/** Cột bảng danh sách hồ sơ (phải bọc `useMemo` ở nơi dùng). */
export function buildUsageProfileColumns(): DataTableColumn<UsageProfileRow>[] {
  return [
    {
      key: 'full_name',
      header: 'Họ tên / Mã',
      width: 220,
      hideable: false,
      defaultPinned: true,
      cell: (r) => (
        <div className="min-w-0">
          <div className="truncate font-medium">{r.full_name}</div>
          <div className="truncate text-xs text-muted-foreground">{r.emp_code}</div>
        </div>
      ),
    },
    { key: 'department', header: 'Phòng', width: 160, cell: (r) => r.department_name },
    { key: 'cohort', header: 'Nhóm so sánh', width: 180, cell: (r) => (r.cohort ? `${r.cohort.name} (${r.cohort.size})` : null) },
    {
      key: 'active',
      header: 'Ngày vào / làm việc',
      width: 170,
      align: 'right',
      cell: (r) => (
        <span className="tabular-nums">
          {formatCount(r.active_days)} / {formatCount(r.workdays_net)} ({formatRatio(r.active_ratio)})
        </span>
      ),
    },
    { key: 'api_writes', header: 'Lượt ghi', width: 100, align: 'right', cell: (r) => formatCount(r.api_writes) },
    { key: 'docs_created', header: 'Phiếu lập', width: 100, align: 'right', cell: (r) => formatCount(r.docs_created) },
    { key: 'approvals', header: 'Lượt duyệt', width: 100, align: 'right', cell: (r) => formatCount(r.approvals) },
    { key: 'exports', header: 'Xuất', width: 80, align: 'right', cell: (r) => formatCount(r.exports) },
    {
      key: 'http_422',
      header: 'Lỗi nhập/100',
      width: 120,
      align: 'right',
      cell: (r) => formatCount(r.http_422_per_100_writes),
    },
    {
      key: 'labels',
      header: 'Kiểu',
      width: 240,
      wrap: true,
      cell: (r) => (
        <div className="flex flex-wrap gap-1">
          {r.labels.map((l) => (
            <Badge key={l.code} variant="secondary">
              {styleLabel(l.code)}
            </Badge>
          ))}
        </div>
      ),
    },
    { key: 'last_active_day', header: 'Hoạt động gần nhất', width: 150, cell: (r) => (r.last_active_day ? formatDate(r.last_active_day) : null) },
  ]
}

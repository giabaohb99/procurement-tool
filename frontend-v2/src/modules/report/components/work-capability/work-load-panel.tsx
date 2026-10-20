import { useMemo } from 'react'

import { extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Card } from '@/shared/ui/card'

import { useWorkLoad } from '../../hooks/use-work-capability'
import type { WorkLoadRow } from '../../types/work-capability'
import { formatCount } from '../../utils/usage-format'

const num = (width = 110) => ({ width, align: 'right' as const, sortable: false })
const n = (v: number) => <span className="tabular-nums">{formatCount(v)}</span>

/** Một số + «(x quá hạn)» khi có việc quá hạn — để người đọc thấy ngay chỗ nghẽn mà không phải cộng thêm cột. */
const withOverdue = (v: number, over: number) => (
  <span className="tabular-nums">
    {formatCount(v)}
    {over > 0 && <span className="ml-1 text-xs text-destructive">({formatCount(over)} quá hạn)</span>}
  </span>
)

const COLUMNS: DataTableColumn<WorkLoadRow>[] = [
  {
    key: 'person',
    header: 'Người',
    hideable: false,
    wrap: true,
    cell: (r) => (
      <span>
        {r.full_name} <span className="text-xs text-muted-foreground">({r.employee_code})</span>
        {r.on_leave_today && <span className="ml-1 text-xs text-amber-600">đang nghỉ</span>}
      </span>
    ),
  },
  { key: 'approvals', header: 'Duyệt chờ', ...num(150), cell: (r) => withOverdue(r.approvals_pending, r.approvals_overdue) },
  { key: 'work', header: 'Việc dự án', ...num(150), cell: (r) => withOverdue(r.work_open, r.work_overdue) },
  { key: 'hours', header: 'Giờ ước lượng', ...num(), cell: (r) => n(r.work_estimate_hours_open) },
  { key: 'pr', header: 'YCMH đang xử lý', ...num(130), cell: (r) => n(r.pr_handling) },
  { key: 'po', header: 'ĐMH đang xử lý', ...num(130), cell: (r) => n(r.po_handling) },
  { key: 'sr', header: 'Dòng báo giá', ...num(), cell: (r) => n(r.survey_lines_handling) },
  { key: 'docs', header: 'Văn bản chờ phát hành', ...num(150), defaultHidden: true, cell: (r) => n(r.docs_pending_issue) },
  { key: 'pr_wait', header: 'YCMH chờ duyệt (trưởng phòng)', ...num(170), defaultHidden: true, cell: (r) => n(r.pr_approval_pending) },
  { key: 'deleg', header: 'Được ủy quyền', ...num(), defaultHidden: true, cell: (r) => n(r.delegated_in) },
  { key: 'leave', header: 'Ngày nghỉ sắp tới', ...num(130), defaultHidden: true, cell: (r) => n(r.leave_days_ahead) },
  { key: 'total', header: 'Tổng đếm thô', ...num(), cell: (r) => <span className="font-medium tabular-nums">{formatCount(r.open_items_total)}</span> },
]

/**
 * Tải đang ôm tính tức thì (D1c) — các số THÀNH PHẦN, không quy ra một điểm. «Tổng đếm thô» chỉ là tổng số đầu việc,
 * không nói việc nặng hay nhẹ. Cần chọn pháp nhân hoặc phòng ban: máy chủ không trả cả công ty khi không nói rõ.
 */
export function WorkLoadPanel({ params }: { params: Record<string, string> | null }) {
  const { data, isLoading, isError, error } = useWorkLoad(params)
  const rows = useMemo(() => [...(data?.items ?? [])].sort((a, b) => b.open_items_total - a.open_items_total), [data])
  if (!params) {
    return (
      <Card className="p-4 text-sm text-muted-foreground">Chọn một pháp nhân hoặc một phòng ban để xem tải đang ôm của từng người.</Card>
    )
  }
  return (
    <Card className="p-4">
      <DataTable
        columns={COLUMNS}
        rows={rows}
        getRowId={(r) => String(r.employee_id)}
        isLoading={isLoading}
        isError={isError}
        errorMessage={isError ? extractErrorMessage(error) : undefined}
        emptyMessage="Không có nhân sự nào trong phạm vi này."
        storageKey="report.work-capability.load"
      />
    </Card>
  )
}

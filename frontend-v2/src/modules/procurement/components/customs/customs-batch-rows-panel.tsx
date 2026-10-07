import { useMemo, useState } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

import { useCustomsBatchRows, useCustomsBatchRowSummary } from '../../hooks/use-customs-saved-filters'
import { CUSTOMS_ROW_STATUS, type CustomsBatchRow } from '../../types/customs-saved-filter'

const PAGE_SIZE = 50

/**
 * Nhãn + màu từng kết cục — khớp `ImportRowStatus` backend
 * (1 Thêm mới · 2 Lỗi · 3 Trùng trong tệp · 4 Đã có · bao-CR-608: 5 Ghi đè · 6 Xóa · 7 Bỏ qua).
 */
const ROW_STATUS_META: Record<number, { label: string; tone: string }> = {
  [CUSTOMS_ROW_STATUS.NEW]: { label: 'Thêm mới', tone: TONE_CLASS.done },
  [CUSTOMS_ROW_STATUS.ERROR]: { label: 'Lỗi', tone: TONE_CLASS.danger },
  [CUSTOMS_ROW_STATUS.DUPLICATE]: { label: 'Trùng trong tệp', tone: TONE_CLASS.pending },
  [CUSTOMS_ROW_STATUS.EXISTING]: { label: 'Đã có', tone: TONE_CLASS.neutral },
  [CUSTOMS_ROW_STATUS.UPDATED]: { label: 'Ghi đè', tone: TONE_CLASS.progress },
  [CUSTOMS_ROW_STATUS.DELETED]: { label: 'Xóa', tone: TONE_CLASS.danger },
  [CUSTOMS_ROW_STATUS.IGNORED]: { label: 'Bỏ qua', tone: TONE_CLASS.pending },
}

/** bao-CR-608 — ba kết cục chỉ có khi tệp có cột «ID» / «Thao tác»: ô đếm 0 thì không hiện cho đỡ rối. */
const OPTIONAL_CHIPS = [
  { value: CUSTOMS_ROW_STATUS.UPDATED, key: 'updated' },
  { value: CUSTOMS_ROW_STATUS.DELETED, key: 'deleted' },
  { value: CUSTOMS_ROW_STATUS.IGNORED, key: 'ignored' },
] as const

/**
 * Hộp «Nhật ký lô» theo TỪNG DÒNG của tệp — bao-CR-496 (F01, ghi chú 25/09 của chị Mi).
 *
 * Đầu hộp là tổng theo kết cục, bấm vào một ô là lọc; bảng liệt kê đủ MỌI dòng dữ liệu (không
 * chỉ dòng có cảnh báo như nhật ký cũ). bao-CR-541: «Trùng trong tệp» và «Đã có» là dòng BỎ
 * QUA, không ghi vào bảng giá; dòng «Thêm mới» nghi sửa giá thì câu ghi chú nói rõ để rà.
 */
interface CustomsBatchRowsPanelProps {
  batchId: number
  className?: string
}

export function CustomsBatchRowsPanel({ batchId, className }: CustomsBatchRowsPanelProps) {
  const [status, setStatus] = useState<number | undefined>(undefined)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)
  const summary = useCustomsBatchRowSummary(batchId)
  const rows = useCustomsBatchRows(batchId, { page, page_size: pageSize, row_status: status })

  const columns = useMemo<DataTableColumn<CustomsBatchRow>[]>(
    () => [
      { key: 'row_no', header: 'Dòng', width: 80, align: 'right', hideable: false, cell: (x) => x.row_no || '—' },
      {
        key: 'row_status',
        header: 'Kết cục',
        width: 130,
        hideable: false,
        cell: (x) => {
          const meta = ROW_STATUS_META[x.row_status]
          return (
            <Badge className={cn(meta?.tone ?? TONE_CLASS.neutral)}>
              {meta?.label ?? x.row_status_label}
            </Badge>
          )
        },
      },
      { key: 'product_name', header: 'Tên hàng', width: 320, wrap: true, cell: (x) => x.product_name || '—' },
      { key: 'message', header: 'Ghi chú', width: 360, wrap: true, cell: (x) => x.message },
    ],
    [],
  )

  function pickStatus(next: number | undefined) {
    setStatus(next)
    setPage(1)
  }

  const counts = summary.data
  const chips: { value: number | undefined; label: string; count: number }[] = counts
    ? [
        { value: undefined, label: 'Tất cả', count: counts.total },
        { value: CUSTOMS_ROW_STATUS.NEW, label: ROW_STATUS_META[CUSTOMS_ROW_STATUS.NEW].label, count: counts.new },
        { value: CUSTOMS_ROW_STATUS.ERROR, label: ROW_STATUS_META[CUSTOMS_ROW_STATUS.ERROR].label, count: counts.error },
        {
          value: CUSTOMS_ROW_STATUS.DUPLICATE,
          label: ROW_STATUS_META[CUSTOMS_ROW_STATUS.DUPLICATE].label,
          count: counts.duplicate,
        },
        {
          value: CUSTOMS_ROW_STATUS.EXISTING,
          label: ROW_STATUS_META[CUSTOMS_ROW_STATUS.EXISTING].label,
          count: counts.existing ?? 0,
        },
        ...OPTIONAL_CHIPS.filter((chip) => (counts[chip.key] ?? 0) > 0).map((chip) => ({
          value: chip.value,
          label: ROW_STATUS_META[chip.value].label,
          count: counts[chip.key] ?? 0,
        })),
      ]
    : []

  return (
    <div className={cn('flex min-h-0 flex-col gap-3', className)}>
      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Lọc theo kết cục">
        {chips.map((chip) => (
          <button
            key={chip.label}
            type="button"
            aria-pressed={status === chip.value}
            onClick={() => pickStatus(chip.value)}
            className={cn(
              'rounded-full border px-3 py-1 text-xs',
              status === chip.value ? 'border-primary bg-primary/10 font-medium' : 'border-border text-muted-foreground',
            )}
          >
            {chip.label}: {chip.count.toLocaleString('vi-VN')}
          </button>
        ))}
        {counts && counts.total === 0 && (
          <span className="text-xs text-muted-foreground">
            Lô này nạp trước khi có nhật ký từng dòng — xem thẻ «Ghi chú lỗi / cảnh báo».
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <DataTable
          columns={columns}
          rows={rows.data?.items}
          getRowId={(x) => x.id}
          isLoading={rows.isLoading}
          isError={rows.isError}
          emptyMessage={status ? 'Không có dòng nào mang kết cục này.' : 'Lô này chưa có nhật ký từng dòng.'}
          pagination={{
            page,
            pageSize,
            total: rows.data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: (size) => {
              setPageSize(size)
              setPage(1)
            },
            unitLabel: 'dòng',
          }}
        />
      </div>
    </div>
  )
}

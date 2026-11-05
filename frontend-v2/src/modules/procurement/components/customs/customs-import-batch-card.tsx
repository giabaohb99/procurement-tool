import type { ReactNode } from 'react'

import { formatDate, formatDateTime } from '@/shared/utils/format-date'

import {
  CUSTOMS_BATCH_MODE_LABELS,
  CUSTOMS_BATCH_STATUS,
  type CustomsImportBatch,
} from '../../types/customs'
import { CustomsBatchStatusBadge } from './customs-batch-status-badge'

/**
 * Thẻ dùng ở đâu: `history` = thẻ Lịch sử nạp (lô đã xong, có người nạp + giờ); `dryRun` /
 * `apply` = bảng kết quả trong hộp Nạp tệp, lúc chạy thử và lúc ghi thật — nhãn số đổi theo
 * đúng tiêu đề cột của bảng ở đó ("Dòng mới" / "Đã thêm"…).
 */
export type CustomsImportBatchCardContext = 'history' | 'dryRun' | 'apply'

interface Stat {
  label: string
  value: string | number
}

/** Các con số của lô, đúng thứ tự và đúng nhãn của cột bảng tương ứng. */
function buildStats(batch: CustomsImportBatch, context: CustomsImportBatchCardContext): Stat[] {
  if (context === 'history') {
    return [
      { label: 'Thêm mới', value: batch.created_count },
      { label: 'Ghi đè', value: batch.updated_count || 0 },
      { label: 'Xóa', value: batch.deleted_count || 0 },
      { label: 'Bỏ qua (trùng)', value: (batch.existing_rows || 0) + (batch.duplicate_rows || 0) },
      { label: 'Vá ngày', value: batch.date_fixed || 0 },
    ]
  }
  //  Lô chưa chạy xong thì chưa có số — gạch ngang như ô của bảng, đừng in 0 (đọc thành "không có").
  const done = batch.status === CUSTOMS_BATCH_STATUS.done
  const count = (value: number | undefined) => (done ? value || 0 : '—')
  const applying = context === 'apply'
  return [
    { label: applying ? 'Đã thêm' : 'Dòng mới', value: count(batch.created_count) },
    { label: applying ? 'Đã ghi đè' : 'Ghi đè', value: count(batch.updated_count) },
    { label: applying ? 'Đã xóa' : 'Xóa', value: count(batch.deleted_count) },
    { label: 'Đã có', value: count(batch.existing_rows) },
    { label: 'Trùng trong tệp', value: count(batch.duplicate_rows) },
    { label: 'Đã vá ngày', value: batch.date_fixed || 0 },
    { label: 'Cảnh báo', value: batch.warning_count || 0 },
  ]
}

interface CustomsImportBatchCardProps {
  batch: CustomsImportBatch
  context: CustomsImportBatchCardContext
  /** Nút thao tác của lô (tải tệp, nhật ký, hoàn tác) — chỉ thẻ Lịch sử nạp có. */
  actions?: ReactNode
}

/**
 * Một LÔ NẠP tệp GTT02 ở khổ điện thoại — dùng chung cho bảng Lịch sử nạp (14 cột) và bảng kết
 * quả trong hộp Nạp tệp (10 cột): cùng một kiểu bản ghi, chỉ khác bộ số bày ra.
 *
 * ⚠️ **Tên tệp lên đầu, ngắt được ở bất kỳ ký tự nào** (`break-all`): tên tệp hải quan dài liền
 * một mạch không dấu cách, để mặc định thì nó đẩy cả thẻ tràn ngang.
 *
 * ⚠️ **Các con số xếp lưới hai cột NHÃN – SỐ**, không nối thành một câu "· ": bảy con số nối
 * nhau trên khung 322px rớt dòng giữa chừng một cặp nhãn – số, đọc ra số của nhãn khác.
 *
 * Hai bảng này không khai `onRowClick` nên thẻ là `<div>` và nút thao tác nằm được bên trong.
 */
export function CustomsImportBatchCard({ batch, context, actions }: CustomsImportBatchCardProps) {
  const range = batch.date_from
    ? `${formatDate(batch.date_from)} → ${formatDate(batch.date_to)}`
    : '—'
  const meta =
    context === 'history'
      ? [
          `Lô #${batch.id}`,
          CUSTOMS_BATCH_MODE_LABELS[batch.mode],
          batch.created_by_name,
          formatDateTime(batch.finished_at || batch.created_at),
        ].filter(Boolean)
      : []

  return (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0 font-medium break-all text-foreground">{batch.filename}</span>
        <span className="shrink-0">
          <CustomsBatchStatusBadge batch={batch} />
        </span>
      </div>

      {meta.length > 0 && <p className="text-xs text-muted-foreground">{meta.join(' · ')}</p>}
      <p className="text-xs text-muted-foreground">
        Khoảng ngày <span className="tabular-nums text-foreground">{range}</span>
      </p>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs">
        {buildStats(batch, context).map((stat) => (
          <div key={stat.label} className="flex justify-between gap-2">
            <dt className="text-muted-foreground">{stat.label}</dt>
            <dd className="tabular-nums">{stat.value}</dd>
          </div>
        ))}
      </dl>

      {actions && <div className="flex items-center justify-end gap-1">{actions}</div>}
    </div>
  )
}

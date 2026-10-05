import type { DataTableColumn } from '@/shared/data-table'
import { WORK_EVENT_TYPE, labelOf } from '@/shared/constants/statuses'
import { formatDate } from '@/shared/utils/format-date'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { workHistorySummaryLine } from '../utils/employee-work-history-display'
import { renderFileCell } from './employee-work-history-columns'

interface BuildEmployeeWorkHistoryDecisionColumnsOptions {
  /** A9 (Q4) — mở được tệp hay chỉ thấy số lượng, cùng luật với bảng chính. */
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
}

/**
 * Cột của bảng khu «Quyết định bổ nhiệm» (đại ca chốt 03/10/2026) — lọc từ
 * CÙNG nguồn dữ liệu quá trình công tác, chỉ các dòng có `decision_no`.
 *
 * Bộ cột khác hẳn bảng quá trình công tác đầy đủ
 * (`employee-work-history-columns.tsx`): không có Đến ngày/Thao tác — khu này
 * CHỈ ĐỌC, ghi vẫn làm ở khu «Quá trình công tác» phía dưới — và gộp ba trường
 * phòng ban/chức vụ/pháp nhân vào một cột «Nội dung tóm tắt» cho đúng yêu cầu.
 */
export function buildEmployeeWorkHistoryDecisionColumns({
  canOpenFiles,
  onOpenFiles,
}: BuildEmployeeWorkHistoryDecisionColumnsOptions): DataTableColumn<EmployeeWorkHistory>[] {
  return [
    {
      key: 'decision_no',
      header: 'Số QĐ',
      width: 140,
      hideable: false,
      cell: (row) => row.decision_no,
    },
    {
      key: 'decision_date',
      header: 'Ngày ký QĐ',
      width: 130,
      cell: (row) => formatDate(row.decision_date) || '—',
    },
    {
      key: 'event_type',
      header: 'Loại',
      width: 140,
      cell: (row) => labelOf(WORK_EVENT_TYPE, String(row.event_type)),
    },
    {
      key: 'summary',
      header: 'Nội dung tóm tắt',
      width: 280,
      wrap: true,
      cell: (row) => workHistorySummaryLine(row) || '—',
    },
    {
      key: 'from_date',
      header: 'Hiệu lực từ',
      width: 130,
      cell: (row) => formatDate(row.from_date),
    },
    {
      key: 'files',
      header: 'Tệp',
      width: 160,
      cell: (row) => renderFileCell({ row, canOpenFiles, onOpenFiles }),
    },
  ]
}

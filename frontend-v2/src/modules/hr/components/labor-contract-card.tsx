import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { formatMoney } from '@/shared/utils/format-money'
import { formatContractPeriod } from '../config/employee-labor-contract-columns'
import type { LaborContract } from '../types/labor-contract'
import { LaborContractRowActions, type LaborContractRowActionHandlers } from './labor-contract-row-actions'
import { LaborContractStatusBadge } from './labor-contract-status-badge'

interface LaborContractCardProps extends LaborContractRowActionHandlers {
  row: LaborContract
  /** Đang có lệnh chạy trên hợp đồng này — khóa nút thao tác, cùng nghĩa với cột Thao tác. */
  busy: boolean
  canReadSigned: boolean
}

/**
 * Một hợp đồng lao động ở tab "Hợp đồng" của hồ sơ, khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Số HĐ lên đầu, mã hệ thống xuống dòng phụ (sky).** Phòng Nhân sự gọi hợp đồng bằng số in
 * trên giấy; mã `HDLD…` chỉ hiện khi đã có số để không in một thứ hai lần.
 *
 * ⚠️ **Nút "⋯" là ANH EM của khối chữ, không nằm trong nó.** Bảng không có `onRowClick` nên thẻ
 * là `<div>` thường, nút đứng cạnh — dùng lại ĐÚNG `LaborContractRowActions` của bảng (menu Xem /
 * Soạn / Trạng thái / Xóa, hiện theo cờ backend) để mọi việc làm được ở bảng làm được ở thẻ.
 *
 * Lương bày nguyên số, không rút gọn: tab này chỉ dựng khi người xem có `labor_contract.read`
 * (trang cha gác) — cùng luật với cột Lương cơ bản của bảng, không che thêm, không mở thêm.
 * Dòng tệp (bảng ẩn mặc định) hiện ở thẻ vì thẻ không có menu "Cột" để bật lại.
 */
export function LaborContractCard({ row, busy, canReadSigned, ...handlers }: LaborContractCardProps) {
  const typeLabel = labelOf(LABOR_CONTRACT_TYPE, String(row.contract_type))

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="min-w-0 truncate font-medium text-foreground">{row.contract_no || row.code}</span>
          <LaborContractStatusBadge status={row.effective_status} />
        </div>

        {row.contract_no && (
          <p className="truncate font-mono text-xs text-sky-600 dark:text-sky-400">{row.code}</p>
        )}

        <p className="truncate text-sm text-muted-foreground">
          {[typeLabel, row.job_title].filter(Boolean).join(' · ') || '—'}
        </p>

        <p className="text-xs text-muted-foreground tabular-nums">
          Hiệu lực: {formatContractPeriod(row.start_date, row.end_date)}
        </p>

        <p className="text-xs text-muted-foreground">
          Lương cơ bản{' '}
          <span className="text-sm font-semibold text-foreground tabular-nums">{formatMoney(row.base_salary)}</span>
        </p>

        <p className="text-xs text-muted-foreground">
          {row.has_generated_file ? 'Đã sinh tệp' : 'Chưa sinh tệp'}
          <span aria-hidden="true"> · </span>
          {row.has_signed_file ? 'Có bản ký' : 'Chưa có bản ký'}
        </p>
      </div>

      <div className="shrink-0">
        <LaborContractRowActions row={row} busy={busy} canReadSigned={canReadSigned} {...handlers} />
      </div>
    </div>
  )
}

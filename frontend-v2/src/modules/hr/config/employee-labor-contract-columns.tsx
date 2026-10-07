import type { DataTableColumn } from '@/shared/data-table'
import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { LaborContractRowActions, type LaborContractRowActionHandlers } from '../components/labor-contract-row-actions'
import { LaborContractStatusBadge } from '../components/labor-contract-status-badge'
import type { LaborContract } from '../types/labor-contract'

export interface LaborContractColumnOptions extends LaborContractRowActionHandlers {
  isBusy: (row: LaborContract) => boolean
  canReadSigned: boolean
}

/** «01/01/2026 – 31/12/2026»; HĐ không xác định thời hạn: «từ 01/01/2026». */
export function formatContractPeriod(start: string, end: string | null): string {
  return end ? `${formatDate(start)} – ${formatDate(end)}` : `Từ ${formatDate(start)}`
}

/** Cột bảng tab «Hợp đồng». Là hàm vì cột Thao tác cần callback; nơi gọi bọc `useMemo`. */
export function buildEmployeeLaborContractColumns(
  options: LaborContractColumnOptions,
): DataTableColumn<LaborContract>[] {
  const { isBusy, canReadSigned, ...handlers } = options
  return [
    {
      key: 'contract_no',
      header: 'Số HĐ',
      width: 150,
      hideable: false,
      wrap: true,
      cell: (r) => (
        <span>
          {r.contract_no || r.code}
          {r.contract_no && <span className="block text-xs text-muted-foreground">{r.code}</span>}
        </span>
      ),
    },
    //  Đứng ngay sau Số HĐ: ở khổ laptop 1440px bảng phải cuộn ngang, cột Thao tác ghim phải sẽ đè
    //  lên cột cuối — trạng thái là thứ HR cần thấy nhất nên không được nằm ở đó (test Chrome 06/10).
    {
      key: 'status',
      header: 'Trạng thái',
      width: 180,
      cell: (r) => <LaborContractStatusBadge status={r.effective_status} />,
    },
    {
      key: 'contract_type',
      header: 'Loại',
      width: 130,
      wrap: true,
      cell: (r) => labelOf(LABOR_CONTRACT_TYPE, String(r.contract_type)) || '—',
    },
    {
      key: 'period',
      header: 'Hiệu lực',
      width: 190,
      cell: (r) => formatContractPeriod(r.start_date, r.end_date),
    },
    { key: 'job_title', header: 'Chức danh', width: 130, wrap: true, cell: (r) => r.job_title },
    {
      key: 'base_salary',
      header: 'Lương cơ bản',
      width: 130,
      align: 'right',
      cell: (r) => formatMoney(r.base_salary),
    },
    {
      key: 'files',
      header: 'Tệp',
      width: 150,
      //  Ẩn mặc định để bảng vừa khung hồ sơ (~1200px) mà cột Thao tác ghim phải không đè lên
      //  cột Trạng thái; tình trạng tệp đã lộ qua các nút tải/xem ở cột Thao tác.
      defaultHidden: true,
      cell: (r) => (
        <span className="text-xs">
          {r.has_generated_file ? 'Đã sinh' : 'Chưa sinh'}
          <span className="text-muted-foreground"> · </span>
          {r.has_signed_file ? 'Có bản ký' : 'Chưa có bản ký'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Thao tác',
      //  Đủ 7 nút của HĐ nháp đã sinh tệp (sửa · sinh · tải · tải bản ký · ký · hủy · xóa) trên một dòng.
      width: 270,
      hideable: false,
      stickyRight: true,
      cell: (r) => (
        <LaborContractRowActions row={r} busy={isBusy(r)} canReadSigned={canReadSigned} {...handlers} />
      ),
    },
  ]
}

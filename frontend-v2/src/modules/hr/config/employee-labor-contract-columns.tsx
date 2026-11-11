import type { DataTableColumn } from '@/shared/data-table'
import { LABOR_CONTRACT_STATUS, LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import type { CellGetters } from '@/shared/utils/sort-rows-by-cell'
import { getStatusRank } from '@/shared/utils/status-rank'
import { LaborContractRowActions, type LaborContractRowActionHandlers } from '../components/labor-contract-row-actions'
import { LaborContractStatusBadge } from '../components/labor-contract-status-badge'
import type { LaborContract } from '../types/labor-contract'

export interface LaborContractColumnOptions extends LaborContractRowActionHandlers {
  isBusy: (row: LaborContract) => boolean
  canReadSigned: boolean
}

/** "01/01/2026 – 31/12/2026"; HĐ không xác định thời hạn: "từ 01/01/2026". */
export function formatContractPeriod(start: string, end: string | null): string {
  return end ? `${formatDate(start)} – ${formatDate(end)}` : `Từ ${formatDate(start)}`
}

/**
 * Giá trị đem xếp của từng cột bảng tab "Hợp đồng" (duoc-CR-748) — bảng nạp ĐỦ mọi hợp đồng của một người nên xếp
 * ở trình duyệt (`sortRowsByCell`). Mỗi khóa xếp theo đúng thứ ô đang hiện:
 * - Số HĐ: số HĐ, chưa có số thì mã phiếu (ô hiện đúng chữ đó);
 * - Trạng thái: theo DÒNG ĐỜI (Nháp → Đã ký → Hết hạn → Chấm dứt → Hủy) của `effective_status` — trạng thái
 *   đang hiện, có "Hết hạn" suy ra — không theo chữ cái;
 * - Loại: theo thứ tự khai của bộ mã (Thử việc → Xác định thời hạn → …), như Hình thức / Cấp bậc ở danh sách
 *   nhân sự; Hiệu lực: ngày bắt đầu.
 * - Lương cơ bản: theo SỐ. Cho xếp được vì tab chỉ dựng khi người xem có `labor_contract.read`, và
 *   `/api/employees/{id}/labor-contracts` trả số thật (không che) cho người có quyền đó — người xem luôn ĐANG
 *   thấy con số, thứ tự không lộ thêm gì. Đổi sang che lương ở bảng này thì phải tắt `sortable` của cột lương.
 * Cột không có trong bảng này (Tệp, Thao tác) thì không xếp.
 */
export const EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS: CellGetters<LaborContract> = {
  contract_no: (r) => r.contract_no || r.code,
  status: (r) => getStatusRank(LABOR_CONTRACT_STATUS, String(r.effective_status)),
  contract_type: (r) => getStatusRank(LABOR_CONTRACT_TYPE, String(r.contract_type)),
  period: (r) => r.start_date,
  job_title: (r) => r.job_title,
  base_salary: (r) => r.base_salary,
}

/** Cột bảng tab "Hợp đồng". Là hàm vì cột Thao tác cần callback; nơi gọi bọc `useMemo`. */
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
      sortable: true,
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
      sortable: true,
      cell: (r) => <LaborContractStatusBadge status={r.effective_status} />,
    },
    {
      key: 'contract_type',
      header: 'Loại',
      width: 130,
      wrap: true,
      sortable: true,
      cell: (r) => labelOf(LABOR_CONTRACT_TYPE, String(r.contract_type)) || '—',
    },
    {
      key: 'period',
      header: 'Hiệu lực',
      width: 190,
      sortable: true,
      //  Cột thời gian: nhịp đầu là hợp đồng MỚI NHẤT trước.
      sortDescFirst: true,
      cell: (r) => formatContractPeriod(r.start_date, r.end_date),
    },
    { key: 'job_title', header: 'Chức danh', width: 130, wrap: true, sortable: true, cell: (r) => r.job_title },
    {
      key: 'base_salary',
      header: 'Lương cơ bản',
      width: 130,
      align: 'right',
      //  Xem chú thích `EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS`: chỉ đúng chừng nào bảng còn bày số thật.
      sortable: true,
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
      //  MỘT nút icon "⋯" mở menu icon + chữ (duoc-CR-633) — không còn dãy 7-8 icon trơn.
      width: 80,
      hideable: false,
      stickyRight: true,
      cell: (r) => (
        <LaborContractRowActions row={r} busy={isBusy(r)} canReadSigned={canReadSigned} {...handlers} />
      ),
    },
  ]
}

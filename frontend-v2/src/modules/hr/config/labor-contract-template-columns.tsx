import type { DataTableColumn } from '@/shared/data-table'
import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { LaborContractTemplateRowActions } from '../components/labor-contract-template-row-actions'
import type { LaborContractTemplate } from '../types/labor-contract'

export interface LaborContractTemplateColumnActions {
  canWrite: boolean
  canDelete: boolean
  onDownload: (template: LaborContractTemplate) => void
  /** duoc-CR-606 — mở trang soạn nội dung trên web (người chỉ có quyền đọc vẫn mở xem được). */
  onEditContent: (template: LaborContractTemplate) => void
  /** duoc-CR-606 — hộp sửa tên / loại HĐ / ghi chú. */
  onEditInfo: (template: LaborContractTemplate) => void
  onReplaceFile: (template: LaborContractTemplate) => void
  onToggleActive: (template: LaborContractTemplate) => void
  onDelete: (template: LaborContractTemplate) => void
}

/**
 * Cột bảng "Mẫu hợp đồng". Là hàm vì cột "Thao tác" cần các callback của trang;
 * trang phải bọc kết quả bằng `useMemo`. Nút bị ẨN theo quyền ở đây — quyền thật do BE.
 */
export function buildLaborContractTemplateColumns(
  actions: LaborContractTemplateColumnActions,
): DataTableColumn<LaborContractTemplate>[] {
  const columns: DataTableColumn<LaborContractTemplate>[] = [
    { key: 'id', header: 'ID', width: 80, hideable: false, cell: (t) => t.id },
    {
      key: 'name',
      header: 'Tên mẫu',
      width: 260,
      hideable: false,
      wrap: true,
      cell: (t) => t.name,
    },
    {
      key: 'company',
      header: 'Pháp nhân',
      width: 240,
      wrap: true,
      cell: (t) => (
        <span>
          {t.company_name}
          {t.company_code && <span className="block text-xs text-muted-foreground">{t.company_code}</span>}
        </span>
      ),
    },
    {
      key: 'contract_type',
      header: 'Loại HĐ',
      width: 190,
      cell: (t) => labelOf(LABOR_CONTRACT_TYPE, String(t.contract_type)) || '—',
    },
    {
      key: 'file',
      header: 'Tệp gốc',
      width: 240,
      cell: (t) => (
        <span className="truncate" title={t.original_filename}>
          {t.original_filename || '—'}
          {t.file_size > 0 && (
            <span className="ml-1 text-muted-foreground">({formatFileSize(t.file_size)})</span>
          )}
        </span>
      ),
    },
    {
      key: 'contract_count',
      header: 'Số HĐ đã dùng',
      width: 130,
      align: 'right',
      cell: (t) => t.contract_count,
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      //  Cùng kiểu nhãn với bảng "Văn bản mẫu" ở tab bên cạnh (xanh đặc = đang dùng).
      cell: (t) => <Badge variant={t.is_active ? 'default' : 'secondary'}>{t.is_active ? 'Đang dùng' : 'Ngừng'}</Badge>,
    },
    {
      //  Backend chỉ trả ngày tạo + người tạo (không có `updated_at`).
      key: 'created_at',
      header: 'Ngày tạo',
      width: 170,
      wrap: true,
      //  Hai dòng như cột Pháp nhân: ngày ở trên, người tạo nhỏ bên dưới (gộp một dòng thì bị cắt cụt).
      cell: (t) => (
        <span>
          {formatDateTime(t.created_at)}
          {t.created_by_name && <span className="block text-xs text-muted-foreground">{t.created_by_name}</span>}
        </span>
      ),
    },
  ]

  //  "Tải tệp" luôn có vì cả trang đã đòi `read`, nên cột Thao tác luôn dựng. Một nút "⋯" mở menu icon +
  //  chữ (cùng kiểu cột thao tác bảng hợp đồng, duoc-CR-633) — cột 240px (CR-610: 120px) nay còn 80px.
  columns.push({
    key: 'actions',
    header: 'Thao tác',
    width: 80,
    hideable: false,
    cell: (t) => <LaborContractTemplateRowActions template={t} actions={actions} />,
  })
  return columns
}

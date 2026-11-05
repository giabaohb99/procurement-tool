import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { formatDate } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'
import type { LaborContractTemplateColumnActions } from '../config/labor-contract-template-columns'
import type { LaborContractTemplate } from '../types/labor-contract'
import { LaborContractTemplateRowActions } from './labor-contract-template-row-actions'

interface LaborContractTemplateCardProps {
  template: LaborContractTemplate
  actions: LaborContractTemplateColumnActions
}

/**
 * Một mẫu hợp đồng lao động (.docx) ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Tên mẫu lên đầu, pháp nhân + mã pháp nhân (sky) ngay dưới.** Hai pháp nhân thường có mẫu
 * cùng tên ("HĐLĐ xác định thời hạn"), nên dòng pháp nhân là thứ phân biệt thật; mã đi kèm vì hai
 * pháp nhân cũng có thể trùng tên.
 *
 * ⚠️ **Huy hiệu chỉ hiện khi "Ngừng"** — gần hết mẫu đang dùng, in "Đang dùng" lên mọi thẻ là
 * một dãy huy hiệu giống hệt nhau (cùng luật thẻ Pháp nhân / Nhân sự). Huy hiệu là ĐÚNG cái bảng
 * dùng cho trạng thái đó.
 *
 * Nút "⋯" dùng lại `LaborContractTemplateRowActions` của bảng (Soạn / Tải / Sửa / Thay tệp /
 * Ngừng / Xóa, ẩn theo quyền), đứng cạnh khối chữ — bảng không có `onRowClick` nên thẻ không bấm được.
 */
export function LaborContractTemplateCard({ template, actions }: LaborContractTemplateCardProps) {
  const typeLabel = labelOf(LABOR_CONTRACT_TYPE, String(template.contract_type))

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex items-start gap-2">
          <span className="line-clamp-2 min-w-0 font-medium break-words text-foreground">{template.name}</span>
          {!template.is_active && (
            <Badge variant="secondary" className="shrink-0">
              Ngừng
            </Badge>
          )}
        </div>

        <p className="truncate text-xs">
          {template.company_code && (
            <span className="font-mono text-sky-600 dark:text-sky-400">{template.company_code} · </span>
          )}
          <span className="text-muted-foreground">{template.company_name}</span>
        </p>

        {typeLabel && <p className="text-sm text-muted-foreground">{typeLabel}</p>}

        {template.original_filename && (
          <p className="truncate text-xs text-muted-foreground" title={template.original_filename}>
            {template.original_filename}
            {template.file_size > 0 && ` (${formatFileSize(template.file_size)})`}
          </p>
        )}

        <p className="text-xs text-muted-foreground tabular-nums">
          {template.contract_count} HĐ đã dùng
          <span aria-hidden="true"> · </span>
          Tạo {formatDate(template.created_at)}
          {template.created_by_name && ` bởi ${template.created_by_name}`}
        </p>
      </div>

      <div className="shrink-0">
        <LaborContractTemplateRowActions template={template} actions={actions} />
      </div>
    </div>
  )
}

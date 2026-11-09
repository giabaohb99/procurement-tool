import { LABOR_CONTRACT_VARIABLE_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { CopyButton } from '@/shared/ui/copy-button'
import {
  renderVariableStatusBadge,
  type LaborContractVariableColumnActions,
} from '../config/labor-contract-variable-columns'
import { VARIABLE_SOURCE_SYSTEM, type LaborContractVariable } from '../types/labor-contract-variable'
import { formatPlaceholderToken } from '../utils/labor-contract-placeholder-groups'
import { LaborContractVariableRowActions } from './labor-contract-variable-row-actions'

interface LaborContractVariableCardProps {
  variable: LaborContractVariable
  actions: LaborContractVariableColumnActions
}

/**
 * Một biến mẫu hợp đồng ở khổ điện thoại (màn "Danh sách biến") — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Tên hiển thị lên đầu, mã `{{ ... }}` xuống dòng phụ (sky) KÈM nút chép.** HR tìm biến bằng
 * tên ("Lương cơ bản"), nhưng thứ họ cần mang đi là mã để dán vào tệp Word — nút chép phải theo
 * sang thẻ, không thì trên điện thoại không còn cách nào lấy mã (chữ trong ô chọn / thẻ khó bôi đen).
 *
 * ⚠️ **Huy hiệu chỉ hiện khi bất thường** (biến hệ thống bị Ẩn, biến tùy chỉnh Ngừng) — dùng ĐÚNG
 * hàm vẽ huy hiệu của cột Trạng thái. Kiểu / Bắt buộc chỉ có nghĩa với biến tùy chỉnh, như ở bảng.
 *
 * Nút thao tác dùng lại `LaborContractVariableRowActions` (Sửa · Ẩn/Hiện · Ngừng/Bật · Xóa, theo
 * `can_manage` / `can_delete` backend tính), đứng cạnh khối chữ; bảng không có `onRowClick`.
 */
export function LaborContractVariableCard({ variable, actions }: LaborContractVariableCardProps) {
  const isSystem = variable.source === VARIABLE_SOURCE_SYSTEM
  const isAbnormal = isSystem ? variable.is_hidden : !variable.is_active
  const token = formatPlaceholderToken(variable.code)
  const typeLabel = isSystem ? '' : labelOf(LABOR_CONTRACT_VARIABLE_TYPE, String(variable.value_type))
  const meta = [variable.group, typeLabel].filter(Boolean).join(' · ')

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex items-start gap-2">
          <span className="min-w-0 font-medium break-words text-foreground">{variable.label}</span>
          {isAbnormal && <span className="shrink-0">{renderVariableStatusBadge(variable)}</span>}
        </div>

        <span className="flex min-w-0 items-center gap-1">
          <code className="truncate font-mono text-xs text-sky-600 dark:text-sky-400">{token}</code>
          <CopyButton value={token} label={`biến ${variable.label}`} />
        </span>

        {(meta || (!isSystem && variable.is_required)) && (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
            {meta && <span>{meta}</span>}
            {!isSystem && variable.is_required && <Badge variant="secondary">Bắt buộc</Badge>}
          </div>
        )}

        {variable.example && (
          <p className="truncate text-xs text-muted-foreground" title={variable.example}>
            Ví dụ: {variable.example}
          </p>
        )}

        <p className="text-xs text-muted-foreground tabular-nums">Dùng trong {variable.template_count} mẫu</p>
      </div>

      {(actions.canManage || actions.canDelete) && (
        <div className="shrink-0">
          <LaborContractVariableRowActions variable={variable} actions={actions} />
        </div>
      )}
    </div>
  )
}

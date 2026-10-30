import type { DataTableColumn } from '@/shared/data-table'
import { LABOR_CONTRACT_VARIABLE_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { CopyButton } from '@/shared/ui/copy-button'
import { LaborContractVariableRowActions } from '../components/labor-contract-variable-row-actions'
import { VARIABLE_SOURCE_SYSTEM, type LaborContractVariable } from '../types/labor-contract-variable'
import { formatPlaceholderToken } from '../utils/labor-contract-placeholder-groups'

export interface LaborContractVariableColumnActions {
  canManage: boolean
  canDelete: boolean
  onEdit: (variable: LaborContractVariable) => void
  onToggleActive: (variable: LaborContractVariable) => void
  onToggleHidden: (variable: LaborContractVariable) => void
  onDelete: (variable: LaborContractVariable) => void
}

function statusBadge(v: LaborContractVariable) {
  if (v.source === VARIABLE_SOURCE_SYSTEM) {
    return v.is_hidden ? <Badge variant="outline">Ẩn</Badge> : <Badge variant="secondary">Đang dùng</Badge>
  }
  return v.is_active ? <Badge variant="secondary">Đang dùng</Badge> : <Badge variant="outline">Ngừng</Badge>
}

/**
 * Cột bảng "Danh sách biến". Là hàm vì cột "Thao tác" cần callback của trang (bọc `useMemo`).
 * Người chỉ có quyền đọc vẫn thấy bảng + nút chép `{{ mã }}`; cột Thao tác chỉ dựng khi có việc để làm.
 */
export function buildLaborContractVariableColumns(
  actions: LaborContractVariableColumnActions,
): DataTableColumn<LaborContractVariable>[] {
  const columns: DataTableColumn<LaborContractVariable>[] = [
    {
      key: 'code',
      header: 'Biến',
      width: 260,
      hideable: false,
      cell: (v) => (
        <span className="flex items-center gap-1">
          <code className="truncate font-mono text-xs">{formatPlaceholderToken(v.code)}</code>
          <CopyButton value={formatPlaceholderToken(v.code)} label={`biến ${v.label}`} />
        </span>
      ),
    },
    { key: 'label', header: 'Tên hiển thị', width: 240, hideable: false, wrap: true, cell: (v) => v.label },
    { key: 'group', header: 'Nhóm', width: 170, cell: (v) => v.group },
    {
      key: 'value_type',
      header: 'Kiểu',
      width: 130,
      cell: (v) =>
        v.source === VARIABLE_SOURCE_SYSTEM ? '—' : labelOf(LABOR_CONTRACT_VARIABLE_TYPE, String(v.value_type)) || '—',
    },
    {
      key: 'example',
      header: 'Ví dụ',
      width: 200,
      cell: (v) => <span className="truncate" title={v.example}>{v.example || '—'}</span>,
    },
    {
      key: 'is_required',
      header: 'Bắt buộc',
      width: 100,
      cell: (v) => (v.source !== VARIABLE_SOURCE_SYSTEM && v.is_required ? <Badge variant="secondary">Bắt buộc</Badge> : '—'),
    },
    { key: 'template_count', header: 'Số mẫu dùng', width: 120, align: 'right', cell: (v) => v.template_count },
    { key: 'status', header: 'Trạng thái', width: 120, cell: statusBadge },
  ]
  if (actions.canManage || actions.canDelete) {
    columns.push({
      key: 'actions',
      header: 'Thao tác',
      width: 130,
      hideable: false,
      cell: (v) => <LaborContractVariableRowActions variable={v} actions={actions} />,
    })
  }
  return columns
}

import { Pencil, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import {
  concurrentDeleteDescription,
  renderConcurrentFileCell,
  type EmployeeConcurrentRowActions,
} from '../config/employee-concurrent-columns'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { concurrentPeriodLabel } from '../utils/employee-concurrent-display'
import { EmployeeConcurrentStatusBadge } from './employee-concurrent-status-badge'

interface EmployeeConcurrentMobileCardProps {
  row: EmployeeConcurrent
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeConcurrent) => void
  actions?: EmployeeConcurrentRowActions
}

/**
 * Một dòng kiêm nhiệm ở khổ điện thoại (`DataTableProps.mobileCard`). Dòng đầu là PHÒNG — công ty (thứ người đọc dùng để
 * nhận ra dòng), kèm huy hiệu trạng thái; nút Sửa / Xóa / Tệp dùng đúng hàm của bảng, không chép luồng.
 */
export function EmployeeConcurrentMobileCard({ row, canOpenFiles, onOpenFiles, actions }: EmployeeConcurrentMobileCardProps) {
  const period = concurrentPeriodLabel(row)
  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="min-w-0 font-medium text-foreground">{row.department_name}</span>
          <EmployeeConcurrentStatusBadge row={row} />
        </div>
        <p className="text-sm text-muted-foreground">
          {[row.company_name, row.position_label].filter(Boolean).join(' · ')}
        </p>
        {period && <p className="text-xs text-muted-foreground">{period}</p>}
        <p className="text-xs text-muted-foreground">
          {row.counts_scope ? 'Tính vào phạm vi quyền' : 'Không tính vào phạm vi quyền'}
          {row.decision_no && ` · Số QĐ: ${row.decision_no}`}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {/*  Không có tệp thì không đặt gạch trơ trọi cạnh nút Sửa / Xóa như ô bảng. */}
        {row.file_count > 0 && renderConcurrentFileCell(row, canOpenFiles, onOpenFiles)}
        {actions && (
          <>
            <Button type="button" variant="ghost" size="icon-sm" title="Sửa" onClick={() => actions.onEdit(row)}>
              <Pencil />
            </Button>
            <ConfirmIconButton
              icon={Trash2}
              title="Xóa"
              confirmTitle="Xóa dòng kiêm nhiệm?"
              confirmDescription={concurrentDeleteDescription(row)}
              confirmLabel="Xóa"
              destructive
              disabled={actions.isDeleting(row)}
              onConfirm={() => actions.onDelete(row)}
            />
          </>
        )}
      </div>
    </div>
  )
}

import { Checkbox } from '@/shared/ui/checkbox'
import { formatDate } from '@/shared/utils/format-date'
import type { PolicyPreviewItem } from '../types/leave-policy'
import { formatPolicyRange, type LeaveTypeNameLookup } from '../utils/leave-policy-display'
import { LeavePolicyBalanceChanges } from './leave-policy-balance-changes'

interface LeavePolicyBulkPreviewCardProps {
  item: PolicyPreviewItem
  checked: boolean
  onToggle: (employeeId: number) => void
  typeName: LeaveTypeNameLookup
}

/**
 * Một người trong danh sách xem trước Phân bổ hàng loạt, ở khổ điện thoại (duoc-CR-721).
 *
 * ⚠️ **Ô chọn nằm TRONG thẻ, và thẻ KHÔNG phải nút.** Bảng xem trước không có `onRowClick`, việc duy nhất
 * làm được trên dòng là tick chọn — nên thẻ giữ đúng ô đó, tên người là `<label>` của ô (chạm vào tên cũng
 * tick được, vùng chạm lớn hơn cái ô 16px). Dòng VƯỚNG khóa ô và nói lý do bằng chữ đỏ, y như cột cuối bảng.
 *
 * ⚠️ **Thay đổi quỹ năm nay bày thành bảng nhỏ "Hiện tại → Sau phân bổ"** (`LeavePolicyBalanceChanges`,
 * dùng chung với hộp phân bổ một người) thay vì câu nối dấu chấm phẩy của ô bảng: trên máy hẹp câu đó tự
 * ngắt ở chỗ ngẫu nhiên và mũi tên trước / sau rơi sang dòng khác. Chỉ kê loại ĐỔI hạn mức, cùng luật với
 * `summarizeQuotaChanges`; không loại nào đổi thì nói *Không đổi*.
 */
export function LeavePolicyBulkPreviewCard({ item, checked, onToggle, typeName }: LeavePolicyBulkPreviewCardProps) {
  const name = item.name || `Nhân sự #${item.employee_id}`
  const inputId = `bulk-preview-${item.employee_id}`
  const moved = item.changes.filter((c) => c.before !== c.after)
  const blocked = Boolean(item.conflict)

  return (
    <div className="flex items-start gap-3 text-sm">
      <Checkbox
        id={inputId}
        className="mt-0.5"
        checked={!blocked && checked}
        disabled={blocked}
        aria-label={`Chọn ${name}`}
        onCheckedChange={() => onToggle(item.employee_id)}
      />
      <div className="min-w-0 flex-1 space-y-1.5">
        <label htmlFor={inputId} className="block min-w-0">
          <span className="block truncate font-medium text-foreground">{name}</span>
          <span className="flex flex-wrap items-center gap-x-1 text-xs text-muted-foreground">
            {item.code && (
              <span className="font-medium text-sky-600 tabular-nums dark:text-sky-400">{item.code}</span>
            )}
            {item.department_name && (
              <span>
                {item.code && <span aria-hidden="true">· </span>}
                {item.department_name}
              </span>
            )}
          </span>
        </label>

        {item.hire_date && (
          <p className="text-xs text-muted-foreground tabular-nums">Vào làm {formatDate(item.hire_date)}</p>
        )}

        {item.conflict !== 'scope' && (
          <p className="text-muted-foreground">
            Hiện tại:{' '}
            {item.current ? (
              <span className="text-foreground">
                {item.current.policy_name} ({formatPolicyRange(item.current.from, item.current.to)})
              </span>
            ) : (
              'Chưa có'
            )}
          </p>
        )}

        {blocked ? (
          <p className="text-destructive">
            {item.conflict === 'self' ? 'Không tự phân bổ chính sách cho chính mình.' : item.conflict_message}
          </p>
        ) : moved.length > 0 ? (
          <LeavePolicyBalanceChanges changes={moved} typeName={typeName} />
        ) : (
          <p className="text-muted-foreground">Quỹ năm nay: Không đổi</p>
        )}
      </div>
    </div>
  )
}

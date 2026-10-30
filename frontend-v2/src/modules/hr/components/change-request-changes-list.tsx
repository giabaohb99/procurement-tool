import { ArrowRight } from 'lucide-react'

import {
  CHANGE_REQUEST_GROUP_LABELS,
  MASKED_VALUE_TEXT,
  formatEmployeeFieldValue,
  getEmployeeFieldLabel,
} from '../config/employee-profile-fields'
import type { EmployeeChangeRequest } from '../types/employee-change-request'

/**
 * Danh sách gọn "ô nào: trước → sau" của MỘT đề nghị sửa hồ sơ (duoc-CR-676) — dùng ở thẻ
 * "Đề nghị sửa hồ sơ" của Trang cá nhân. Màn duyệt của phòng Nhân sự dùng bảng so sánh đủ cột
 * (`change-request-diff-table.tsx`) chứ không dùng khối này.
 */
export function ChangeRequestChangesList({ request }: { request: EmployeeChangeRequest }) {
  const families = request.families
  if (request.items.length === 0 && !families) {
    return <p className="text-sm text-muted-foreground">Đề nghị không có ô nào.</p>
  }

  return (
    <ul className="flex flex-col gap-1.5 text-sm">
      {request.items.map((item) => (
        <li key={`${item.group}-${item.field}`} className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-muted-foreground">
            {CHANGE_REQUEST_GROUP_LABELS[item.group]} · {getEmployeeFieldLabel(item.field)}:
          </span>
          {item.masked ? (
            <span className="italic text-muted-foreground">{MASKED_VALUE_TEXT}</span>
          ) : (
            <span className="inline-flex flex-wrap items-baseline gap-1.5">
              <span className="line-through decoration-muted-foreground/60">
                {formatEmployeeFieldValue(item.field, item.before) || '(trống)'}
              </span>
              <ArrowRight className="size-3.5 shrink-0 self-center text-muted-foreground" />
              <span className="font-medium">
                {formatEmployeeFieldValue(item.field, item.after) || '(trống)'}
              </span>
            </span>
          )}
        </li>
      ))}
      {families && (
        <li className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-muted-foreground">{CHANGE_REQUEST_GROUP_LABELS.families}:</span>
          {families.masked ? (
            <span className="italic text-muted-foreground">{MASKED_VALUE_TEXT}</span>
          ) : (
            <span>
              khai lại danh sách ({families.before?.length ?? 0} → {families.after?.length ?? 0} người)
            </span>
          )}
        </li>
      )}
    </ul>
  )
}

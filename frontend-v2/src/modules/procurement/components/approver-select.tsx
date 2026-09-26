import type { Employee } from '@/modules/hr/types/employee'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { SearchSelect } from '@/shared/ui/search-select'

/**
 * Ô «Trưởng phòng phê duyệt» dùng chung cho YCMH · YCBG · ĐMH — bao-CR-499 (đại ca chốt 26/09/2026).
 *
 * Một cột, hai nghĩa theo thời điểm: TRƯỚC khi duyệt là người ĐƯỢC CHỌN (hệ gửi chuông + mail cho
 * người này lúc gửi duyệt); bấm Duyệt xong hệ ghi đè bằng người THỰC duyệt (bao-CR-490) và ô khóa.
 * Bản in luôn in tên đang nằm trong cột. Cố ý KHÔNG gộp với ô «Trưởng bộ phận» (CR-474): đại ca
 * muốn giữ hai ô tách để sau này bỏ ô này được mà không đụng ô kia.
 */
interface ApproverSelectProps {
  id: string
  /** id nhân sự đang nằm trong cột (0 = chưa chọn). */
  value: number
  /** Tên hiển thị backend trả — dùng khi khóa hoặc khi người đó không còn trong danh sách. */
  name: string
  employees: Employee[]
  /** Đang ở chế độ sửa VÀ phiếu chưa duyệt. */
  editable: boolean
  onChange: (next: { approver_employee_id: number; approver_employee_name: string }) => void
}

export function ApproverSelect({ id, value, name, employees, editable, onChange }: ApproverSelectProps) {
  const inList = employees.some((employee) => employee.id === value)
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className={editable && employees.length ? '' : 'text-muted-foreground'}>
        Trưởng phòng phê duyệt
      </Label>
      {editable && employees.length ? (
        <SearchSelect
          id={id}
          searchInTrigger
          value={inList ? String(value) : ''}
          placeholder={name || 'Chọn người sẽ duyệt — hệ báo cho người này khi gửi duyệt'}
          searchPlaceholder="Gõ tên hoặc mã nhân sự…"
          options={employees.map((employee) => ({
            value: String(employee.id),
            label: `${employee.code} - ${employee.full_name}`,
          }))}
          onChange={(next) => {
            const employee = employees.find((option) => option.id === Number(next))
            if (!employee || employee.id === value) return
            onChange({ approver_employee_id: employee.id, approver_employee_name: employee.full_name })
          }}
        />
      ) : (
        <ReadOnlyValue>{name || 'Chưa chọn'}</ReadOnlyValue>
      )}
    </div>
  )
}

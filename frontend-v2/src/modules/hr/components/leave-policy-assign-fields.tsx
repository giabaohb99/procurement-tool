import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { HelpHint } from '@/shared/ui/help-hint'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { LeavePolicySelect } from './leave-policy-select'
import { LEAVE_POLICY_FROM_DATE_HINT, LEAVE_POLICY_TO_DATE_HINT } from '../utils/leave-policy-date-hints'

interface AssignEmployeeOption {
  id: number
  code: string
  full_name: string
  hire_date?: string | null
}

interface LeavePolicyAssignFieldsProps {
  /** Thiếu `employee.read` thì không dựng ô chọn người (mount là gọi API). */
  canPickEmployee: boolean
  employees: readonly AssignEmployeeOption[]
  employeeId: number
  onEmployeeChange: (id: number) => void
  policies: readonly { id: number; code: string; name: string }[]
  policiesLoading: boolean
  policyId: number
  onPolicyChange: (id: number) => void
  from: string
  onFromChange: (value: string) => void
  to: string
  onToChange: (value: string) => void
  /** Câu báo khoảng ngày ngược; rỗng = hợp lệ. */
  rangeError: string
  note: string
  onNoteChange: (value: string) => void
  recalc: boolean
  onRecalcChange: (value: boolean) => void
}

/**
 * Các ô nhập của hộp Phân bổ chính sách cho MỘT người (tách khỏi `leave-policy-assign-dialog.tsx`, review
 * L6 của duoc-CR-717): nhân sự · chính sách · khoảng ngày (kèm nút "Từ ngày vào làm") · ghi chú · ô tick
 * "Tính lại hạn mức năm nay" (mặc định BẬT, D3a). Thuần trình bày — state và xem trước ở hộp cha.
 */
export function LeavePolicyAssignFields({
  canPickEmployee,
  employees,
  employeeId,
  onEmployeeChange,
  policies,
  policiesLoading,
  policyId,
  onPolicyChange,
  from,
  onFromChange,
  to,
  onToChange,
  rangeError,
  note,
  onNoteChange,
  recalc,
  onRecalcChange,
}: LeavePolicyAssignFieldsProps) {
  const employee = employees.find((e) => e.id === employeeId)
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="space-y-1.5 sm:col-span-2">
        <Label htmlFor="assign-employee">
          Nhân sự
          <RequiredMark />
        </Label>
        {canPickEmployee ? (
          <SearchSelect
            id="assign-employee"
            value={employeeId ? String(employeeId) : ''}
            options={employees.map((e) => ({ value: String(e.id), label: e.full_name, hint: e.code }))}
            placeholder="Chọn nhân sự"
            searchPlaceholder="Tìm theo tên hoặc mã…"
            emptyMessage="Không tìm thấy nhân sự nào."
            clearable
            onChange={(v) => onEmployeeChange(Number(v) || 0)}
          />
        ) : (
          <p className="text-sm text-muted-foreground">Cần quyền xem danh sách nhân sự để chọn người.</p>
        )}
      </div>

      <div className="space-y-1.5 sm:col-span-2">
        <Label htmlFor="assign-policy">
          Chính sách
          <RequiredMark />
        </Label>
        <LeavePolicySelect
          id="assign-policy"
          policies={policies}
          isLoading={policiesLoading}
          value={policyId}
          onChange={onPolicyChange}
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between gap-2">
          <Label>
            Từ ngày
            <RequiredMark />
            <HelpHint label="Giải thích Từ ngày">{LEAVE_POLICY_FROM_DATE_HINT}</HelpHint>
          </Label>
          <Button
            type="button"
            variant="link"
            size="sm"
            className="h-auto p-0 text-xs"
            disabled={!employee?.hire_date}
            title={employee && !employee.hire_date ? 'Hồ sơ chưa có ngày vào làm' : undefined}
            onClick={() => employee?.hire_date && onFromChange(employee.hire_date.slice(0, 10))}
          >
            Từ ngày vào làm
          </Button>
        </div>
        <DatePicker value={from} onChange={onFromChange} clearable={false} />
      </div>
      <div className="space-y-1.5">
        <Label>
          Đến ngày
          <HelpHint label="Giải thích Đến ngày">{LEAVE_POLICY_TO_DATE_HINT}</HelpHint>
        </Label>
        <DatePicker value={to} onChange={onToChange} placeholder="Không thời hạn" />
        {rangeError && <p className="text-xs text-destructive">{rangeError}</p>}
      </div>

      <div className="space-y-1.5 sm:col-span-2">
        <Label htmlFor="assign-note">Ghi chú</Label>
        <Textarea id="assign-note" rows={2} maxLength={500} value={note} onChange={(e) => onNoteChange(e.target.value)} />
      </div>

      <label className="flex items-start gap-2 text-sm sm:col-span-2">
        <Checkbox checked={recalc} onCheckedChange={(v) => onRecalcChange(v === true)} className="mt-0.5" />
        <span>
          Tính lại hạn mức năm nay cho quỹ đã cấp
          <span className="block text-xs text-muted-foreground">
            Bỏ tick thì quỹ năm nay đã cấp giữ nguyên, chính sách chỉ áp cho lần cấp quỹ sau.
          </span>
        </span>
      </label>
    </div>
  )
}

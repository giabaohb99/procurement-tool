import { useFormContext } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { FormSection } from '@/shared/ui/form-section'
import { Label } from '@/shared/ui/label'
import { NumberInput } from '@/shared/ui/number-input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { formatMoney } from '@/shared/utils/format-money'
import { MAX_PROFILE_SALARY, type EmployeeProfileFormValues } from '../schemas/employee-schema'
import type { EmployeeDetail } from '../types/employee'

interface EmployeeSalarySectionProps {
  employee: EmployeeDetail
  /** Người đang xem là CHÍNH nhân sự này — chỉ họ nhận được số. */
  isSelf: boolean
  canWrite: boolean
}

const FIELDS = [
  { name: 'salary_monthly', label: 'Lương (đ/tháng)' },
  { name: 'allowance_monthly', label: 'Phụ cấp (đ/tháng)' },
] as const

/** Đã nhập lương chưa — người khác đọc cờ `salary_set`, chính chủ đọc thẳng hai số. */
function isSalarySet(employee: EmployeeDetail): boolean {
  if (employee.salary_set != null) return employee.salary_set
  return (employee.salary_monthly ?? 0) > 0 || (employee.allowance_monthly ?? 0) > 0
}

/**
 * Nhóm «Lương» trong mục Công việc (duoc-CR-693) — MỘT chỗ nhập lương duy nhất của hồ sơ.
 *
 * ⚠️ Chỉ chính nhân sự này xem được số (backend chỉ trả hai số khi người xem là chính họ). Người
 * khác — kể cả người nhập và quản trị — nhận `salary_set` thay số, nên ô sửa LUÔN mở ra trống:
 * - giá trị form `null` = KHÔNG ĐỤNG → `pickWritableProfile` bỏ khỏi PATCH, số thật được giữ;
 * - gõ số mới = thay số cũ; bấm «Xóa số đã nhập» = gửi `0` (xóa).
 * Gõ rồi xóa trắng ô thì quay về «không đụng», KHÔNG thành 0 — xóa nhầm số mình không nhìn thấy
 * là mất dữ liệu mà không ai biết.
 *
 * Chính chủ chỉ XEM: tự sửa lương mình thì backend trả 403, nên không bày ô nhập.
 */
export function EmployeeSalarySection({ employee, isSelf, canWrite }: EmployeeSalarySectionProps) {
  const form = useFormContext<EmployeeProfileFormValues>()
  const salarySet = isSalarySet(employee)
  const salary = form.watch('salary_monthly')
  const allowance = form.watch('allowance_monthly')
  const clearing = salary === 0 && allowance === 0
  const unsetLabel = salarySet ? 'Đã nhập (ẩn)' : 'Chưa nhập'

  if (isSelf || !canWrite) {
    return (
      <FormSection title="Lương">
        {FIELDS.map((f) => {
          const amount = employee[f.name] ?? 0
          return (
            <div key={f.name} className="grid gap-2">
              <Label>{f.label}</Label>
              <ReadOnlyValue>
                {isSelf ? (amount > 0 ? `${formatMoney(amount)} đ` : 'Chưa nhập') : unsetLabel}
              </ReadOnlyValue>
            </div>
          )
        })}
        <p className="text-xs text-muted-foreground sm:col-span-2">
          {isSelf
            ? 'Chỉ bạn xem được số lương của mình. Cần điều chỉnh thì liên hệ phòng Nhân sự.'
            : 'Chỉ chính nhân sự này xem được số lương.'}
        </p>
      </FormSection>
    )
  }

  function setBoth(value: number | null) {
    for (const f of FIELDS) form.setValue(f.name, value, { shouldDirty: true })
  }

  return (
    <FormSection title="Lương">
      {FIELDS.map((f) => (
        <FormField
          key={f.name}
          control={form.control}
          name={f.name}
          render={({ field }) => (
            <FormItem>
              <FormLabel>{f.label}</FormLabel>
              <FormControl>
                <NumberInput
                  decimals={false}
                  max={MAX_PROFILE_SALARY}
                  value={field.value ?? 0}
                  //  Ô trống (0) giữ nguyên trạng thái đang có: «không đụng» vẫn là `null`,
                  //  «sẽ xóa» vẫn là 0. Chỉ số > 0 mới là thay số.
                  onChange={(next) => field.onChange(next > 0 ? next : field.value === 0 ? 0 : null)}
                  placeholder={field.value === 0 ? 'Sẽ xóa khi Lưu' : unsetLabel}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      ))}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground sm:col-span-2">
        <span>
          {clearing
            ? 'Lương và phụ cấp đã nhập sẽ bị xóa khi bấm Lưu.'
            : 'Chỉ chính nhân sự này xem được số lương. Ký hợp đồng lao động sẽ tự cập nhật ô này. Để trống là giữ nguyên số cũ.'}
        </span>
        {/*  `type="button"`: nút nằm trong form hồ sơ, thiếu là bấm vào form LƯU luôn. */}
        {salarySet && !clearing && (
          <Button type="button" variant="link" size="sm" className="h-auto p-0 text-xs" onClick={() => setBoth(0)}>
            Xóa số đã nhập
          </Button>
        )}
        {clearing && (
          <Button type="button" variant="link" size="sm" className="h-auto p-0 text-xs" onClick={() => setBoth(null)}>
            Không xóa nữa
          </Button>
        )}
      </div>
    </FormSection>
  )
}

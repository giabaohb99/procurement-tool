import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { SearchSelect } from '@/shared/ui/search-select'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { useEmployees } from '../hooks/use-employees'
import { useLeaveTypes } from '../hooks/use-leave'
import { encashmentYearOptions, type LeaveEncashment } from '../types/leave-encashment'
import type {
  LeaveEncashmentFormErrors,
  LeaveEncashmentFormValues,
} from '../utils/leave-encashment-form-values'
import { EncashFieldLabel, EncashReadOnlyField } from './leave-encashment-flat-field'

interface LeaveEncashmentTargetFieldsProps {
  /** Phiếu đang sửa: ba ô thành chữ chỉ xem (backend không cho đổi người, loại nghỉ, năm quỹ). */
  request?: LeaveEncashment
  values: LeaveEncashmentFormValues
  errors: LeaveEncashmentFormErrors
  onChange: <K extends 'employee_id' | 'leave_type_id' | 'balance_year'>(
    key: K,
    value: LeaveEncashmentFormValues[K],
  ) => void
  today: Date
}

/** `SearchSelect` là nút mở hộp chọn, `ERP_FILLED_FIELDS` không bắt được — tô cùng dạng ô nền xám không viền. */
const FILLED_TRIGGER = 'border-transparent bg-muted shadow-none'

/**
 * Ba ô "thanh toán CHO AI, LOẠI NÀO, NĂM NÀO" của form phiếu thanh toán nghỉ phép (duoc-CR-719) — tách khỏi
 * `leave-encashment-form.tsx` cho tệp gọn. Ba ô này quyết định khóa trùng (người, loại, năm) nên chỉ chọn lúc LẬP.
 * Mỗi ô một ô lưới (không trải hai cột): form xếp chúng vào lưới 2 cột cùng ô Lý do.
 */
export function LeaveEncashmentTargetFields({
  request,
  values,
  errors,
  onChange,
  today,
}: LeaveEncashmentTargetFieldsProps) {
  const { can } = usePermission()
  const { user } = useAuth()

  //  Lập hộ — chỉ dựng ô chọn cho người đọc được danh bạ; thiếu quyền thì KHÔNG gọi danh bạ (mount là ăn toast 403).
  //  Không lọc `is_active`: người đang làm thủ tục nghỉ việc vẫn phải lập được phiếu trả phép (D5).
  const canPickTaker = can('employee', 'read') && !request
  const { data: employeeData } = useEmployees({ page_size: 1000 }, { enabled: canPickTaker })
  const employeeOptions = (employeeData?.items ?? []).map((e) => ({
    value: String(e.id),
    label: `${e.full_name} (${e.code})`,
  }))

  const { data: typeData, isLoading: typesLoading } = useLeaveTypes(true)
  const encashableTypes = (typeData?.items ?? []).filter((t) => t.allow_encashment)
  const selfName = user?.full_name || 'bạn'

  if (request) {
    return (
      <>
        <EncashReadOnlyField label="Người được thanh toán">
          {request.employee_name}
          {request.employee_code ? ` (${request.employee_code})` : ''}
        </EncashReadOnlyField>
        <EncashReadOnlyField label="Loại nghỉ">{request.leave_type_name}</EncashReadOnlyField>
        <EncashReadOnlyField label="Năm quỹ phép">{request.balance_year}</EncashReadOnlyField>
      </>
    )
  }

  return (
    <>
      {/*  Không lập hộ được thì phiếu luôn là của chính mình — nói thành lời thay vì bỏ trống một ô trong lưới. */}
      {!canPickTaker && (
        <EncashReadOnlyField label="Người được thanh toán">{user?.full_name || 'Chính bạn'}</EncashReadOnlyField>
      )}
      {canPickTaker && (
        <div className="space-y-1.5">
          <EncashFieldLabel
            label="Người được thanh toán"
            htmlFor="encash-taker"
            hintId="encash-taker-hint"
            hint="Để trống là lập cho chính bạn. Lập hộ người khác cần quyền lập phiếu trong phạm vi của người đó."
          />
          <SearchSelect
            id="encash-taker"
            className={FILLED_TRIGGER}
            value={values.employee_id ? String(values.employee_id) : ''}
            options={employeeOptions}
            placeholder={`Mặc định: ${selfName}`}
            searchPlaceholder="Tìm theo tên hoặc mã…"
            emptyMessage="Không tìm thấy nhân sự nào."
            clearable
            onChange={(id) => onChange('employee_id', Number(id) || 0)}
          />
        </div>
      )}

      <div className="space-y-1.5">
        <EncashFieldLabel label="Loại nghỉ" htmlFor="encash-type" required />
        <Select
          value={values.leave_type_id ? String(values.leave_type_id) : ''}
          onValueChange={(v) => onChange('leave_type_id', Number(v) || 0)}
          disabled={typesLoading || encashableTypes.length === 0}
        >
          <SelectTrigger id="encash-type" className="w-full" aria-label="Loại nghỉ">
            <SelectValue placeholder={typesLoading ? 'Đang tải…' : 'Chọn loại nghỉ'} />
          </SelectTrigger>
          <SelectContent>
            {encashableTypes.map((t) => (
              <SelectItem key={t.id} value={String(t.id)}>
                {t.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {/*  Hai câu này là TRẠNG THÁI cần làm gì đó (ô sai / chưa có loại nào), nên để hiện dòng chứ không thu vào (i). */}
        {errors.leave_type_id ? (
          <p role="alert" className="text-xs text-destructive">
            {errors.leave_type_id}
          </p>
        ) : (
          !typesLoading &&
          encashableTypes.length === 0 && (
            <p className="text-xs text-muted-foreground">
              Chưa loại nghỉ nào bật <strong>Cho phép thanh toán nghỉ phép</strong>. Nhờ Nhân sự bật ở Thiết lập, Loại
              nghỉ.
            </p>
          )
        )}
      </div>

      <div className="space-y-1.5">
        <EncashFieldLabel
          label="Năm quỹ phép"
          htmlFor="encash-year"
          required
          hintId="encash-year-hint"
          hint="Năm nay hoặc năm trước. Năm trước đã kết sổ thì không còn ngày."
        />
        <Select value={String(values.balance_year)} onValueChange={(v) => onChange('balance_year', Number(v))}>
          <SelectTrigger id="encash-year" className="w-full" aria-label="Năm quỹ phép">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {encashmentYearOptions(today).map((y) => (
              <SelectItem key={y} value={String(y)}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </>
  )
}

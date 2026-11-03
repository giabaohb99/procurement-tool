import { CalendarPlus, Save, Send } from 'lucide-react'
import { useRef, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { FormCard } from '@/shared/ui/form-card'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { toDateInputValue } from '@/shared/utils/format-date'
import { useEmployees } from '../hooks/use-employees'
import { useLeaveCompAction, useSaveLeaveCompRequest } from '../hooks/use-leave-comp'
import {
  COMP_REASON_MAX,
  LEAVE_COMP_DAY_OPTIONS,
  type LeaveCompRequest,
} from '../types/leave-comp'
import {
  emptyLeaveCompForm,
  formValuesOfLeaveComp,
  toLeaveCompPayload,
  validateLeaveCompForm,
  type LeaveCompFormErrors,
  type LeaveCompFormValues,
} from '../utils/leave-comp-form-values'

interface LeaveCompRequestFormProps {
  /** Phiếu đang sửa (Nháp / Trả về); vắng = lập mới. */
  request?: LeaveCompRequest
  /** Gọi sau khi LƯU thành công (kể cả khi bước gửi duyệt sau đó hỏng) với id phiếu. */
  onSaved?: (id: number) => void
}

const DAY_LABELS: Record<number, string> = { 0.5: 'Nửa ngày (0,5)', 1: 'Cả ngày (1)' }

/**
 * FORM PHIẾU XIN NGHỈ BÙ — bốn ô: người nghỉ · ngày đã đi làm · số ngày · lý do, kèm hai nút
 * «Lưu nháp» / «Gửi duyệt» ngay dưới thẻ (form quá ngắn để cần nhóm nút dính đầu trang).
 *
 * ⚠️ Ba bẫy biểu mẫu của repo (xem `.claude/rules/frontend-v2-ui-conventions.md`):
 *  · hai nút khai `type="button"` — không đứng trong `<form>` nhưng nếu ai bọc lại thì không bị submit ngầm;
 *  · chặn bấm đúp bằng `useRef` (đổi ngay trong tick), `disabled={...isPending}` chỉ để báo hiệu;
 *  · «Gửi duyệt» = LƯU rồi mới gửi, vì backend kiểm lý do trên bản đã lưu. Nếu lưu xong mà gửi
 *    hỏng (vd 422) thì vẫn báo `onSaved` để trang chuyển sang phiếu nháp vừa tạo — ở lại form mới
 *    thì bấm lần nữa sẽ tạo phiếu thứ hai và ăn 409 trùng ngày.
 * Lỗi 4xx của backend (422 ngày tương lai / ngày làm việc thường, 409 trùng) do http client bật toast.
 */
export function LeaveCompRequestForm({ request, onSaved }: LeaveCompRequestFormProps) {
  const [values, setValues] = useState<LeaveCompFormValues>(() =>
    request ? formValuesOfLeaveComp(request) : emptyLeaveCompForm(),
  )
  const [errors, setErrors] = useState<LeaveCompFormErrors>({})
  const [busy, setBusy] = useState(false)
  const busyRef = useRef(false)

  const save = useSaveLeaveCompRequest()
  const act = useLeaveCompAction()

  //  Lập hộ — chỉ dựng ô chọn cho người đọc được danh bạ; không có quyền thì KHÔNG gọi danh bạ
  //  (mount là ăn toast 403). Phạm vi tạo hộ vẫn do backend chốt.
  const { can } = usePermission()
  const canPickTaker = can('employee', 'read')
  const { data: employeeData } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: canPickTaker },
  )
  const employeeOptions = (employeeData?.items ?? []).map((e) => ({
    value: String(e.id),
    label: `${e.full_name} (${e.code})`,
  }))
  const { user } = useAuth()
  const takerId = values.employee_id || request?.employee_id || user?.employee_id || 0

  const today = toDateInputValue(new Date())

  const set = <K extends keyof LeaveCompFormValues>(key: K, v: LeaveCompFormValues[K]) =>
    setValues((prev) => ({ ...prev, [key]: v }))

  const run = async (andSubmit: boolean) => {
    if (busyRef.current) return
    const found = validateLeaveCompForm(values, today, andSubmit)
    setErrors(found)
    if (Object.keys(found).length > 0) return

    busyRef.current = true
    setBusy(true)
    let savedId = 0
    try {
      const saved = await save.mutateAsync({
        id: request?.id,
        values: toLeaveCompPayload(values),
      })
      savedId = saved.id
      if (andSubmit) await act.mutateAsync({ id: saved.id, action: 'submit' })
    } catch {
      //  Toast lỗi đã do http client bật; ở đây chỉ để không nổ lời hứa chưa bắt.
    } finally {
      busyRef.current = false
      setBusy(false)
    }
    if (savedId) onSaved?.(savedId)
  }

  const disabled = busy || save.isPending || act.isPending

  return (
    <FormCard title="Phiếu xin nghỉ bù" icon={CalendarPlus} iconClassName="text-primary">
      <div className="grid items-start gap-x-4 gap-y-4 md:grid-cols-2">
        {request && (
          //  Sửa phiếu: PATCH không đổi được người nghỉ (backend chỉ nhận ngày / số ngày / lý do) — chỉ HIỆN tên,
          //  không dựng ô chọn để người dùng khỏi tưởng đổi được rồi thấy phiếu vẫn của người cũ.
          <p className="text-sm md:col-span-2" data-testid="comp-taker-readonly">
            <span className="text-muted-foreground">Người nghỉ: </span>
            <strong>{request.employee_name}</strong>
            {request.employee_code ? ` (${request.employee_code})` : ''}
          </p>
        )}
        {canPickTaker && !request && (
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="comp-taker">
              Người nghỉ
              <RequiredMark />
            </Label>
            <SearchSelect
              value={takerId ? String(takerId) : ''}
              options={employeeOptions}
              placeholder="Chọn người nghỉ"
              searchPlaceholder="Tìm theo tên hoặc mã…"
              emptyMessage="Không tìm thấy nhân sự nào."
              clearable
              onChange={(id) => set('employee_id', Number(id) || 0)}
            />
            <p className="text-xs text-muted-foreground">
              Mặc định là bạn. Lập hộ người khác cần quyền tạo phiếu trong phạm vi của người đó.
            </p>
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="comp-work-date">
            Ngày đã đi làm
            <RequiredMark />
          </Label>
          <DatePicker
            id="comp-work-date"
            value={values.work_date}
            onChange={(v) => set('work_date', v)}
            clearable={false}
          />
          {errors.work_date ? (
            <p role="alert" className="text-xs text-destructive">
              {errors.work_date}
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">
              Ngày nghỉ tuần hoặc ngày lễ mà bạn đã đi làm; không chọn ngày tương lai.
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label id="comp-days-label">
            Số ngày xin nghỉ bù
            <RequiredMark />
          </Label>
          <RadioGroup
            aria-labelledby="comp-days-label"
            value={String(values.days)}
            onValueChange={(v) => set('days', Number(v))}
            className="h-9"
          >
            {LEAVE_COMP_DAY_OPTIONS.map((d) => (
              <div key={d} className="flex items-center gap-2">
                <RadioGroupItem id={`comp-days-${d}`} value={String(d)} />
                <Label htmlFor={`comp-days-${d}`} className="font-normal">
                  {DAY_LABELS[d]}
                </Label>
              </div>
            ))}
          </RadioGroup>
          {errors.days && (
            <p role="alert" className="text-xs text-destructive">
              {errors.days}
            </p>
          )}
        </div>

        <div className="space-y-1.5 md:col-span-2">
          <Label htmlFor="comp-reason">
            Lý do đi làm
            <RequiredMark />
          </Label>
          <Textarea
            id="comp-reason"
            rows={3}
            maxLength={COMP_REASON_MAX}
            placeholder="Làm việc gì, theo yêu cầu của ai — để người duyệt không phải hỏi lại."
            value={values.reason}
            onChange={(e) => set('reason', e.target.value)}
          />
          <div className="flex justify-between gap-2">
            {errors.reason ? (
              <p role="alert" className="text-xs text-destructive">
                {errors.reason}
              </p>
            ) : (
              <span />
            )}
            <p className="text-xs text-muted-foreground tabular-nums">
              {values.reason.length} / {COMP_REASON_MAX}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-end gap-2 border-t border-dashed pt-4">
        <Button type="button" variant="outline" onClick={() => void run(false)} disabled={disabled}>
          <Save className="size-4" />
          Lưu nháp
        </Button>
        <Button type="button" onClick={() => void run(true)} disabled={disabled}>
          <Send className="size-4" />
          Gửi duyệt
        </Button>
      </div>
    </FormCard>
  )
}

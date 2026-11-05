import { Save, Send } from 'lucide-react'
import { useRef, useState, type ReactNode } from 'react'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { FormSection } from '@/shared/ui/form-section'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Textarea } from '@/shared/ui/textarea'
import {
  useLeaveEncashmentAction,
  useLeaveEncashmentPreview,
  useSaveLeaveEncashment,
} from '../hooks/use-leave-encashment'
import {
  ENCASHMENT_NOTE_MAX,
  formatEncashDays,
  LEAVE_ENCASHMENT_REASON,
  LEAVE_ENCASHMENT_REASON_LABELS,
  type LeaveEncashment,
} from '../types/leave-encashment'
import {
  emptyLeaveEncashmentForm,
  formValuesOfLeaveEncashment,
  toLeaveEncashmentCreatePayload,
  toLeaveEncashmentUpdatePayload,
  validateLeaveEncashmentForm,
  type LeaveEncashmentFormErrors,
  type LeaveEncashmentFormValues,
} from '../utils/leave-encashment-form-values'
import { PRIMARY_ACTION_SLOT, SECONDARY_ACTION_SLOT } from '../utils/leave-detail-action-slots'
import { EncashFieldLabel } from './leave-encashment-flat-field'
import { LeaveEncashmentDaysSection } from './leave-encashment-days-section'
import { LeaveEncashmentTargetFields } from './leave-encashment-target-fields'

interface LeaveEncashmentFormProps {
  /** Phiếu đang sửa (Nháp / Trả về); vắng = lập mới. */
  request?: LeaveEncashment
  /** Gọi sau khi LƯU thành công (kể cả khi bước gửi duyệt sau đó hỏng) với id phiếu. */
  onSaved?: (id: number) => void
  /** Hôm nay — truyền vào để test không phụ thuộc đồng hồ (năm quỹ = năm nay / năm trước). */
  today?: Date
  /**
   * Đặt hai phần của form vào khung trang: `actions` (Lưu nháp / Gửi duyệt) lên hàng tiêu đề, `body` (các nhóm ô)
   * xuống mặt phẳng. Vắng = nút nằm dưới các nhóm (dùng khi form đứng một mình, như trong bài kiểm).
   */
  frame?: (parts: { actions: ReactNode; body: ReactNode }) => ReactNode
}

const REASONS = [LEAVE_ENCASHMENT_REASON.YEAR_END, LEAVE_ENCASHMENT_REASON.RESIGNATION]

const defaultFrame = ({ actions, body }: { actions: ReactNode; body: ReactNode }) => (
  <>
    {body}
    <div className="flex flex-wrap justify-end gap-2 px-4 py-4 sm:px-6">{actions}</div>
  </>
)

/**
 * FORM PHIẾU THANH TOÁN NGHỈ PHÉP (duoc-CR-719) — bố cục PHẲNG kiểu ERPNext (cùng trang Loại nghỉ / Chính sách nghỉ
 * phép): nhóm Thông tin (người nhận · loại nghỉ · năm quỹ · lý do · ghi chú, lưới 2 cột) và nhóm Số ngày (dải số ngày
 * được thanh toán đọc từ `/preview` + ô số ngày). Chú thích thu vào (i) cạnh nhãn; hai nút Lưu nháp / Gửi duyệt do
 * trang đặt lên hàng tiêu đề qua `frame`.
 *
 * ⚠️ Bẫy biểu mẫu (`.claude/rules/frontend-v2-ui-conventions.md`): nút đều `type="button"`; chặn bấm đúp bằng `useRef`
 * (đổi ngay trong tick); "Gửi duyệt" = LƯU rồi mới gửi, lưu xong mà gửi hỏng vẫn báo `onSaved` để trang chuyển sang
 * phiếu nháp vừa tạo — ở lại form mới thì bấm lần nữa là phiếu thứ hai và ăn 409 trùng (người, loại, năm).
 * Sửa phiếu: người, loại nghỉ, năm quỹ KHÔNG đổi được (backend bỏ qua) — hiện chữ thường, không dựng ô chọn.
 */
export function LeaveEncashmentForm({
  request,
  onSaved,
  today = new Date(),
  frame = defaultFrame,
}: LeaveEncashmentFormProps) {
  const [values, setValues] = useState<LeaveEncashmentFormValues>(() =>
    request ? formValuesOfLeaveEncashment(request) : emptyLeaveEncashmentForm(today.getFullYear()),
  )
  const [errors, setErrors] = useState<LeaveEncashmentFormErrors>({})
  const [busy, setBusy] = useState(false)
  const busyRef = useRef(false)

  const save = useSaveLeaveEncashment()
  const act = useLeaveEncashmentAction()
  const { can } = usePermission()

  const previewParams = {
    leave_type_id: values.leave_type_id,
    //  `0` = chính mình; sửa phiếu thì luôn là người trên phiếu.
    employee_id: request?.employee_id ?? values.employee_id,
    balance_year: values.balance_year,
    reason_kind: values.reason_kind,
  }
  const previewQuery = useLeaveEncashmentPreview(previewParams, can('leave_encashment', 'create'))
  const preview = previewQuery.data
  const previewError = previewQuery.isError ? extractErrorMessage(previewQuery.error) : undefined
  const maxDays = preview && !previewQuery.isFetching ? preview.encashable : null

  const set = <K extends keyof LeaveEncashmentFormValues>(key: K, v: LeaveEncashmentFormValues[K]) =>
    setValues((prev) => ({ ...prev, [key]: v }))

  const run = async (andSubmit: boolean) => {
    if (busyRef.current) return
    const found = validateLeaveEncashmentForm(values, maxDays, Boolean(request))
    setErrors(found)
    if (Object.keys(found).length > 0) return

    busyRef.current = true
    setBusy(true)
    let savedId = 0
    try {
      const saved = request
        ? await save.mutateAsync({ id: request.id, values: toLeaveEncashmentUpdatePayload(values) })
        : await save.mutateAsync({ values: toLeaveEncashmentCreatePayload(values) })
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
  const daysPlaceholder =
    !request && maxDays !== null && maxDays > 0
      ? `Để trống = ${formatEncashDays(maxDays)} ngày`
      : 'VD: 3 hoặc 2,5'

  const actions = (
    <>
      <Button
        type="button"
        variant="outline"
        className={SECONDARY_ACTION_SLOT}
        onClick={() => void run(false)}
        disabled={disabled}
      >
        <Save className="size-4" />
        Lưu nháp
      </Button>
      <Button type="button" className={PRIMARY_ACTION_SLOT} onClick={() => void run(true)} disabled={disabled}>
        <Send className="size-4" />
        Gửi duyệt
      </Button>
    </>
  )

  const body = (
    <>
      {/*  `forceOpen` khi trong nhóm có ô sai: câu lỗi nằm trong nhóm đang gập thì bấm Lưu là không thấy gì (duoc-CR-317). */}
      <FormSection title="Thông tin" forceOpen={Boolean(errors.leave_type_id || errors.note)}>
        <LeaveEncashmentTargetFields
          request={request}
          values={values}
          errors={errors}
          onChange={set}
          today={today}
        />

        <div className="space-y-1.5">
          <EncashFieldLabel
            id="encash-reason-label"
            label="Lý do thanh toán"
            required
            hintId="encash-reason-hint"
            hint="Nghỉ việc cần hồ sơ nhân sự đã ghi ngày nghỉ việc; khi đó được thanh toán hết số ngày chưa nghỉ."
          />
          <RadioGroup
            aria-labelledby="encash-reason-label"
            value={String(values.reason_kind)}
            onValueChange={(v) => set('reason_kind', Number(v))}
            className="flex min-h-9 flex-wrap items-center gap-x-6 gap-y-2"
          >
            {REASONS.map((r) => (
              <div key={r} className="flex items-center gap-2">
                <RadioGroupItem id={`encash-reason-${r}`} value={String(r)} />
                <Label htmlFor={`encash-reason-${r}`} className="font-normal">
                  {LEAVE_ENCASHMENT_REASON_LABELS[r]}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <div className="col-span-full space-y-1.5">
          <EncashFieldLabel label="Ghi chú" htmlFor="encash-note" />
          <Textarea
            id="encash-note"
            rows={3}
            maxLength={ENCASHMENT_NOTE_MAX}
            placeholder="VD: thanh toán phép dư năm 2026 theo chính sách công ty."
            value={values.note}
            onChange={(e) => set('note', e.target.value)}
          />
          <div className="flex justify-between gap-2">
            {errors.note ? (
              <p role="alert" className="text-xs text-destructive">
                {errors.note}
              </p>
            ) : (
              <span />
            )}
            <p className="text-xs text-muted-foreground tabular-nums">
              {values.note.length} / {ENCASHMENT_NOTE_MAX}
            </p>
          </div>
        </div>
      </FormSection>

      <LeaveEncashmentDaysSection
        preview={values.leave_type_id ? preview : undefined}
        previewLoading={Boolean(values.leave_type_id) && previewQuery.isFetching}
        previewError={values.leave_type_id ? previewError : undefined}
        days={values.days}
        error={errors.days}
        required={Boolean(request)}
        placeholder={daysPlaceholder}
        onDaysChange={(d) => set('days', d)}
      />
    </>
  )

  return frame({ actions, body })
}

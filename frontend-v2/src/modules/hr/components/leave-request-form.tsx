import { CalendarDays } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { DatePicker } from '@/shared/ui/date-picker'
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { NumberInput } from '@/shared/ui/number-input'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useEstimateLeaveDays, useLeaveTypes } from '../hooks/use-leave'
import { REASON_MAX, type LeaveFormValues } from '../utils/leave-form-values'
import { LeaveBalanceHintBox } from './leave-balance-hint-box'
import { LeaveHandoverEditor } from './leave-handover-editor'
import { LEAVE_SESSION, LEAVE_SESSION_LABELS, type LeaveRequest } from '../types/leave'

interface LeaveRequestFormProps {
  value: LeaveFormValues
  onChange: (values: LeaveFormValues) => void
  /** Đơn đang sửa — dùng để biết người nghỉ là ai khi hành chính lập hộ. */
  request?: LeaveRequest
}

/**
 * FORM ĐƠN NGHỈ PHÉP — **chỉ dùng khi đơn còn SỬA ĐƯỢC**.
 *
 * Đơn đã gửi duyệt thì trang chi tiết dựng `LeaveRequestSummary`, KHÔNG dựng
 * form này với cờ `readOnly`. Lý do là luật của bộ ERP: ô chỉ xem cấm
 * `<Input disabled>` — `disabled` gỡ luôn khả năng nhận con trỏ nên người dùng
 * không bôi đen, không copy được giá trị, lại còn bị làm mờ nhìn như chữ gợi ý.
 *
 * Bố cục: **một thẻ `FormCard` duy nhất**, lưới hai cột, đọc từ trên xuống theo
 * đúng thứ tự câu hỏi — nghỉ loại gì · mấy ngày · từ bao giờ · vì sao · bàn giao
 * cho ai · gọi ở đâu. Từng cắt thành ba thẻ (*Thông tin nghỉ* · *Bàn giao* ·
 * *Liên hệ*) nhưng hai thẻ sau mỗi thẻ chỉ có một hai ô, nên phần khung viền và
 * tiêu đề chiếm chỗ nhiều hơn phần nội dung.
 *
 * Hai thứ chạy nền ở đây, và cả hai là lý do tồn tại của màn này:
 *
 * 1. **Số ngày tự tính** mỗi khi đổi ngày hoặc buổi — đã trừ T7/CN và ngày lễ
 *    theo `tab_holiday`. Người dùng gõ đè được, vì lịch làm việc thật luôn có
 *    ngoại lệ máy không biết.
 * 2. **Số phép còn lại nằm ngay dưới ô loại nghỉ** (ràng buộc §6.1), chạy hết
 *    bề ngang thẻ. Trước đây nó bị nhét vào một ô lưới cạnh ô loại nghỉ nên
 *    không có nhãn, cao thấp lệch hẳn so với ô bên trái. Doc gọi con số này là
 *    *"chi tiết nhỏ, nhưng nó cắt phần lớn số đơn sai và phần lớn câu hỏi gửi
 *    về phòng Nhân sự"* — nó phải dễ đọc, không phải chỉ cần có mặt.
 */
export function LeaveRequestForm({ value, onChange, request }: LeaveRequestFormProps) {
  const { data: typeData } = useLeaveTypes()
  const types = typeData?.items ?? []

  //  Người dùng đã gõ tay số ngày chưa. Gõ rồi thì thôi ghi đè bằng số máy tính
  //  — ghi đè là họ gõ xong nhìn con số nhảy về chỗ cũ.
  const [manualDays, setManualDays] = useState(false)

  const estimateParams = useMemo(
    () => ({
      from_date: value.from_date,
      to_date: value.to_date,
      leave_type_id: value.leave_type_id || undefined,
      from_session: value.from_session,
      to_session: value.to_session,
      employee_id: request?.employee_id || undefined,
    }),
    [value, request],
  )
  const { data: estimate } = useEstimateLeaveDays(estimateParams)
  const suggestedDays = estimate?.total_days

  useEffect(() => {
    if (manualDays) return
    if (typeof suggestedDays === 'number') {
      onChange({ ...value, total_days: suggestedDays })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ chạy khi con số gợi ý đổi
  }, [suggestedDays, manualDays])

  const set = <K extends keyof LeaveFormValues>(key: K, v: LeaveFormValues[K]) =>
    onChange({ ...value, [key]: v })

  const year = value.from_date ? Number(value.from_date.slice(0, 4)) : new Date().getFullYear()

  return (
    <FormCard title="Đơn nghỉ phép" icon={CalendarDays} iconClassName="text-primary">
      <div className="grid items-start gap-x-4 gap-y-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="leave-type">
            Loại nghỉ
            <RequiredMark />
          </Label>
          <Select
            value={value.leave_type_id ? String(value.leave_type_id) : ''}
            onValueChange={(v) => set('leave_type_id', Number(v))}
          >
            <SelectTrigger id="leave-type" className="w-full">
              <SelectValue placeholder="Chọn loại nghỉ" />
            </SelectTrigger>
            <SelectContent>
              {types.map((t) => (
                <SelectItem key={t.id} value={String(t.id)}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="total-days">
            Tổng số ngày
            <RequiredMark />
          </Label>
          <NumberInput
            value={value.total_days}
            maxDecimals={1}
            placeholder="0"
            onChange={(v) => {
              setManualDays(true)
              set('total_days', v)
            }}
          />
          <p className="text-xs text-muted-foreground">
            {manualDays
              ? `Bạn đang nhập tay. Hệ thống gợi ý ${suggestedDays ?? '—'} ngày.`
              : 'Tự tính, đã trừ thứ Bảy · Chủ nhật · ngày lễ. Sửa được nếu lịch khác.'}
          </p>
        </div>

        {/*  Ràng buộc §6.1 — số phép còn lại chạy hết bề ngang, ngay dưới ô loại
             nghỉ và ô số ngày, đúng hai con số nó đang đối chiếu. */}
        <div className="md:col-span-2">
          <LeaveBalanceHintBox
            leaveTypeId={value.leave_type_id}
            year={year}
            employeeId={request?.employee_id ?? 0}
            requestedDays={value.total_days}
          />
        </div>

        <DateSessionField
          label="Từ ngày"
          date={value.from_date}
          session={value.from_session}
          sessionLabel="Buổi bắt đầu"
          onDateChange={(v) => set('from_date', v)}
          onSessionChange={(v) => set('from_session', v)}
        />

        <DateSessionField
          label="Đến ngày"
          date={value.to_date}
          session={value.to_session}
          sessionLabel="Buổi kết thúc"
          onDateChange={(v) => set('to_date', v)}
          onSessionChange={(v) => set('to_session', v)}
        />

        <div className="space-y-1.5 md:col-span-2">
          <Label htmlFor="reason">
            Lý do nghỉ
            <RequiredMark />
          </Label>
          <Textarea
            id="reason"
            rows={3}
            maxLength={REASON_MAX}
            placeholder="Nêu ngắn gọn lý do để người duyệt không phải hỏi lại."
            value={value.reason}
            onChange={(e) => set('reason', e.target.value)}
          />
          <p className="text-right text-xs text-muted-foreground tabular-nums">
            {value.reason.length} / {REASON_MAX}
          </p>
        </div>

        {/*  Bàn giao và liên hệ là phần HÀNH CHÍNH của tờ đơn — xếp cuối, sau
             khi đã trả lời xong "nghỉ loại gì, mấy ngày, vì sao". */}
        <LeaveHandoverEditor
          value={value.handovers}
          onChange={(rows) => set('handovers', rows)}
          excludeEmployeeId={request?.employee_id ?? 0}
        />

        <div className="space-y-1.5">
          <Label htmlFor="contact-phone">Điện thoại liên hệ khi nghỉ</Label>
          <Input
            id="contact-phone"
            inputMode="tel"
            placeholder="Số gọi được trong thời gian nghỉ"
            value={value.contact_phone}
            onChange={(e) => set('contact_phone', e.target.value)}
          />
        </div>

        <div className="space-y-1.5 md:col-span-2">
          <Label htmlFor="contact-address">Địa chỉ khi nghỉ</Label>
          <Input
            id="contact-address"
            placeholder="Nơi ở trong thời gian nghỉ"
            value={value.contact_address}
            onChange={(e) => set('contact_address', e.target.value)}
          />
        </div>
      </div>
    </FormCard>
  )
}

/**
 * Một ô ngày + ô buổi đứng cùng hàng. Hai ô này luôn đi đôi (nghỉ nửa ngày là
 * chuyện thường), tách rời ra hai dòng thì người dùng chọn ngày xong không thấy
 * ô buổi ở đâu.
 *
 * Ngày dùng `DatePicker`, **không** `<input type="date">` — xem `docs/ui/date.md`:
 * ô ngày của trình duyệt mỗi hệ điều hành vẽ một kiểu, trên Windows còn hiện
 * `mm/dd/yyyy` trong khi cả hệ đọc `dd/mm/yyyy`.
 */
function DateSessionField({
  label,
  date,
  session,
  sessionLabel,
  onDateChange,
  onSessionChange,
}: {
  label: string
  date: string
  session: number
  sessionLabel: string
  onDateChange: (value: string) => void
  onSessionChange: (value: number) => void
}) {
  return (
    <div className="space-y-1.5">
      <Label>
        {label}
        <RequiredMark />
      </Label>
      <div className="grid grid-cols-[minmax(0,1fr)_9rem] gap-2">
        {/*  Ô bắt buộc thì bỏ nút ✕: cho xóa là để người dùng tự tay tạo ra lỗi
             validate (docs/ui/date.md §1). */}
        <DatePicker value={date} onChange={onDateChange} clearable={false} />
        <Select value={String(session)} onValueChange={(v) => onSessionChange(Number(v))}>
          {/*  `SelectValue` sao chép children của mục đang chọn vào ô kích hoạt
               nếu không truyền children tường minh — với mục có phần chú thích
               thì ô hiện hai dòng cụt. Truyền thẳng nhãn (CR-258). */}
          <SelectTrigger className="w-full" aria-label={sessionLabel}>
            <SelectValue>{LEAVE_SESSION_LABELS[session]}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {Object.values(LEAVE_SESSION).map((s) => (
              <SelectItem key={s} value={String(s)}>
                {LEAVE_SESSION_LABELS[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

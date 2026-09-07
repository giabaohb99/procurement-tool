import { CalendarDays } from 'lucide-react'
import { useEffect, useMemo, useRef } from 'react'

import { cn } from '@/shared/utils/cn'
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
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { SearchSelect } from '@/shared/ui/search-select'
import { useEmployees } from '../hooks/use-employees'
import { useEstimateLeaveDays, useLeaveTypes } from '../hooks/use-leave'
import { REASON_MAX, type LeaveFormValues } from '../utils/leave-form-values'
import { LeaveBalanceHintBox } from './leave-balance-hint-box'
import { LeaveHandoverEditor } from './leave-handover-editor'
import {
  LEAVE_SESSION,
  LEAVE_SESSION_LABELS,
  WORK_DAY_LABEL,
  WORK_HOURS_PER_DAY,
  isHourlyLeave,
  type LeaveRequest,
} from '../types/leave'

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

  //  LẬP HỘ — ô «Người nghỉ» chỉ dựng cho người đọc được danh bạ nhân sự. Đó
  //  cũng đúng một trong hai điều kiện backend đòi (`ensure_can_create_for`);
  //  điều kiện còn lại (phạm vi tạo đơn rộng hơn «của mình») backend giữ, vì
  //  giao diện không được là chốt chặn cuối.
  //  ⚠️ Không có quyền thì KHÔNG gọi danh bạ: cứ mount là ăn toast 403, đúng
  //  bẫy đã dính ở tab «Công nợ» của Nhà cung cấp (CR-106).
  const { can } = usePermission()
  const canPickTaker = can('employee', 'read')
  const { data: employeeData } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: canPickTaker },
  )
  const employees = employeeData?.items ?? []
  const employeeOptions = employees.map((e) => ({
    value: String(e.id),
    label: `${e.full_name} (${e.code})`,
  }))

  const isHourly = isHourlyLeave(value.from_session, value.to_session)
  //  NGƯỜI NGHỈ mặc định là CHÍNH MÌNH — đó là đường đi của gần như mọi tờ đơn.
  //  Thứ tự: ô trên form → người của tờ đơn đang sửa → hồ sơ của người đăng nhập.
  //  Để ô trống kèm câu gợi ý "mặc định là bạn" thì người dùng vẫn phải tự đoán
  //  xem đơn sẽ đứng tên ai, và câu đó lại nằm ngay chỗ đáng ra là câu trả lời.
  const { user } = useAuth()
  const takerId = value.employee_id || request?.employee_id || user?.employee_id || 0

  const estimateParams = useMemo(
    () => ({
      from_date: value.from_date,
      to_date: value.to_date,
      leave_type_id: value.leave_type_id || undefined,
      from_session: value.from_session,
      to_session: value.to_session,
      from_time: isHourly ? value.from_time || undefined : undefined,
      to_time: isHourly ? value.to_time || undefined : undefined,
      employee_id: takerId || undefined,
    }),
    //  Chỉ mấy ô này mới đổi con số gợi ý. Phụ thuộc cả `value` thì gõ một chữ
    //  trong ô lý do cũng dựng lại tham số và chạy lại hook truy vấn.
    [
      value.from_date,
      value.to_date,
      value.leave_type_id,
      value.from_session,
      value.to_session,
      value.from_time,
      value.to_time,
      isHourly,
      takerId,
    ],
  )
  const { data: estimate } = useEstimateLeaveDays(estimateParams)
  const suggestedDays = estimate?.total_days

  //  Con số máy vừa tự điền lần gần nhất. So với ô hiện tại để biết người dùng
  //  đã gõ đè hay chưa — KHÔNG dùng cờ `useState` như trước (lỗi báo 05/09/2026):
  //  cờ đó chết theo component, nên mở lại một tờ đơn đã lưu số ngày gõ tay là
  //  cờ về `false` và con số gợi ý đè mất số đã lưu. Người dùng nhập 4, mở lại
  //  thấy 3, lưu xong lại nhảy về 4 — màn hình nói một đằng, sổ sách một nẻo.
  const lastAutoDays = useRef<number | null>(null)

  //  Giá trị form MỚI NHẤT, để effect bên dưới không ghi đè bằng bản chụp cũ:
  //  effect chỉ chạy khi `suggestedDays` đổi, mà giữa hai lần đó người dùng có
  //  thể đã gõ lý do / đổi người bàn giao. Dựng `{...value}` từ bản chụp cũ là
  //  xóa trắng những gì họ vừa gõ.
  //  Gán trong effect chứ không giữa lúc render — đọc/ghi `ref.current` lúc
  //  render là thứ `react-hooks` bắt lỗi, và effect này khai TRƯỚC effect dưới
  //  nên nó luôn chạy trước ở cùng một lượt commit.
  const latestValue = useRef(value)
  useEffect(() => {
    latestValue.current = value
  })

  useEffect(() => {
    if (typeof suggestedDays !== 'number') return
    const current = latestValue.current
    //  Đơn THEO GIỜ không có "số người dùng gõ" để mà giữ — ô đó chỉ xem, con số
    //  là phép chia từ hai đầu giờ. Nên nó luôn bám con số mới.
    //  ⚠️ Thiếu nhánh này thì mở một đơn theo giờ đã lưu rồi đổi ngày/giờ, ô số
    //  ngày đứng im ở giá trị cũ: `lastAutoDays` khởi tạo `null` nên bản thân
    //  con số đã lưu bị coi là "người dùng gõ tay" (bắt được lúc test tay
    //  07/09/2026 — đổi «Đến ngày» sang 09/09 mà vẫn hiện 0.38).
    //
    //  Ngoài ra: `0` = ô trống, chưa ai quyết con số nào. Khác `0` mà cũng khác
    //  con số máy điền lần trước nghĩa là người dùng đã gõ đè — để yên.
    const untouched =
      isHourlyLeave(current.from_session, current.to_session) ||
      current.total_days === 0 ||
      current.total_days === lastAutoDays.current
    if (!untouched) return
    lastAutoDays.current = suggestedDays
    onChange({ ...current, total_days: suggestedDays })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ chạy khi con số gợi ý đổi
  }, [suggestedDays])

  //  "Đang nhập tay" là một SỰ THẬT so sánh được, không phải một cờ nhớ trong
  //  đầu: ô đang khác con số máy tính ra thì đúng là người dùng tự quyết.
  const manualDays = typeof suggestedDays === 'number' && value.total_days !== suggestedDays

  const set = <K extends keyof LeaveFormValues>(key: K, v: LeaveFormValues[K]) =>
    onChange({ ...value, [key]: v })

  /**
   * Đổi ô BUỔI — hai ô buổi và hai ô ngày phải đi cùng nhau khi chọn «Theo giờ».
   *
   * Chọn «Theo giờ» ở một đầu thì đầu kia theo luôn — backend đòi hai ô buổi
   * khai giống nhau, và bắt người dùng chọn hai lần cùng một thứ là thừa. Hai ô
   * NGÀY giữ nguyên: nghỉ theo giờ vắt qua nhiều ngày là hợp lệ.
   * Bỏ «Theo giờ» thì XÓA khoảng giờ: giữ lại là lưu một khoảng giờ mà tờ đơn
   * không còn khai theo giờ nữa.
   */
  const setSession = (which: 'from_session' | 'to_session', next: number) => {
    const other = which === 'from_session' ? 'to_session' : 'from_session'
    if (next === LEAVE_SESSION.HOURLY) {
      onChange({ ...value, [which]: next, [other]: next })
      return
    }
    const leavingHourly = value[other] === LEAVE_SESSION.HOURLY
    onChange({
      ...value,
      [which]: next,
      ...(leavingHourly ? { [other]: LEAVE_SESSION.FULL } : null),
      ...(leavingHourly || isHourly ? { from_time: '', to_time: '' } : null),
    })
  }

  const year = value.from_date ? Number(value.from_date.slice(0, 4)) : new Date().getFullYear()

  return (
    <FormCard title="Đơn nghỉ phép" icon={CalendarDays} iconClassName="text-primary">
      <div className="grid items-start gap-x-4 gap-y-4 md:grid-cols-2">
        {/*  NGƯỜI NGHỈ — chỉ hiện với người được phép lập hộ. Người thường không
             thấy ô này: đơn của họ luôn đứng tên chính họ, bày ra một ô chỉ chọn
             được đúng một giá trị là bắt họ đọc thừa một dòng. */}
        {canPickTaker && (
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="leave-taker">
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
              onChange={(id) => {
                const employeeId = Number(id) || 0
                const picked = employees.find((e) => e.id === employeeId)
                onChange({
                  ...value,
                  employee_id: employeeId,
                  employee_name: picked?.full_name ?? '',
                })
              }}
            />
            <p className="text-xs text-muted-foreground">
              Đơn sẽ đứng tên người này; bạn vẫn là người lập và vẫn theo dõi được nó.
            </p>
          </div>
        )}

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
          {/*  Theo giờ thì con số này là PHÉP CHIA từ hai đầu giờ, không cho gõ
               đè: người dùng đã chọn giờ rồi, thêm một con số thứ ba là mở đường
               cho tờ đơn nghỉ 2 tiếng trừ 3 ngày phép (backend cũng bỏ qua số
               gõ tay ở nhánh này). Ô chỉ xem dùng `ReadOnlyValue`, KHÔNG dùng
               `<Input disabled>` — xem docstring đầu tệp. */}
          {isHourly ? (
            <ReadOnlyValue>{value.total_days} ngày</ReadOnlyValue>
          ) : (
            <NumberInput
              id="total-days"
              value={value.total_days}
              maxDecimals={1}
              placeholder="0"
              onChange={(v) => set('total_days', v)}
            />
          )}
          <p className="text-xs text-muted-foreground">
            {isHourly
              ? `Quy đổi từ khoảng giờ đã chọn, theo ngày công ${WORK_HOURS_PER_DAY} giờ.`
              : manualDays
                ? `Bạn đang nhập tay. Hệ thống gợi ý ${suggestedDays ?? '—'} ngày.`
                : 'Tự tính, đã trừ thứ Bảy · Chủ nhật · ngày lễ. Sửa được nếu lịch khác.'}
          </p>
        </div>

        {/*  Ràng buộc §6.1 — số phép còn lại chạy hết bề ngang, ngay dưới ô loại
             nghỉ và ô số ngày, đúng hai con số nó đang đối chiếu. */}
        <div className="md:col-span-2">
          {/*  Quỹ phép của NGƯỜI NGHỈ, không phải của người đang lập: lập hộ
               mà hiện quỹ của chính mình thì con số đối chiếu vô nghĩa, tệ hơn
               là nó khiến người lập tưởng người kia còn phép. */}
          <LeaveBalanceHintBox
            leaveTypeId={value.leave_type_id}
            year={year}
            employeeId={takerId}
            requestedDays={value.total_days}
          />
        </div>

        {/*  Hai đầu ngày GIỮ NGUYÊN khi chọn «Theo giờ», chỉ mọc thêm ô giờ:
             nghỉ *từ 14:00 ngày 07 đến 10:00 ngày 09* là tờ đơn có thật, gộp hai
             ô ngày làm một là cắt mất đúng ca đó. */}
        <DateSessionField
          label="Từ ngày"
          date={value.from_date}
          session={value.from_session}
          sessionLabel="Buổi bắt đầu"
          time={isHourly ? value.from_time : undefined}
          timeLabel="Từ giờ"
          onDateChange={(v) => set('from_date', v)}
          onSessionChange={(v) => setSession('from_session', v)}
          onTimeChange={(v) => set('from_time', v)}
        />

        <DateSessionField
          label="Đến ngày"
          date={value.to_date}
          session={value.to_session}
          sessionLabel="Buổi kết thúc"
          time={isHourly ? value.to_time : undefined}
          timeLabel="Đến giờ"
          onDateChange={(v) => set('to_date', v)}
          onSessionChange={(v) => setSession('to_session', v)}
          onTimeChange={(v) => set('to_time', v)}
        />

        {isHourly && (
          <p className="text-xs text-muted-foreground md:col-span-2">
            Nghỉ theo giờ quy đổi theo ngày công {WORK_HOURS_PER_DAY} giờ ({WORK_DAY_LABEL}),
            đã trừ giờ nghỉ trưa. Vắt qua nhiều ngày cũng được: ngày đầu tính tới hết giờ
            làm, ngày cuối tính từ đầu giờ làm.
          </p>
        )}

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
          excludeEmployeeId={takerId}
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
  time,
  timeLabel,
  onDateChange,
  onSessionChange,
  onTimeChange,
}: {
  label: string
  date: string
  session: number
  sessionLabel: string
  /** Có giá trị = buổi đang là «Theo giờ» → mọc thêm ô giờ ở cuối hàng. */
  time?: string
  timeLabel?: string
  onDateChange: (value: string) => void
  onSessionChange: (value: number) => void
  onTimeChange?: (value: string) => void
}) {
  const withTime = time !== undefined
  return (
    <div className="space-y-1.5">
      <Label>
        {label}
        <RequiredMark />
      </Label>
      {/*  Ô giờ chen vào CÙNG MỘT HÀNG với ngày và buổi: ba thứ đó là một câu
           trả lời («nghỉ từ lúc nào»), tách xuống dòng thì mắt phải ghép lại. */}
      <div
        className={cn(
          'grid gap-2',
          withTime
            ? 'grid-cols-[minmax(0,1fr)_8rem_7rem]'
            : 'grid-cols-[minmax(0,1fr)_9rem]',
        )}
      >
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
        {withTime && (
          <Input
            type="time"
            aria-label={timeLabel}
            value={time}
            onChange={(e) => onTimeChange?.(e.target.value)}
          />
        )}
      </div>
    </div>
  )
}

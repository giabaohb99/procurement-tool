import { CalendarDays } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { extractErrorMessage } from '@/core/api'
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { SearchSelect } from '@/shared/ui/search-select'
import { useEmployees } from '../hooks/use-employees'
import { useEstimateLeavePeriods, useLeaveTypes } from '../hooks/use-leave'
import {
  REASON_MAX,
  isHourlyForm,
  outerRangeOf,
  type LeaveFormValues,
} from '../utils/leave-form-values'
import { daysInRowOrder, overlappingPeriodIndexes } from '../utils/leave-periods'
import { LeaveHandoverEditor } from './leave-handover-editor'
import { LeaveRequestLinesEditor } from './leave-request-lines-editor'
import { LeaveRequestPeriodsEditor } from './leave-request-periods-editor'
import type { LeaveRequest } from '../types/leave'

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

  const isHourly = isHourlyForm(value)
  //  NGƯỜI NGHỈ mặc định là CHÍNH MÌNH — đó là đường đi của gần như mọi tờ đơn.
  //  Thứ tự: ô trên form → người của tờ đơn đang sửa → hồ sơ của người đăng nhập.
  //  Để ô trống kèm câu gợi ý "mặc định là bạn" thì người dùng vẫn phải tự đoán
  //  xem đơn sẽ đứng tên ai, và câu đó lại nằm ngay chỗ đáng ra là câu trả lời.
  const { user } = useAuth()
  const takerId = value.employee_id || request?.employee_id || user?.employee_id || 0

  //  Loại nghỉ dùng để tra số ngày gợi ý: lấy dòng ĐẦU. Nó chỉ quyết định một
  //  thứ — có trừ ngày lễ hay không (`exclude_holiday`) — và đơn nhiều loại thì
  //  con số gợi ý cũng chỉ là mốc đối chiếu, không phải con số đi vào sổ.
  const firstTypeId = value.lines[0]?.leave_type_id ?? 0

  //  Hai khoảng chồng ngày thì form đã báo đỏ dưới hàng — gọi ước lượng chỉ để ăn đúng câu
  //  lỗi đó lần nữa, nên tắt.
  const overlaps = overlappingPeriodIndexes(value.periods)
  const estimateQuery = useEstimateLeavePeriods({
    employee_id: takerId || undefined,
    leave_type_id: firstTypeId || undefined,
    periods: value.periods,
    from_time: isHourly ? value.from_time || undefined : undefined,
    to_time: isHourly ? value.to_time || undefined : undefined,
    enabled: overlaps.size === 0,
  })
  const estimate = estimateQuery.data
  const rowDays = daysInRowOrder(value.periods, estimate?.periods)
  const estimateError = estimateQuery.error ? extractErrorMessage(estimateQuery.error) : undefined
  const suggestedDays = estimate?.total_days
  //  Tùy chọn: backend cũ chưa trả tên lịch thì câu chữ rơi về dạng chung, form vẫn chạy.
  const scheduleName = estimate?.schedule_name

  //  Con số máy vừa tự điền lần gần nhất nằm ở `value.auto_days` (trong giá trị form, không
  //  phải cờ `useState` như trước — lỗi báo 05/09/2026: cờ đó chết theo component, nên mở lại
  //  một tờ đơn đã lưu số ngày gõ tay là cờ về `false` và con số gợi ý đè mất số đã lưu).
  //  So ô hiện tại với nó để biết người dùng đã gõ đè hay chưa. `formValuesOf` gieo sẵn nó cho
  //  đơn nhiều khoảng đã lưu mà chưa gõ đè (duoc-CR-683 M3); đơn một khoảng thì xem
  //  `firstEstimate` bên dưới.

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

  //  Con số ước lượng ĐẦU TIÊN của lần mở form. Đơn đã lưu mà số ngày trùng đúng con số đó thì
  //  coi như máy điền (chưa gõ đè) — cách duy nhất nhận ra ở đơn MỘT khoảng, vì backend lưu ngày
  //  của khoảng = tổng dòng nên `formValuesOf` không phân biệt được (duoc-CR-683 M3).
  //  Khác con số đó thì vẫn là số gõ tay, để yên — đúng ca NP025 (gõ 4, máy tính 3).
  const firstEstimate = useRef(true)
  //  Con số máy điền lần gần nhất CỦA LẦN MỞ FORM NÀY. Lưu đơn mới xong trang nạp lại form từ
  //  bản đã lưu (`formValuesOf`) — với đơn một khoảng thì `auto_days` về `null`, nhưng con số
  //  trên ô vẫn là con số máy vừa điền, nên đổi ngày sau đó vẫn phải bám theo.
  const lastAutoDays = useRef<number | null>(null)

  useEffect(() => {
    if (typeof suggestedDays !== 'number') return
    const isFirst = firstEstimate.current
    firstEstimate.current = false
    const current = latestValue.current
    //  ⚠️ CHỈ đơn MỘT dòng mới tự điền. Nhiều loại nghỉ thì máy không đoán được
    //  chia 4 ngày thành 3+1 hay 2+2 — đè con số gợi ý lên một dòng bất kỳ là
    //  âm thầm sửa vào phần quỹ người dùng vừa phân bổ.
    if (current.lines.length !== 1) return
    const line = current.lines[0]

    //  Đơn THEO GIỜ không có "số người dùng gõ" để mà giữ — ô đó chỉ xem, con số
    //  là phép chia từ hai đầu giờ. Nên nó luôn bám con số mới.
    //  ⚠️ Thiếu nhánh này thì mở một đơn theo giờ đã lưu rồi đổi ngày/giờ, ô số
    //  ngày đứng im ở giá trị cũ (bắt được lúc test tay 07/09/2026 — đổi «Đến
    //  ngày» sang 09/09 mà vẫn hiện 0.38).
    //
    //  Ngoài ra: `0` = ô trống, chưa ai quyết con số nào. Khác `0` mà cũng khác
    //  con số máy điền lần trước nghĩa là người dùng đã gõ đè — để yên.
    const untouched =
      isHourlyForm(current) ||
      line.days === 0 ||
      line.days === current.auto_days ||
      line.days === lastAutoDays.current ||
      (isFirst && line.days === suggestedDays)
    if (!untouched) return
    lastAutoDays.current = suggestedDays
    if (line.days === suggestedDays && current.auto_days === suggestedDays) return
    onChange({ ...current, auto_days: suggestedDays, lines: [{ ...line, days: suggestedDays }] })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ chạy khi con số gợi ý đổi
  }, [suggestedDays])

  const set = <K extends keyof LeaveFormValues>(key: K, v: LeaveFormValues[K]) =>
    onChange({ ...value, [key]: v })

  //  Năm của quỹ phép đối chiếu = năm của ngày nghỉ ĐẦU TIÊN (đơn nhiều khoảng phải cùng năm).
  const firstDate = outerRangeOf(value.periods).from_date
  const year = firstDate ? Number(firstDate.slice(0, 4)) : new Date().getFullYear()

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

        {/*  Bảng LOẠI NGHỈ — một đơn khai được nhiều loại (07/09/2026). Số phép
             còn lại nằm ngay dưới từng dòng, đúng ràng buộc §6.1: mỗi loại một
             sổ quỹ riêng nên một hộp chung ở cuối bảng không trả lời được câu
             người dùng đang hỏi.
             Quỹ phép hiện là của NGƯỜI NGHỈ, không phải của người đang lập: lập
             hộ mà hiện quỹ của chính mình thì con số đối chiếu vô nghĩa, tệ hơn
             là nó khiến người lập tưởng người kia còn phép. */}
        <LeaveRequestLinesEditor
          value={value.lines}
          onChange={(lines) => set('lines', lines)}
          types={types}
          year={year}
          employeeId={takerId}
          suggestedDays={suggestedDays}
          scheduleName={scheduleName}
          isHourly={isHourly}
        />

        {/*  KHOẢNG NGÀY (duoc-CR-683) — đơn một khoảng vẫn là hai ô «Từ ngày» · «Đến
             ngày» như cũ; «+ Thêm khoảng ngày» mọc thêm hàng cho đơn nghỉ không liền. */}
        <LeaveRequestPeriodsEditor
          periods={value.periods}
          fromTime={value.from_time}
          toTime={value.to_time}
          rowDays={rowDays}
          totalDays={estimate?.total_days}
          estimateError={estimateError}
          onChange={(patch) => onChange({ ...value, ...patch })}
        />

        {isHourly && (
          <p className="text-xs text-muted-foreground md:col-span-2">
            Nghỉ theo giờ quy đổi theo giờ làm của{' '}
            {scheduleName ? `lịch «${scheduleName}»` : 'lịch làm việc áp cho người nghỉ'}, đã trừ
            giờ nghỉ trưa. Vắt qua nhiều ngày cũng được: ngày đầu tính tới hết giờ làm, ngày cuối
            tính từ đầu giờ làm.
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

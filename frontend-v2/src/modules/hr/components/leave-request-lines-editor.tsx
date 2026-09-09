import { Plus, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Label } from '@/shared/ui/label'
import { NumberInput } from '@/shared/ui/number-input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import {
  MAX_LEAVE_LINES,
  totalLeaveDays,
  type LeaveLineValue,
} from '../utils/leave-form-values'
import type { LeaveType } from '../types/leave'
import { LeaveBalanceHintBox } from './leave-balance-hint-box'

interface LeaveRequestLinesEditorProps {
  value: LeaveLineValue[]
  onChange: (lines: LeaveLineValue[]) => void
  types: LeaveType[]
  /** Năm để tra quỹ phép — lấy từ «Từ ngày» của đơn. */
  year: number
  /** NGƯỜI NGHỈ; quỹ phép hiện là của họ, không phải của người đang lập. */
  employeeId: number
  /** Số ngày máy tính được cho khoảng đang chọn. `undefined` = chưa tra xong. */
  suggestedDays?: number
  /** Đơn khai theo GIỜ: khóa còn một dòng, số ngày là phép chia nên chỉ xem. */
  isHourly: boolean
}

/**
 * BẢNG LOẠI NGHỈ của tờ đơn — *"3 ngày phép năm + 1 ngày không lương"* (07/09/2026).
 *
 * Trước đợt này chỗ đây là một ô chọn loại nghỉ và một ô tổng số ngày. Nay mỗi
 * loại một dòng, và **tổng số ngày là con số cộng lại, không còn ô nhập riêng**:
 * hai nguồn cho cùng một con số thì cái thứ hai sẽ lệch, và cái lệch đó đi
 * thẳng vào sổ quỹ phép.
 *
 * Bố cục là **một bảng thật** — hàng tiêu đề, các dòng, hàng chân. Bản đầu bày
 * ba thứ rời nhau (nút *Thêm loại nghỉ* dạt sang mép phải cách bảng cả một
 * khoảng, ô số ngày không nhãn nên đọc ra như một ô «0» vô danh, và hộp gợi ý
 * quỹ phép viền đứt chiếm trọn một hàng ngay cả khi chưa chọn loại nào) —
 * khách bác đúng chỗ đó.
 *
 * Bốn điều đáng chú ý:
 *
 * 1. **Cột «Số ngày» có tiêu đề.** Ô số không nhãn nằm cạnh một ô chọn là chỗ
 *    người dùng phải đoán, và trình đọc màn hình thì đọc ra một ô trống.
 * 2. **Hộp quỹ phép chỉ mọc khi ĐÃ chọn loại.** Chưa chọn thì nó chỉ nói lại
 *    đúng thứ ô bên cạnh đang nói, mà lại chiếm một hàng viền đứt.
 * 3. **Đơn một dòng thì số ngày tự điền**, y như ô tổng số ngày cũ. Đơn nhiều
 *    dòng thì không tự điền: máy không đoán được chia 4 ngày thành 3+1 hay 2+2,
 *    và đoán sai là trừ nhầm quỹ của người ta.
 * 4. **Nghỉ theo giờ khóa còn một dòng** — số ngày là phép chia từ hai đầu giờ,
 *    ô đó chỉ xem. Dùng `ReadOnlyValue`, KHÔNG `<Input disabled>`: `disabled`
 *    gỡ luôn khả năng bôi đen nên người dùng không copy được giá trị.
 */
export function LeaveRequestLinesEditor({
  value,
  onChange,
  types,
  year,
  employeeId,
  suggestedDays,
  isHourly,
}: LeaveRequestLinesEditorProps) {
  const total = totalLeaveDays(value)
  const canAdd = !isHourly && value.length < MAX_LEAVE_LINES
  //  Chỉ đối chiếu khi có TỪ HAI DÒNG: đơn một dòng đã tự bám con số máy tính,
  //  nói thêm "khác gợi ý" ở đó là nhắc lại thứ người dùng vừa cố ý sửa.
  const mismatch =
    value.length > 1 && typeof suggestedDays === 'number' && total !== suggestedDays

  const setLine = (index: number, patch: Partial<LeaveLineValue>) =>
    onChange(value.map((line, i) => (i === index ? { ...line, ...patch } : line)))

  const addLine = () => onChange([...value, { leave_type_id: 0, days: 0 }])

  const removeLine = (index: number) => onChange(value.filter((_, i) => i !== index))

  //  Loại đã chọn ở dòng khác thì không cho chọn lại — backend chặn với câu
  //  «khai hai lần», nhưng để người dùng chọn xong mới báo là bắt họ làm hai lần.
  const takenElsewhere = (index: number, typeId: number) =>
    value.some((line, i) => i !== index && line.leave_type_id === typeId)

  //  Ba cột dùng CHUNG một khai báo lưới cho hàng tiêu đề và mọi dòng — khai hai
  //  lần là tiêu đề «Số ngày» trôi khỏi ô số ngay lần đầu ai đó chỉnh bề rộng.
  //  Cột «Số ngày» hẹp lại trên điện thoại: 7rem cho một con số một chữ số là
  //  thừa, mà phần thừa đó lấy đúng từ ô CHỌN LOẠI NGHỈ — thứ duy nhất ở hàng
  //  này có chữ dài ("Nghỉ không lương" cụt thành "Nghỉ khô…" trên màn 390px).
  const grid =
    'grid grid-cols-[minmax(0,1fr)_4.5rem_2rem] items-center gap-2 sm:grid-cols-[minmax(0,1fr)_7rem_2rem]'

  return (
    <div className="space-y-1.5 md:col-span-2">
      <Label>
        Loại nghỉ
        <RequiredMark />
      </Label>

      <div className="overflow-hidden rounded-md border">
        <div
          className={cn(
            grid,
            'border-b bg-muted/40 px-3 py-1.5 text-xs font-medium text-muted-foreground',
          )}
        >
          <span>Nghỉ loại gì</span>
          <span className="text-right">Số ngày</span>
          <span />
        </div>

        <div className="divide-y">
          {value.map((line, index) => (
            <div key={index} className="space-y-2 px-3 py-2.5">
              <div className={grid}>
                <Select
                  value={line.leave_type_id ? String(line.leave_type_id) : ''}
                  onValueChange={(v) => setLine(index, { leave_type_id: Number(v) })}
                >
                  <SelectTrigger
                    className="w-full"
                    aria-label={`Loại nghỉ dòng ${index + 1}`}
                  >
                    <SelectValue placeholder="Chọn loại nghỉ" />
                  </SelectTrigger>
                  <SelectContent>
                    {types.map((t) => (
                      <SelectItem
                        key={t.id}
                        value={String(t.id)}
                        disabled={takenElsewhere(index, t.id)}
                      >
                        {t.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {isHourly ? (
                  <ReadOnlyValue>{line.days}</ReadOnlyValue>
                ) : (
                  <NumberInput
                    value={line.days}
                    maxDecimals={2}
                    placeholder="0"
                    className="text-right"
                    aria-label={`Số ngày dòng ${index + 1}`}
                    onChange={(v) => setLine(index, { days: v })}
                  />
                )}

                {/*  Nút bỏ dòng chỉ có nghĩa khi CÒN dòng khác. Đơn một loại mà
                     bày nút xóa ra thì bấm vào là mất trắng ô chọn, trong khi
                     việc người dùng muốn là ĐỔI loại — làm bằng chính ô chọn. */}
                {value.length > 1 ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8"
                    aria-label={`Bỏ dòng ${index + 1}`}
                    onClick={() => removeLine(index)}
                  >
                    <X className="size-4" />
                  </Button>
                ) : (
                  <span />
                )}
              </div>

              {/*  Ràng buộc §6.1 — số phép còn lại của ĐÚNG loại ở dòng này.
                   Chưa chọn loại thì không dựng: hộp lúc đó chỉ nói lại đúng
                   thứ ô chọn bên trên đang nói. */}
              {line.leave_type_id > 0 && (
                <LeaveBalanceHintBox
                  leaveTypeId={line.leave_type_id}
                  year={year}
                  employeeId={employeeId}
                  requestedDays={line.days}
                />
              )}
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 border-t bg-muted/20 px-3 py-1.5">
          {canAdd ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="-ml-2 h-7 text-primary"
              onClick={addLine}
            >
              <Plus className="size-4" />
              Thêm loại nghỉ
            </Button>
          ) : (
            <span />
          )}
          {/*  Một chuỗi liền, không tách thẻ: «Tổng cộng» và con số đọc thành
               một câu, mà tách ra thì khoảng cách giữa hai thẻ cũng phải canh. */}
          <span className="text-sm font-medium tabular-nums">{`Tổng cộng ${total} ngày`}</span>
        </div>
      </div>

      <p
        className={cn(
          'text-xs',
          mismatch ? 'text-amber-600 dark:text-amber-400' : 'text-muted-foreground',
        )}
      >
        {isHourly
          ? 'Quy đổi từ khoảng giờ đã chọn — không sửa đè được.'
          : typeof suggestedDays !== 'number'
            ? 'Đang tính số ngày công của khoảng đã chọn…'
            : mismatch
              ? //  Cảnh báo, KHÔNG chặn: lịch làm việc thật luôn có ngoại lệ máy
                //  không biết (ca kíp, nghỉ bù, công trường chạy Chủ nhật).
                `Tổng ${total} ngày khác số ngày công của khoảng (${suggestedDays} ngày) — kiểm lại nếu không cố ý.`
              : //  ⚠️ Nói ĐÚNG lịch của công ty: DEGO làm cả thứ Bảy, chỉ nghỉ
                //  Chủ nhật (`workday_service.WEEKEND_DAYS`). Câu cũ ghi "đã
                //  trừ thứ Bảy" nên người dùng đọc xong tưởng máy tính hụt và
                //  gõ đè thêm một ngày — chữ sai đẻ ra số sai.
                `Khoảng ngày đã chọn có ${suggestedDays} ngày công (đã trừ Chủ nhật và ngày lễ; thứ Bảy vẫn tính vì công ty làm cả T7).`}
      </p>
    </div>
  )
}

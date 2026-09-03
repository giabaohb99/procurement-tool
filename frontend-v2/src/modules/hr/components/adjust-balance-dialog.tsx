import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'
import { useAdjustLeaveBalance } from '../hooks/use-leave'
import type { LeaveBalance } from '../types/leave'

interface AdjustBalanceDialogProps {
  /** `null` = hộp đóng. Truyền dòng quỹ vào là mở. */
  balance: LeaveBalance | null
  onClose: () => void
}

const NOTE_MAX = 500

/**
 * ĐIỀU CHỈNH TAY quỹ phép — thao tác nhạy cảm nhất của cả phân hệ.
 *
 * Ba chi tiết cố ý:
 *
 * 1. **Ghi ĐÈ, không cộng dồn.** Người dùng nhìn con số hiện tại trên màn hình
 *    và gõ con số họ muốn nó thành. Cộng dồn thì bấm Lưu hai lần là gấp đôi, và
 *    không ai đoán được điều đó từ giao diện.
 * 2. **Nhận số ÂM.** Đây là cột duy nhất trừ được — dùng khi cấp nhầm.
 * 3. **Bắt buộc có lý do.** Đây là tặng ngày phép; phải truy được ai làm và vì
 *    sao. Backend chặn lớp thứ hai và ghi câu này vào `tab_audit_log`.
 */
export function AdjustBalanceDialog({ balance, onClose }: AdjustBalanceDialogProps) {
  const adjust = useAdjustLeaveBalance()
  const [days, setDays] = useState(0)
  const [note, setNote] = useState('')

  //  Nạp lại mỗi khi mở sang MỘT DÒNG KHÁC. Không đồng bộ thì mở dòng thứ hai
  //  vẫn thấy số của dòng trước, và bấm Lưu là ghi đè nhầm người.
  //
  //  Đặt ngay trong lúc render (`useHasChanged`) chứ không trong `useEffect`:
  //  effect chạy SAU khi đã commit nên người dùng thấy một khung hình mang số
  //  của dòng TRƯỚC rồi mới thấy số đúng. Xem `shared/hooks/use-has-changed.ts`.
  if (useHasChanged(balance?.id ?? 0) && balance) {
    setDays(balance.adjusted_days)
    setNote(balance.note ?? '')
  }

  if (!balance) return null

  const canSave = note.trim().length > 0 && !adjust.isPending
  //  Xem trước kết quả: người dùng gõ số điều chỉnh nhưng thứ họ quan tâm là
  //  «còn lại» sẽ thành bao nhiêu. Bắt họ tự cộng trừ là bắt họ tính sai.
  const preview =
    Math.round((balance.remaining_days - balance.adjusted_days + days) * 100) / 100

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Điều chỉnh quỹ phép</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Nhân sự</Label>
              <ReadOnlyValue>
                {balance.employee_name || `#${balance.employee_id}`}
              </ReadOnlyValue>
            </div>
            <div className="space-y-1.5">
              <Label>Loại nghỉ · năm</Label>
              <ReadOnlyValue>
                {balance.leave_type_name || `#${balance.leave_type_id}`} · {balance.year}
              </ReadOnlyValue>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="adjust-days">
              Số ngày điều chỉnh
              <RequiredMark hint="Số dương là cộng thêm, số âm là trừ bớt" />
            </Label>
            <Input
              id="adjust-days"
              type="number"
              step={0.5}
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Số dương cộng thêm, số âm trừ bớt. Ô này <strong>ghi đè</strong> lần điều chỉnh
              trước ({balance.adjusted_days} ngày), không cộng dồn. Sau khi lưu, số ngày còn lại
              sẽ là <strong className="tabular-nums">{preview}</strong>.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="adjust-note">
              Lý do điều chỉnh
              <RequiredMark hint="Bắt buộc — thao tác này được ghi vào dấu vết hệ thống" />
            </Label>
            <Textarea
              id="adjust-note"
              rows={3}
              maxLength={NOTE_MAX}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="VD: Bù 2 ngày phép tồn năm 2025 theo quyết định số…"
            />
            <p className="text-right text-xs text-muted-foreground">
              {note.length} / {NOTE_MAX}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Đóng
          </Button>
          <Button
            disabled={!canSave}
            onClick={() =>
              adjust.mutate(
                { id: balance.id, values: { adjusted_days: days, note: note.trim() } },
                { onSuccess: onClose },
              )
            }
          >
            Lưu điều chỉnh
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'
import type { LeaveBalanceAdjustForm } from '../hooks/use-leave-balance-adjust-form'
import type { LeaveBalance } from '../types/leave'

interface LeaveBalanceAdjustCardProps {
  balance: LeaveBalance
  /** Trạng thái dùng chung với nút Lưu trên đầu trang — xem hook cùng tên. */
  form: LeaveBalanceAdjustForm
}

const NOTE_MAX = 500

/**
 * ĐIỀU CHỈNH TAY quỹ phép — thao tác nhạy cảm nhất của cả phân hệ.
 *
 * ⚠️ Là một THẺ TRONG TRANG chứ không phải hộp thoại (đổi 03/09/2026). Hộp
 * thoại buộc phải gói gọn, nên mọi thứ giải thích cho con số đang sửa — phân rã
 * quỹ, những đơn đã nghỉ trong năm — đều nằm ngoài nó; người dùng đóng hộp ra
 * xem rồi mở lại, và lúc mở lại thì phải nhớ mình vừa đọc gì.
 *
 * Ba chi tiết cố ý:
 *
 * 1. **Ghi ĐÈ, không cộng dồn.** Người dùng nhìn con số hiện tại trên màn hình
 *    và gõ con số họ muốn nó thành. Cộng dồn thì bấm Lưu hai lần là gấp đôi, và
 *    không ai đoán được điều đó từ giao diện.
 * 2. **Nhận số ÂM.** Đây là cột duy nhất trừ được — dùng khi cấp nhầm.
 * 3. **Bắt buộc có lý do.** Đây là tặng ngày phép; phải truy được ai làm và vì
 *    sao. Backend chặn lớp thứ hai và ghi câu này vào `tab_audit_log`.
 *
 * ⚠️ Nút Lưu KHÔNG nằm ở đây (dời 04/09/2026): nó ở đầu trang, cùng hàng với
 * tiêu đề và dính khi cuộn — trang này có bốn thẻ nên nút nằm dưới đáy thẻ thứ
 * ba là mỗi lần lưu một lần cuộn xuống rồi cuộn ngược lên. Trạng thái chung nằm
 * ở `useLeaveBalanceAdjustForm`.
 */
export function LeaveBalanceAdjustCard({ balance, form }: LeaveBalanceAdjustCardProps) {
  const { days, setDays, note, setNote, preview } = form

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Điều chỉnh tay</CardTitle>
        <p className="text-sm text-muted-foreground">
          Cộng hoặc trừ ngày phép ngoài hạn mức. Thao tác này ghi vào dấu vết hệ thống.
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="adjust-days">
            Số ngày điều chỉnh
            <RequiredMark hint="Số dương là cộng thêm, số âm là trừ bớt" />
          </Label>
          <Input
            id="adjust-days"
            type="number"
            step={0.5}
            className="max-w-40"
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
      </CardContent>
    </Card>
  )
}

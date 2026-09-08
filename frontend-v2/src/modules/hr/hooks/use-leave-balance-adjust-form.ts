import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { useAdjustLeaveBalance } from './use-leave'
import type { LeaveBalance } from '../types/leave'

/**
 * Trạng thái của form ĐIỀU CHỈNH TAY quỹ phép.
 *
 * ⚠️ Tách khỏi `LeaveBalanceAdjustCard` vì **nút Lưu không còn nằm trong thẻ**
 * (đổi 04/09/2026): nút lên đầu trang cùng hàng với tiêu đề, còn các ô nhập ở
 * lại trong thẻ — hai chỗ cách nhau cả màn hình nhưng phải đọc chung một trạng
 * thái (`canSave` khóa nút khi chưa ghi lý do). Nhét state vào một trong hai
 * component rồi bắn ngược lên là sớm muộn lệch nhau.
 */
export interface LeaveBalanceAdjustForm {
  days: number
  setDays: (value: number) => void
  note: string
  setNote: (value: string) => void
  /** Đủ điều kiện gửi: có lý do và không đang gửi dở. */
  canSave: boolean
  isPending: boolean
  /** Số ngày CÒN LẠI sau khi lưu — xem trước để người dùng khỏi tự tính. */
  preview: number
  submit: () => void
}

export function useLeaveBalanceAdjustForm(balance: LeaveBalance): LeaveBalanceAdjustForm {
  const adjust = useAdjustLeaveBalance()
  //  Bấm ba lần liên tiếp không đẻ bản ghi trùng (PATCH ghi đè) nhưng đẻ BA
  //  dòng dấu vết giống hệt nhau — xem `useSingleFlight`.
  const once = useSingleFlight()
  const [days, setDays] = useState(balance.adjusted_days)
  const [note, setNote] = useState(balance.note ?? '')

  //  Nạp lại khi chuyển sang MỘT DÒNG QUỸ KHÁC. Đặt ngay trong lúc render
  //  (`useHasChanged`) chứ không trong `useEffect`: effect chạy SAU khi đã
  //  commit nên người dùng thấy một khung hình mang số của dòng TRƯỚC.
  if (useHasChanged(balance.id)) {
    setDays(balance.adjusted_days)
    setNote(balance.note ?? '')
  }

  return {
    days,
    setDays,
    note,
    setNote,
    canSave: note.trim().length > 0 && !adjust.isPending,
    isPending: adjust.isPending,
    //  Người dùng gõ số điều chỉnh nhưng thứ họ quan tâm là «còn lại» sẽ thành
    //  bao nhiêu. Bắt họ tự cộng trừ là bắt họ tính sai.
    preview: Math.round((balance.remaining_days - balance.adjusted_days + days) * 100) / 100,
    submit: () =>
      void once(
        () =>
          new Promise<void>((resolve) => {
            adjust.mutate(
              { id: balance.id, values: { adjusted_days: days, note: note.trim() } },
              { onSettled: () => resolve() },
            )
          }),
      ),
  }
}

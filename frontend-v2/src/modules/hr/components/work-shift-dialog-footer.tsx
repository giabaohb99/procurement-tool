import { Button } from '@/shared/ui/button'
import { RESET_PAST_HINT } from '../utils/work-shift-access'
import type { ShiftSubmitState } from '../utils/work-shift-submit-state'

interface WorkShiftDialogFooterProps {
  readOnly: boolean
  onClose: () => void
  /** Ô có ca riêng VÀ người xem có quyền gỡ — mới bày nút "Về mẫu tuần". */
  showReset: boolean
  /** Ngày đã qua / hôm nay: nút "Về mẫu tuần" tắt kèm lý do (backend 422 với mọi người). */
  resetBlocked: boolean
  onReset: () => void
  /** Đang gửi một lượt ghi. */
  pending: boolean
  /** Nhãn + bấm được + lý do tắt của nút chính (`resolveShiftSubmit`). */
  submit: ShiftSubmitState
  onSubmit: () => void
}

/**
 * Chân hộp xếp ca (duoc-CR-761, bản làm lại 16/11/2026) — MỘT bố cục duy nhất, không đổi theo phần "Áp cùng ca":
 * màn rộng: trái "Về mẫu tuần", phải [lý do tắt] Hủy · nút chính; điện thoại (tấm trượt): lý do ở trên, nút chính rồi
 * Hủy rồi "Về mẫu tuần" xếp chồng hết bề ngang. Nút chính nói đúng việc ("Lưu" / "Lưu cho N ô"); tắt thì luôn có câu
 * lý do và vẫn đọc rõ (nền xám chữ xám đậm, không mờ 50% trên nền xanh). Chỉ xem thì một nút Đóng.
 */
export function WorkShiftDialogFooter({
  readOnly,
  onClose,
  showReset,
  resetBlocked,
  onReset,
  pending,
  submit,
  onSubmit,
}: WorkShiftDialogFooterProps) {
  if (readOnly) {
    return (
      <div className="flex border-t px-5 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
        <Button type="button" variant="outline" className="max-md:w-full md:ml-auto" onClick={onClose}>
          Đóng
        </Button>
      </div>
    )
  }
  return (
    <div className="space-y-2 border-t bg-background px-5 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      {showReset && resetBlocked && <p className="text-xs text-muted-foreground">{RESET_PAST_HINT}</p>}
      <div className="flex gap-2 max-md:flex-col md:items-center">
        {showReset && (
          <Button
            type="button"
            variant="ghost"
            className="max-md:order-4 max-md:w-full"
            disabled={pending || resetBlocked}
            onClick={onReset}
          >
            Về mẫu tuần
          </Button>
        )}
        {/*  `contents` ở khổ điện thoại: ba phần tử con tham gia thẳng cột dọc bên ngoài để đổi thứ tự bằng `order`. */}
        <div className="flex items-center gap-2 max-md:contents md:ml-auto">
          <p
            id="work-shift-submit-reason"
            aria-live="polite"
            className="text-xs text-muted-foreground empty:hidden max-md:order-1 max-md:text-center"
          >
            {submit.reason}
          </p>
          <Button type="button" variant="outline" className="max-md:order-3 max-md:w-full" onClick={onClose}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={!submit.enabled}
            aria-describedby={submit.reason ? 'work-shift-submit-reason' : undefined}
            onClick={onSubmit}
            className="max-md:order-2 max-md:w-full disabled:bg-muted disabled:text-muted-foreground disabled:opacity-100"
          >
            {submit.label}
          </Button>
        </div>
      </div>
    </div>
  )
}

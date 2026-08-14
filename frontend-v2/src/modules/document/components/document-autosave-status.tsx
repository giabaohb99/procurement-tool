import { Check, Loader2, PencilLine } from 'lucide-react'

import { formatDateTime } from '@/shared/utils/format-date'

interface DocumentAutosaveStatusProps {
  /** Còn nội dung chưa kịp lưu. */
  dirty: boolean
  /** Đang ghi xuống kho — chỉ đúng lúc này mới được hiện vòng xoay. */
  saving: boolean
  /** ISO string của lần lưu gần nhất; `null` = chưa lưu lần nào trong phiên. */
  savedAt: string | null
}

/**
 * Một dòng chữ nhỏ cho biết nội dung đã lưu tới đâu.
 *
 * Đặt cạnh phụ đề ở đầu trang chứ không nằm trong khung soạn thảo: người dùng
 * ngước lên đầu trang để tìm nút Lưu, thấy luôn ở đó là "đã lưu rồi" thì khỏi
 * phải bấm.
 *
 * ⚠️ Lúc đang gõ KHÔNG dùng biểu tượng xoay: vòng xoay đọc ra là "đang gửi đi",
 * làm người dùng tưởng cứ mỗi phím gõ là một lần lưu. Thực tế lúc này chưa lưu
 * gì cả — chỉ ghi nhận là có thay đổi, việc lưu đợi ngừng gõ 1,5 giây mới chạy
 * (xem `use-document-autosave.ts`). Vòng xoay để dành cho đúng lúc ghi thật,
 * nhờ vậy nó giữ nghĩa "hệ đang làm việc với dữ liệu của bạn".
 */
export function DocumentAutosaveStatus({
  dirty,
  saving,
  savedAt,
}: DocumentAutosaveStatusProps) {
  // "Đang lưu" đè lên "chưa lưu": lượt ghi đã chạy rồi thì báo chưa lưu là sai.
  if (saving) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <Loader2 className="size-3.5 animate-spin" />
        Đang lưu…
      </span>
    )
  }

  if (dirty) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <PencilLine className="size-3.5" />
        Chưa lưu — tự lưu khi bạn ngừng gõ
      </span>
    )
  }

  if (savedAt) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <Check className="size-3.5 text-emerald-600" />
        Đã lưu {formatDateTime(savedAt)}
      </span>
    )
  }

  return <span>Tự lưu trong lúc soạn</span>
}

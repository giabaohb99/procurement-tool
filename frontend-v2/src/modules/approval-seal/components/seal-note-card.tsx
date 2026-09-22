import { NotebookPen } from 'lucide-react'

import { Card } from '@/shared/ui/card'
import type { SealRequest } from '../types/seal-request'
import { SealSectionHeader } from './seal-section-header'

/**
 * Thẻ **GHI CHÚ NGƯỜI GỬI** của phiếu đóng dấu — đứng ở CỘT PHẢI (đổi 22/09/2026,
 * trước đó khép lại thân phiếu ở cột chính).
 *
 * Ghi chú là lời người gửi dặn thêm, và người đọc nó là người sắp quyết định
 * (TBP duyệt · văn thư đóng dấu) — tức thuộc cột trả lời *phiếu đang ở đâu, ai
 * dặn gì*, cạnh Luồng duyệt và Trao đổi, chứ không nằm cuối mạch *văn bản này
 * là gì* (văn bản → pháp nhân → người yêu cầu).
 *
 * Tách khỏi `SealDetailBody` chứ không truyền cờ ẩn/hiện: thân phiếu và cột phải
 * là hai chỗ gọi khác nhau, mà một thẻ thì chỉ nên có một chủ.
 */
export function SealNoteCard({ request }: { request: SealRequest }) {
  //  Chỉ hiện khi ghi chú CÓ NỘI DUNG THẬT — `.trim()` để ô toàn khoảng trắng /
  //  xuống dòng cũng coi như rỗng, không dựng khung trống.
  if (!request.note?.trim()) return null

  return (
    <Card className="flex flex-col gap-4 p-5">
      <SealSectionHeader
        icon={NotebookPen}
        title="Ghi chú người gửi"
        iconColor="text-amber-600 dark:text-amber-400"
      />
      {/*  `whitespace-pre-wrap` giữ nguyên xuống dòng người ta gõ; ở cột hẹp
          380px thì `break-words` lo phần đường dẫn tệp / số dài không có khoảng
          trắng — không có nó thì một chuỗi dài đẩy cả thẻ tràn ra ngoài. */}
      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground">
        {request.note}
      </p>
    </Card>
  )
}

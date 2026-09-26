import { cn } from '@/shared/utils/cn'

interface TreeIndentGuidesProps {
  /** Số cấp thụt lề — 0 (gốc) không vẽ gì. */
  depth: number
  /**
   * Đậm hơn — dòng ĐANG CHỌN kẻ đường gióng đậm để mắt bám theo nhánh dễ hơn.
   * Đơn giản hoá có chủ đích: chỉ đậm đường gióng của CHÍNH dòng đang chọn,
   * không kẻ liền một mạch xuống hết các dòng con cháu cùng nhánh (kiểu VS Code
   * đầy đủ cần biết cả chuỗi tổ tiên của MỌI dòng khác, không đáng công cho một
   * cây thư mục văn bản — xem `MAX_FOLDER_DEPTH`).
   */
  bold: boolean
}

/**
 * Đường gióng thụt lề dọc — mỗi cấp một vạch 16px, kẻ tại tâm ô để thẳng hàng
 * với chevron mở/đóng của dòng tổ tiên ở cấp đó. Tách khỏi `tree-row.tsx` để
 * giữ tệp đó dưới 200 dòng (luật modularization).
 */
export function TreeIndentGuides({ depth, bold }: TreeIndentGuidesProps) {
  if (depth <= 0) return null
  return (
    <>
      {Array.from({ length: depth }, (_, i) => (
        <span key={i} data-tree-indent-guide aria-hidden className="relative h-6 w-4 shrink-0">
          <span
            className={cn(
              'absolute inset-y-0 left-1/2 w-px -translate-x-1/2',
              bold ? 'bg-muted-foreground/50' : 'bg-border',
            )}
          />
        </span>
      ))}
    </>
  )
}

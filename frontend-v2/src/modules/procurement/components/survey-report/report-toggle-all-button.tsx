import { ChevronsDownUp, ChevronsUpDown } from 'lucide-react'

import { Button } from '@/shared/ui/button'

interface ReportToggleAllButtonProps {
  /** Mọi nhóm đang mở — bấm sẽ thu gọn; ngược lại bấm sẽ mở hết. */
  allOpen: boolean
  onClick: () => void
}

/**
 * Nút "Thu gọn / Mở tất cả" trên thanh công cụ của khối Báo cáo thực hiện và Hồ sơ cần hoàn
 * thành (duoc-CR-737). Khổ rộng vẫn là nút chữ như cũ; điện thoại chỉ còn biểu tượng để cả
 * hàng nút vừa 358px, `aria-label` giữ đúng tên chữ cho trình đọc màn hình và bài kiểm.
 *
 * ⚠️ Biểu tượng bọc trong `<span>` chứ không đặt thẳng `<svg>` làm con của nút: `Button` có
 * luật `has-[>svg]:px-2.5`, đặt thẳng thì khổ rộng bị đổi lề dù biểu tượng đang ẩn.
 */
export function ReportToggleAllButton({ allOpen, onClick }: ReportToggleAllButtonProps) {
  const label = allOpen ? 'Thu gọn' : 'Mở tất cả'
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      aria-label={label}
      className="max-md:px-2.5"
      onClick={onClick}
    >
      <span className="md:hidden" aria-hidden="true">
        {allOpen ? <ChevronsDownUp /> : <ChevronsUpDown />}
      </span>
      <span className="max-md:hidden">{label}</span>
    </Button>
  )
}

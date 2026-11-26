/**
 * duoc-CR-784 — hai nút đầu màn dùng chung của cụm Giá bao bì: "In" (mở trang in ở tab mới) và "Xuất Excel".
 *
 * Khổ điện thoại (< 768px) cả hai chỉ còn BIỂU TƯỢNG (chữ giữ cho trình đọc màn hình): hàng nút đầu màn phải vừa một hàng
 * với ô "Khoảng ngày tính min – max" thay vì rơi ba hàng lổn nhổn (người chủ chê 26/11/2026). Màn rộng giữ nguyên chữ.
 */
import { FileDown, Loader2, Printer } from 'lucide-react'
import { Link } from 'react-router-dom'

import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
import { Button } from '@/shared/ui/button'

/** Nút vuông 36px ở khổ điện thoại. */
const MOBILE_ICON_ONLY = 'max-md:size-9 max-md:px-0'

/** In = xem (quyền đọc). `href` rỗng = chưa in được (vd chưa chọn mã) → nút mờ kèm lời giải thích `disabledTitle`. */
export function PackagingPrintButton({ href, disabledTitle }: { href?: string; disabledTitle?: string }) {
  if (!href) {
    return (
      <Button type="button" variant="outline" className={MOBILE_ICON_ONLY} disabled title={disabledTitle}>
        <Printer />
        <span className="max-md:sr-only">In</span>
      </Button>
    )
  }
  return (
    <Button asChild variant="outline" className={MOBILE_ICON_ONLY} title="In">
      <Link to={href} target="_blank" rel="noreferrer" onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)}>
        <Printer />
        <span className="max-md:sr-only">In</span>
      </Link>
    </Button>
  )
}

export function PackagingExportExcelButton({
  exporting,
  disabled = false,
  onClick,
}: {
  exporting: boolean
  disabled?: boolean
  onClick: () => void
}) {
  return (
    <Button
      type="button"
      variant="outline"
      className={MOBILE_ICON_ONLY}
      title="Xuất Excel"
      disabled={disabled || exporting}
      onClick={onClick}
    >
      {exporting ? <Loader2 className="animate-spin" /> : <FileDown />}
      <span className="max-md:sr-only">Xuất Excel</span>
    </Button>
  )
}

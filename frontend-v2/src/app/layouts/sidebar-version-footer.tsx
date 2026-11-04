import { ReleaseVersionLink } from '@/shared/release/release-version-link'
import { useReleaseUnseen } from '@/shared/release/use-release-info'
import { SidebarFooter } from '@/shared/ui/sidebar'

/**
 * Chân menu trái: "Phiên bản 2.12.0" (bao-CR-722, đại ca chốt số 2.X.Y), bấm mở trang Có gì mới; mã commit + giờ
 * build chỉ hiện khi rê chuột (title) và trong trang. Có đợt mới chưa xem thì một chấm đỏ nhỏ trước chữ.
 * Menu thu gọn thì ẩn (rail 48px không đủ chỗ). Máy chủ chưa trả phiên bản thì không vẽ gì.
 */
export function SidebarVersionFooter() {
  const { version } = useReleaseUnseen()
  if (!version) return null
  return (
    <SidebarFooter className="border-t border-border px-3 py-2 group-data-[collapsible=icon]:hidden">
      <ReleaseVersionLink className="truncate text-[11px] text-muted-foreground" />
    </SidebarFooter>
  )
}

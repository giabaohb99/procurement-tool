import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { runningVersionText } from '@/shared/release/release-format'
import { useReleaseUnseen } from '@/shared/release/use-release-info'
import { SidebarFooter } from '@/shared/ui/sidebar'

/**
 * Chân menu trái: "Phiên bản 2.12.0" (bao-CR-722, đại ca chốt số 2.X.Y), bấm mở trang Có gì mới; mã commit + giờ
 * build chỉ hiện khi rê chuột (title) và trong trang.
 * Có đợt mới chưa xem thì một chấm đỏ nhỏ trước chữ. Menu thu gọn thì ẩn (rail 48px không đủ chỗ).
 * Máy chủ chưa trả phiên bản (đang tải / lỗi) thì không vẽ gì — không chiếm chỗ bằng chữ "đang tải".
 */
export function SidebarVersionFooter() {
  const { unseen, version } = useReleaseUnseen()
  if (!version) return null
  return (
    <SidebarFooter className="border-t border-border px-3 py-2 group-data-[collapsible=icon]:hidden">
      <Link
        to={appRoutes.whatsNew}
        className="flex items-center gap-1.5 truncate text-[11px] text-muted-foreground hover:text-foreground"
        title={runningVersionText(version, '')}
      >
        {unseen && (
          <span className="size-1.5 shrink-0 rounded-full bg-destructive" role="status" aria-label="Có đợt cập nhật chưa xem" />
        )}
        <span className="truncate">Phiên bản {version.version}</span>
      </Link>
    </SidebarFooter>
  )
}

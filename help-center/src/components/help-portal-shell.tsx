import { useEffect, type ReactNode } from 'react'
import { useOutletContext } from 'react-router-dom'
import { X } from 'lucide-react'

import HelpSectionNav from '@/components/help-section-nav'
import { Button } from '@/components/ui/button'
import { useMediaQuery, WIDE_QUERY } from '@/hooks/use-media-query'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import type { HelpNode } from '@/lib/help-tree'

// Khung 3 cột của khu người dùng — dùng chung cho trang danh mục và trang bài viết:
//   trái  : cây tài liệu (danh mục)
//   giữa  : nội dung, CANH GIỮA khoảng trống còn lại giữa hai cột bên
//   phải  : mục lục bài viết (trang danh mục không có)
//
// Ba mức bề ngang:
//
// | Bề ngang        | Danh mục                      | Mục lục                      |
// |-----------------|-------------------------------|------------------------------|
// | ≥ 1280 (xl)     | cột, bật/tắt được             | luôn hiện                    |
// | 1024–1279 (lg)  | cột, bật/tắt được             | chỉ hiện KHI tắt danh mục    |
// | < 1024          | ngăn kéo phủ lên (nút ☰ header)| ẩn hẳn                       |
//
// Ở mức lg không thể để cả hai: 1024 - 256×2 - lề - khoảng cách còn chưa tới 400px cho nội dung,
// đọc không nổi. Nên mục lục "nhường chỗ" cho danh mục và chỉ hiện khi người đọc tự tắt danh mục.

/** Chiều cao header — cột hai bên bám ngay dưới nó. */
const HEADER_OFFSET = 'top-[4.25rem]'
const SIDE_HEIGHT = 'h-[calc(100vh-4.25rem)]'

export default function HelpPortalShell({
  tree, activeId, toc, children,
}: {
  tree: HelpNode[]
  activeId: number | null
  /** Cột mục lục bên phải. Bỏ trống = trang này không có mục lục (vd trang danh mục). */
  toc?: ReactNode
  children: ReactNode
}) {
  const { sidebar } = useOutletContext<PortalOutletContext>()
  const isWide = useMediaQuery(WIDE_QUERY)

  // Báo cho header biết trang này có danh mục -> hiện nút bật/tắt
  const { setAvailable } = sidebar
  useEffect(() => {
    setAvailable(true)
    return () => setAvailable(false)
  }, [setAvailable])

  const { open, isDesktop, close } = sidebar
  const showColumn = isDesktop && open
  const showDrawer = !isDesktop && open
  const showToc = !!toc && isDesktop && (isWide || !open)

  const nav = <HelpSectionNav tree={tree} activeId={activeId} />

  return (
    // px-6/md:px-8 = ĐÚNG lề của header, để danh mục thẳng hàng với logo và mục lục thẳng hàng
    // với cụm tài khoản. KHÔNG bọc thêm div border-t: header đã có border-b, thêm nữa là 2 vạch.
    <div className="flex w-full items-start gap-8 px-6 md:px-8">
      {/* Cột danh mục. <aside> chỉ giữ chỗ rộng 16rem; khung bên trong để "fixed" nên đứng yên khi
          cuộn kể cả lúc bài ngắn hơn danh mục (sticky sẽ tuột theo trang vì thẻ cha không đủ cao).
          Không đặt "left" -> trình duyệt giữ nguyên vị trí ngang vốn có, vẫn thẳng lề với header. */}
      {showColumn && (
        <aside className="w-64 shrink-0">
          <div className={`fixed ${HEADER_OFFSET} ${SIDE_HEIGHT} w-64 overflow-y-auto border-r py-8 pr-4`}>
            {nav}
          </div>
        </aside>
      )}

      {/* Ngăn kéo ở màn hẹp — phủ lên nội dung thay vì đẩy, vì đẩy thì nội dung chỉ còn vài trăm px */}
      {showDrawer && (
        <>
          <div
            aria-hidden
            onClick={close}
            className={`fixed inset-x-0 bottom-0 ${HEADER_OFFSET} z-40 bg-black/40 animate-in fade-in`}
          />
          <aside
            className={`fixed left-0 ${HEADER_OFFSET} ${SIDE_HEIGHT} z-50 w-72 max-w-[85vw] overflow-y-auto border-r bg-background py-6 pl-4 pr-2 shadow-xl animate-in slide-in-from-left duration-200`}
          >
            <div className="mb-2 flex justify-end pr-2">
              <Button variant="ghost" size="icon" className="size-8" title="Đóng danh mục" onClick={close}>
                <X className="size-4" />
              </Button>
            </div>
            {nav}
          </aside>
        </>
      )}

      {/* mx-auto: nội dung canh giữa chỗ trống còn lại thay vì dính sát danh mục — nếu không, màn
          rộng mà bài không có mục lục sẽ chừa một dải trắng rất lớn bên phải. */}
      <main className="mx-auto w-full min-w-0 max-w-3xl flex-1 pb-16 pt-8">
        {children}
      </main>

      {showToc && (
        <aside className={`sticky ${HEADER_OFFSET} hidden max-h-[calc(100vh-4.25rem)] w-64 shrink-0 overflow-y-auto py-8 lg:block`}>
          {toc}
        </aside>
      )}
    </div>
  )
}

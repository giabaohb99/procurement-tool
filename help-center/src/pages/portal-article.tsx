import { useEffect, useRef, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { FileX2 } from 'lucide-react'

import { api } from '@/api/client'
import HelpArticleNav from '@/components/help-article-nav'
import HelpArticleToc from '@/components/help-article-toc'
import { HelpSlideGallery, type HelpSlide } from '@/components/help-article-slides'
import HelpBreadcrumb from '@/components/help-breadcrumb'
import HelpSectionNav from '@/components/help-section-nav'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useHeadingToc } from '@/hooks/use-heading-toc'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import { findPath, findReadingNeighbors } from '@/lib/help-tree'

// Trang CHI TIẾT bài viết — bố cục 3 cột như khu quản trị:
// sidebar cây tài liệu (trái) · nội dung (giữa) · mục lục bài viết (phải).
// Cả hai cột hai bên đều sticky và tự cuộn riêng; ẩn dần ở màn hẹp (trái < lg, phải < xl).

interface PortalArticleData {
  id: number
  title: string
  content: string
  parent_id: number | null
  slides: HelpSlide[]
}

export default function PortalArticle({ nodeId }: { nodeId: number | null }) {
  const { tree } = useOutletContext<PortalOutletContext>()

  const [article, setArticle] = useState<PortalArticleData | null>(null)
  const [notFound, setNotFound] = useState(false)

  const contentRef = useRef<HTMLDivElement>(null)
  const { items: toc, activeId } = useHeadingToc(contentRef, [article], !!article)

  const crumbs = nodeId ? findPath(tree, nodeId) : null
  const { prev, next } = nodeId
    ? findReadingNeighbors(tree, nodeId)
    : { prev: null, next: null }

  useEffect(() => {
    let cancelled = false
    setArticle(null)
    setNotFound(false)
    // Slug không tra ra bài nào -> báo không tìm thấy luôn, khỏi gọi API
    if (!nodeId) { setNotFound(true); return }
    api.get(`/api/v1/help-center/${nodeId}`)
      .then((res) => { if (!cancelled) setArticle(res.data.data) })
      .catch(() => { if (!cancelled) setNotFound(true) })
    window.scrollTo({ top: 0 })
    return () => { cancelled = true }
  }, [nodeId])

  // px-6/md:px-8 = ĐÚNG lề của header, để sidebar thẳng hàng với logo và mục lục thẳng hàng với
  // cụm tài khoản. Chiều rộng dễ đọc do cột giữa tự giới hạn.
  // KHÔNG bọc thêm div border-t: header đã có border-b, thêm nữa là 2 vạch chồng nhau.
  return (
    <div className="flex w-full items-start gap-8 px-6 md:px-8">
      {/* Cột trái: cây tài liệu của mục đang đọc.
          <aside> chỉ giữ chỗ rộng 16rem; khung bên trong để "fixed" nên đứng yên khi cuộn kể cả khi
          bài viết ngắn hơn sidebar (sticky sẽ tuột theo trang vì thẻ cha không đủ cao). Không đặt
          "left" -> trình duyệt giữ nguyên vị trí ngang vốn có, vẫn thẳng lề với header. */}
      <aside className="hidden w-64 shrink-0 lg:block">
        <div className="fixed top-[4.25rem] h-[calc(100vh-4.25rem)] w-64 overflow-y-auto border-r py-8 pr-4">
          <HelpSectionNav tree={tree} activeId={nodeId} />
        </div>
      </aside>

      <main className="min-w-0 max-w-3xl flex-1 pb-16 pt-8">
        <div className="mb-5">
          <HelpBreadcrumb crumbs={crumbs} />
        </div>

        {notFound ? (
          <Card className="items-center gap-1.5 border-dashed py-12 text-center">
            <FileX2 className="mb-1.5 size-9 text-muted-foreground" />
            <strong className="text-navy">Không tìm thấy bài viết</strong>
            <span className="text-sm text-muted-foreground">
              Bài viết này không tồn tại hoặc đã bị xóa.
            </span>
          </Card>
        ) : !article ? (
          <div className="space-y-4">
            <Skeleton className="h-9 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-11/12" />
            <Skeleton className="h-4 w-4/6" />
          </div>
        ) : (
          <>
            <h1 className="mb-2.5 border-b pb-4 text-[1.8rem] font-bold leading-tight text-navy">
              {article.title}
            </h1>

            <div ref={contentRef} className="hc-content"
                 dangerouslySetInnerHTML={{ __html: article.content || '' }} />

            {!article.content && (
              <p className="text-muted-foreground">Bài viết chưa có nội dung.</p>
            )}

            <HelpSlideGallery slides={article.slides} />

            <HelpArticleNav prev={prev} next={next} />
          </>
        )}
      </main>

      {/* Cột phải: mục lục bài viết. Danh sách bài cùng nhóm đã có ở sidebar trái nên
          không lặp lại box "Bài viết liên quan" nữa. */}
      <aside className="sticky top-[4.25rem] ml-auto hidden max-h-[calc(100vh-4.25rem)] w-64 shrink-0 overflow-y-auto py-8 xl:block">
        <HelpArticleToc items={toc} activeId={activeId} />
      </aside>
    </div>
  )
}

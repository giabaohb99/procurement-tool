import { useEffect, useRef, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { FileX2 } from 'lucide-react'

import { api } from '@/api/client'
import HelpArticleNav from '@/components/help-article-nav'
import HelpArticleToc from '@/components/help-article-toc'
import { HelpSlideGallery, type HelpSlide } from '@/components/help-article-slides'
import HelpBreadcrumb from '@/components/help-breadcrumb'
import HelpPortalShell from '@/components/help-portal-shell'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useHeadingToc } from '@/hooks/use-heading-toc'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import { findPath, findReadingNeighbors } from '@/lib/help-tree'

// Trang CHI TIẾT bài viết. Khung 3 cột (danh mục · nội dung · mục lục) và toàn bộ cách xoay xở
// theo bề ngang màn hình nằm ở components/help-portal-shell.tsx — ở đây chỉ lo phần nội dung.

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

  return (
    <HelpPortalShell
      tree={tree}
      activeId={nodeId}
      // Bài không có heading nào thì không dựng cột mục lục, để nội dung dùng trọn bề ngang
      toc={toc.length > 0 ? <HelpArticleToc items={toc} activeId={activeId} /> : undefined}
    >
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
    </HelpPortalShell>
  )
}

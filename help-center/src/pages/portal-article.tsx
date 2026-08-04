import { useEffect, useRef, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import { ArrowLeft, FileText, FileX2 } from 'lucide-react'

import { api } from '@/api/client'
import HelpArticleToc from '@/components/help-article-toc'
import { HelpSlideGallery, type HelpSlide } from '@/components/help-article-slides'
import HelpTopBar from '@/components/help-topbar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useHeadingToc } from '@/hooks/use-heading-toc'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import { findParent, findPath } from '@/lib/help-tree'

// Trang CHI TIẾT bài viết — nội dung bên trái, cột phải là mục lục (sticky) + bài liên quan.

const MAX_RELATED = 6

interface PortalArticleData {
  id: number
  title: string
  content: string
  parent_id: number | null
  slides: HelpSlide[]
}

export default function PortalArticle() {
  const { id } = useParams()
  const { tree } = useOutletContext<PortalOutletContext>()

  const [article, setArticle] = useState<PortalArticleData | null>(null)
  const [notFound, setNotFound] = useState(false)

  const contentRef = useRef<HTMLDivElement>(null)
  const { items: toc, activeId } = useHeadingToc(contentRef, [article], !!article)

  const nodeId = id ? parseInt(id, 10) : null
  const crumbs = nodeId ? findPath(tree, nodeId) : null
  const parent = nodeId ? findParent(tree, nodeId) : null
  const related = (parent?.children || []).filter((c) => c.id !== nodeId).slice(0, MAX_RELATED)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    setArticle(null)
    setNotFound(false)
    api.get(`/api/v1/help-center/${id}`)
      .then((res) => { if (!cancelled) setArticle(res.data.data) })
      .catch(() => { if (!cancelled) setNotFound(true) })
    window.scrollTo({ top: 0 })
    return () => { cancelled = true }
  }, [id])

  return (
    <>
      <HelpTopBar crumbs={crumbs} />

      <div className="mx-auto flex max-w-7xl flex-col items-start gap-10 px-6 pb-16 pt-8 lg:flex-row">
        <main className="min-w-0 flex-1">
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
            </>
          )}
        </main>

        <aside className="w-full shrink-0 space-y-4 lg:sticky lg:top-24 lg:w-[19rem]">
          <HelpArticleToc items={toc} activeId={activeId} />

          {related.length > 0 && (
            <Card className="gap-3 border bg-muted/50 py-4">
              <CardHeader className="px-5">
                <CardTitle className="text-[15px] font-bold text-navy">Bài viết liên quan</CardTitle>
              </CardHeader>
              <CardContent className="px-5">
                <ul className="space-y-1">
                  {related.map((r) => (
                    <li key={r.id}>
                      <Link to={`/${r.id}`}
                            className="flex items-start gap-2 py-1.5 text-sm leading-snug text-slate-600 transition-colors hover:text-primary">
                        <FileText className="mt-0.5 size-4 shrink-0 text-primary" />
                        {r.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {parent && (
            <Link to={`/${parent.id}`}
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
              <ArrowLeft className="size-4" /> Về "{parent.title}"
            </Link>
          )}
        </aside>
      </div>
    </>
  )
}

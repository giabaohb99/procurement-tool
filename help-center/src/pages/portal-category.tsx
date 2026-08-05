import { useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { ChevronRight, FileText } from 'lucide-react'

import { api } from '@/api/client'
import HelpArticleNav from '@/components/help-article-nav'
import HelpBreadcrumb from '@/components/help-breadcrumb'
import HelpSectionNav from '@/components/help-section-nav'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import { useArticlePath } from '@/lib/help-slug'
import { findPath, findReadingNeighbors, type HelpNode } from '@/lib/help-tree'
import { excerptFromHtml } from '@/lib/utils'

// Trang DANH MỤC — cùng khung với trang bài viết: sidebar cây tài liệu bên trái, nội dung ở giữa.
// Thứ tự đọc trong cột giữa: tiêu đề mục -> mô tả/nội dung mở đầu -> DANH SÁCH bài viết bên trong.
// Danh sách để dạng thẻ bấm được, tách hẳn khỏi phần văn bản mở đầu — trước đây cả hai đều là
// chữ đậm + gạch ngang nên nhìn lẫn lộn, không biết đâu là nội dung đâu là link sang bài khác.

export default function PortalCategory({ node }: { node: HelpNode }) {
  const { tree } = useOutletContext<PortalOutletContext>()
  const pathOf = useArticlePath()
  const [intro, setIntro] = useState('')
  const [excerpts, setExcerpts] = useState<Record<number, string>>({})

  const children = node.children || []
  const crumbs = findPath(tree, node.id)
  const { prev, next } = findReadingNeighbors(tree, node.id)

  // Nội dung mở đầu của chính danh mục + trích đoạn của từng bài con
  useEffect(() => {
    let cancelled = false
    setIntro('')
    setExcerpts({})
    window.scrollTo({ top: 0 })

    api.get(`/api/v1/help-center/${node.id}`)
      .then((res) => { if (!cancelled) setIntro(res.data.data.content || '') })
      .catch(() => {})

    // Chỉ bài nào CHƯA có mô tả ngắn mới cần tải nội dung về để cắt trích đoạn
    Promise.all(
      children.filter((c) => !c.summary).map((c) =>
        api.get(`/api/v1/help-center/${c.id}`)
          .then((res) => [c.id, excerptFromHtml(res.data.data.content)] as const)
          .catch(() => [c.id, ''] as const),
      ),
    ).then((pairs) => { if (!cancelled) setExcerpts(Object.fromEntries(pairs)) })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node.id])

  return (
    <div className="flex w-full items-start gap-8 px-6 md:px-8">
      <aside className="sticky top-[4.25rem] hidden h-[calc(100vh-4.25rem)] w-64 shrink-0 overflow-y-auto border-r py-8 pr-4 lg:block">
        <HelpSectionNav tree={tree} activeId={node.id} />
      </aside>

      <main className="min-w-0 max-w-3xl flex-1 pb-16 pt-8">
        <div className="mb-5">
          <HelpBreadcrumb crumbs={crumbs} />
        </div>

        <h1 className="text-[1.75rem] font-bold leading-tight text-ink">{node.title}</h1>
        {node.summary && (
          <p className="mt-2 text-[15px] leading-relaxed text-ink-muted">{node.summary}</p>
        )}

        {/* hc-content--intro hạ cỡ heading trong nội dung mở đầu để không đấu với tiêu đề mục */}
        {intro && (
          <div className="hc-content hc-content--intro mt-6"
               dangerouslySetInnerHTML={{ __html: intro }} />
        )}

        {children.length > 0 && (
          <section className="mt-10">
            <h2 className="mb-4 border-b pb-2 text-xs font-bold uppercase tracking-wide text-ink-muted">
              Bài viết trong mục ({children.length})
            </h2>

            <div className="grid gap-3">
              {children.map((child) => (
                <Link
                  key={child.id}
                  to={pathOf(child.id)}
                  className="group flex items-start gap-3 rounded-xl border p-4 transition-all hover:border-primary hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)]"
                >
                  <FileText className="mt-0.5 size-5 shrink-0 text-primary" strokeWidth={1.75} />
                  <span className="min-w-0 flex-1">
                    <span className="block font-semibold leading-snug text-ink transition-colors group-hover:text-primary">
                      {child.title}
                    </span>
                    {/* Cắt 2 dòng: trích đoạn cắt từ HTML là văn bản chạy dài, để nguyên sẽ lấn át tiêu đề */}
                    <span className="mt-1 line-clamp-2 block text-sm leading-relaxed text-ink-muted">
                      {child.summary || excerpts[child.id] || 'Xem hướng dẫn chi tiết.'}
                    </span>
                  </span>
                  <ChevronRight className="mt-0.5 size-4 shrink-0 text-ink-muted transition-colors group-hover:text-primary" />
                </Link>
              ))}
            </div>
          </section>
        )}

        <HelpArticleNav prev={prev} next={next} />
      </main>
    </div>
  )
}

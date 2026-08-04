import { useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'

import { api } from '@/api/client'
import HelpTopBar from '@/components/help-topbar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import { findPath, type HelpNode } from '@/lib/help-tree'

// Trang DANH MỤC — danh sách bài viết (tiêu đề + trích đoạn) bên trái, box điều hướng bên phải.

const EXCERPT_LEN = 150

/** Bỏ thẻ HTML, rút gọn nội dung làm trích đoạn 1–2 dòng. */
function excerpt(html: string): string {
  const text = (html || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
  if (!text) return ''
  return text.length > EXCERPT_LEN ? text.slice(0, EXCERPT_LEN) + '…' : text
}

export default function PortalCategory({ node }: { node: HelpNode }) {
  const { tree } = useOutletContext<PortalOutletContext>()
  const [intro, setIntro] = useState('')
  const [excerpts, setExcerpts] = useState<Record<number, string>>({})

  const children = node.children || []
  const crumbs = findPath(tree, node.id)
  const otherRoots = tree.filter((n) => n.id !== crumbs?.[0]?.id)

  // Nội dung mở đầu của chính danh mục + trích đoạn của từng bài con
  useEffect(() => {
    let cancelled = false
    setIntro('')
    setExcerpts({})
    window.scrollTo({ top: 0 })

    api.get(`/api/v1/help-center/${node.id}`)
      .then((res) => { if (!cancelled) setIntro(res.data.data.content || '') })
      .catch(() => {})

    Promise.all(
      children.map((c) =>
        api.get(`/api/v1/help-center/${c.id}`)
          .then((res) => [c.id, excerpt(res.data.data.content)] as const)
          .catch(() => [c.id, ''] as const),
      ),
    ).then((pairs) => { if (!cancelled) setExcerpts(Object.fromEntries(pairs)) })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node.id])

  return (
    <>
      <HelpTopBar crumbs={crumbs} />

      <div className="mx-auto flex max-w-7xl flex-col items-start gap-10 px-6 pb-16 pt-8 lg:flex-row">
        <main className="min-w-0 flex-1">
          <h1 className="mb-2.5 border-b pb-4 text-[1.8rem] font-bold leading-tight text-navy">
            {node.title}
          </h1>

          {intro && (
            <div className="hc-content mb-2" dangerouslySetInnerHTML={{ __html: intro }} />
          )}

          <div className="divide-y">
            {children.map((child) => (
              <article key={child.id} className="py-5">
                <h2 className="mb-2 text-lg font-bold leading-snug">
                  <Link to={`/${child.id}`} className="text-navy transition-colors hover:text-primary">
                    {child.title}
                  </Link>
                </h2>
                <p className="text-[15px] leading-relaxed text-muted-foreground">
                  {child.children?.length
                    ? `${child.children.length} bài viết bên trong danh mục này.`
                    : excerpts[child.id] || 'Xem hướng dẫn chi tiết.'}
                </p>
              </article>
            ))}
          </div>
        </main>

        <aside className="w-full shrink-0 space-y-4 lg:sticky lg:top-24 lg:w-[19rem]">
          <SideBox title="Bài viết trong mục" items={children} />
          {otherRoots.length > 0 && <SideBox title="Nhóm nghiệp vụ khác" items={otherRoots} />}
        </aside>
      </div>
    </>
  )
}

function SideBox({ title, items }: { title: string; items: HelpNode[] }) {
  return (
    <Card className="gap-3 border bg-muted/50 py-4">
      <CardHeader className="px-5">
        <CardTitle className="text-[15px] font-bold text-navy">{title}</CardTitle>
      </CardHeader>
      <CardContent className="px-5">
        <ul className="space-y-1">
          {items.map((item) => (
            <li key={item.id}>
              <Link to={`/${item.id}`}
                    className="block py-1.5 text-sm leading-snug text-slate-600 transition-colors hover:text-primary">
                {item.title}
              </Link>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

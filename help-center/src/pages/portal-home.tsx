import { useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { BookOpen, ChevronRight, Images, MessageCircleQuestion, Search } from 'lucide-react'

import { api } from '@/api/client'
import HelpCategoryTiles from '@/components/help-category-tiles'
import HelpSearchBox from '@/components/help-search-box'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import type { HelpNode } from '@/lib/help-tree'
import { excerptFromHtml } from '@/lib/utils'

// Trang chủ khu người dùng — đồng bộ tông với Trung tâm trợ giúp của hệ Văn thư:
// nền gradient sáng, tiêu đề lớn canh giữa, tile "bắt đầu ngay" gradient có ảnh minh họa,
// lưới thẻ phân hệ nền trắng không viền (đổ bóng mảnh).

const QUICK_COUNT = 3

/** Nền + ảnh minh họa cho 3 tile "Bắt đầu ngay", xoay vòng theo vị trí. */
const QUICK_SKINS = [
  { gradient: 'linear-gradient(135deg, #e4f7ff 0%, #bde1ff 100%)', image: '/hc_overview.png' },
  { gradient: 'linear-gradient(135deg, #e6e6ff 0%, #cccdff 100%)', image: '/hc_new_user.png' },
  { gradient: 'linear-gradient(135deg, #fae6ff 0%, #efc2ff 100%)', image: '/hc_admin.png' },
]

/** Duyệt cây theo chiều sâu, lấy các bài viết lá đầu tiên làm lối tắt "bắt đầu ngay". */
function firstLeaves(nodes: HelpNode[], limit: number, acc: HelpNode[] = []): HelpNode[] {
  for (const node of nodes) {
    if (acc.length >= limit) break
    if (node.children?.length) firstLeaves(node.children, limit, acc)
    else acc.push(node)
  }
  return acc
}

const TIPS = [
  { Icon: Search, title: 'Tìm kiếm nhanh', desc: 'Gõ từ khóa để tra theo tiêu đề hoặc nội dung bài viết.' },
  { Icon: BookOpen, title: 'Duyệt theo danh mục', desc: 'Mở một nhóm nghiệp vụ để xem toàn bộ bài viết bên trong.' },
  { Icon: Images, title: 'Xem theo từng bước', desc: 'Nhiều bài có ảnh minh họa từng bước ở cuối trang.' },
]

export default function PortalHome() {
  const { tree } = useOutletContext<PortalOutletContext>()
  const quick = firstLeaves(tree, QUICK_COUNT)

  // Bài nào chưa có mô tả ngắn thì lấy tạm trích đoạn đầu nội dung để tile không trống.
  const needExcerpt = quick.filter((n) => !n.summary).map((n) => n.id)
  const excerptKey = needExcerpt.join(',')

  const [excerpts, setExcerpts] = useState<Record<number, string>>({})
  useEffect(() => {
    if (!excerptKey) return
    let cancelled = false
    Promise.all(
      excerptKey.split(',').map((raw) => {
        const id = Number(raw)
        return api.get(`/api/v1/help-center/${id}`)
          .then((res) => [id, excerptFromHtml(res.data.data.content, 90)] as const)
          .catch(() => [id, ''] as const)
      }),
    ).then((pairs) => { if (!cancelled) setExcerpts(Object.fromEntries(pairs)) })
    return () => { cancelled = true }
  }, [excerptKey])

  return (
    <div className="bg-[linear-gradient(#f0f4ff_0%,#ffffff_500px,#ffffff_100%)]">
      {/* Hero nền sáng — tiêu đề lớn + ô tìm kiếm canh giữa */}
      <section className="px-6 pb-20 pt-16">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="mb-10 text-[2rem] font-bold leading-tight tracking-[-0.02em] text-ink md:text-[3rem]">
            Chúng tôi có thể giúp gì cho bạn?
          </h1>
          <HelpSearchBox
            size="lg"
            className="mx-auto max-w-[41.25rem]"
            placeholder="Tìm kiếm tài liệu, hướng dẫn..."
          />
        </div>
      </section>

      <div className="mx-auto max-w-[71.25rem] px-6">
        {/* Bắt đầu ngay — tile gradient có ảnh minh họa */}
        {quick.length > 0 && (
          <Section title="Bắt đầu ngay">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {quick.map((node, i) => {
                const skin = QUICK_SKINS[i % QUICK_SKINS.length]
                return (
                  <Link
                    key={node.id}
                    to={`/${node.id}`}
                    style={{ background: skin.gradient }}
                    className="relative block h-60 overflow-hidden rounded-2xl transition-all hover:-translate-y-0.5 hover:shadow-lg"
                  >
                    <div className="relative z-[2] p-7">
                      <h3 className="mb-2 flex items-center gap-1 text-xl font-semibold text-ink">
                        {node.title} <ChevronRight className="size-4" />
                      </h3>
                      <p className="line-clamp-3 max-w-[65%] text-sm leading-relaxed text-ink-muted">
                        {node.summary || excerpts[node.id] || 'Mở hướng dẫn chi tiết cho nghiệp vụ này.'}
                      </p>
                    </div>
                    <img
                      src={skin.image}
                      alt=""
                      aria-hidden
                      className="pointer-events-none absolute -bottom-5 -right-2.5 z-[1] size-[11.25rem] object-contain"
                    />
                  </Link>
                )
              })}
            </div>
          </Section>
        )}

        {/* Các phân hệ */}
        <Section title="Các Phân hệ">
          {tree.length > 0 ? (
            <HelpCategoryTiles nodes={tree} />
          ) : (
            <div className="rounded-xl border border-dashed border-hairline px-6 py-12 text-center">
              <BookOpen className="mx-auto mb-2 size-8 text-ink-muted" strokeWidth={1.5} />
              <strong className="block text-ink">Chưa có tài liệu nào</strong>
              <span className="text-sm text-ink-muted">
                Quản trị viên chưa đăng tài liệu hướng dẫn. Vui lòng quay lại sau.
              </span>
            </div>
          )}
        </Section>

        {/* Câu hỏi thường gặp */}
        <Section title="Không tìm thấy điều bạn cần?">
          <Link
            to="/cau-hoi-thuong-gap"
            className="mx-auto flex max-w-2xl items-center gap-4 rounded-xl bg-card p-6 shadow-[0_4px_12px_rgba(0,0,0,0.03)] transition-all hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(0,0,0,0.07)]"
          >
            <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-primary/8 text-primary">
              <MessageCircleQuestion className="size-6" strokeWidth={1.75} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-base font-semibold text-ink">Câu hỏi thường gặp</span>
              <span className="mt-1 block text-sm leading-relaxed text-ink-muted">
                Giải đáp nhanh những thắc mắc hay gặp nhất khi dùng hệ thống.
              </span>
            </span>
            <ChevronRight className="size-5 shrink-0 text-ink-muted" />
          </Link>
        </Section>

        {/* Mẹo tra cứu */}
        <Section title="Mẹo tra cứu" className="pb-20">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
            {TIPS.map(({ Icon, title, desc }) => (
              <div
                key={title}
                className="rounded-xl bg-card p-6 shadow-[0_4px_12px_rgba(0,0,0,0.03)]"
              >
                <span className="mb-3 grid size-12 place-items-center rounded-xl bg-primary/8 text-primary">
                  <Icon className="size-6" strokeWidth={1.75} />
                </span>
                <strong className="block text-base font-semibold text-ink">{title}</strong>
                <span className="mt-1 block text-sm leading-relaxed text-ink-muted">{desc}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </div>
  )
}

/** Khối nội dung: tiêu đề lớn canh giữa, cách nhau 80px như bản tham chiếu. */
function Section({
  title, className = '', children,
}: {
  title: string
  className?: string
  children: React.ReactNode
}) {
  return (
    <section className={`mb-20 ${className}`}>
      <h2 className="mb-8 text-center text-[1.75rem] font-bold text-ink">{title}</h2>
      {children}
    </section>
  )
}

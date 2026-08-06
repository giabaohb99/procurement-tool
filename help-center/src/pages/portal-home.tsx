import { useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import {
  BookOpen, ChevronRight, Images, MessageCircleQuestion, Search, type LucideIcon,
} from 'lucide-react'

import { api } from '@/api/client'
import HelpCategoryTiles from '@/components/help-category-tiles'
import HelpSearchBox from '@/components/help-search-box'
import { HERO_SEARCH_ID, type PortalOutletContext } from '@/layouts/portal-layout'
import {
  fetchHomeSections, HOME_SECTION, type HelpHomeSection,
} from '@/lib/help-home-api'
import { gradientCss, illustrationUrl } from '@/lib/help-home-skins'
import { resolveHelpIcon } from '@/lib/help-icons'
import { useArticlePath } from '@/lib/help-slug'
import { findNode, firstLeaves, type HelpNode } from '@/lib/help-tree'
import { excerptFromHtml } from '@/lib/utils'

// Trang chủ khu người dùng — đồng bộ tông với Trung tâm trợ giúp của hệ Văn thư:
// nền gradient sáng, tiêu đề lớn canh giữa, tile "bắt đầu ngay" gradient có ảnh minh họa,
// lưới thẻ phân hệ nền xám nhạt không viền (đổ bóng mảnh).
//
// THỨ TỰ, TIÊU ĐỀ, ẨN/HIỆN của 4 khối lấy từ cấu hình ở /admin/trang-chu. Gọi API lỗi hoặc
// backend chưa seed thì rơi về bố cục mặc định bên dưới — trang chủ không bao giờ trắng.

const QUICK_COUNT = 3

const TIPS = [
  { Icon: Search, title: 'Tìm kiếm nhanh', desc: 'Gõ từ khóa để tra theo tiêu đề hoặc nội dung bài viết.' },
  { Icon: BookOpen, title: 'Duyệt theo danh mục', desc: 'Mở một nhóm nghiệp vụ để xem toàn bộ bài viết bên trong.' },
  { Icon: Images, title: 'Xem theo từng bước', desc: 'Nhiều bài có ảnh minh họa từng bước ở cuối trang.' },
]

/** Bố cục mặc định khi chưa có cấu hình — đúng thứ tự/tiêu đề vốn có của trang chủ. */
const DEFAULT_SECTIONS: Pick<HelpHomeSection, 'key' | 'title'>[] = [
  { key: HOME_SECTION.QUICK, title: 'Bắt đầu ngay' },
  { key: HOME_SECTION.CATEGORIES, title: 'Các Phân hệ' },
  { key: HOME_SECTION.FAQ, title: 'Không tìm thấy điều bạn cần?' },
  { key: HOME_SECTION.TIPS, title: 'Mẹo tra cứu' },
]

export default function PortalHome() {
  const { tree } = useOutletContext<PortalOutletContext>()
  const pathOf = useArticlePath()

  const [sections, setSections] = useState<HelpHomeSection[] | null>(null)
  useEffect(() => {
    let cancelled = false
    fetchHomeSections()
      .then((data) => { if (!cancelled) setSections(data) })
      .catch(() => { if (!cancelled) setSections([]) })
    return () => { cancelled = true }
  }, [])

  // Khung chưa chọn bài nào -> tự lấy như cũ, để trang chủ có nội dung ngay từ lúc mới cài
  const layout = sections?.length ? sections.filter((s) => s.is_visible) : DEFAULT_SECTIONS
  const configured = (key: string) => sections?.find((s) => s.key === key)?.items ?? []

  const quickPicked = configured(HOME_SECTION.QUICK)
    .map((item) => findNode(tree, item.article_id))
    .filter((n): n is HelpNode => !!n)
  const quick = quickPicked.length > 0 ? quickPicked : firstLeaves(tree, QUICK_COUNT)
  const quickSkins = quickPicked.length > 0 ? configured(HOME_SECTION.QUICK) : []

  const categoryPicked = configured(HOME_SECTION.CATEGORIES)
    .map((item) => findNode(tree, item.article_id))
    .filter((n): n is HelpNode => !!n)
  const categories = categoryPicked.length > 0 ? categoryPicked : tree

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
          {/* id để header biết ô này đã cuộn khuất chưa mà tự hiện ô tìm kiếm nhỏ */}
          <div id={HERO_SEARCH_ID}>
            <HelpSearchBox
              size="lg"
              className="mx-auto max-w-[41.25rem]"
              placeholder="Tìm kiếm tài liệu, hướng dẫn..."
            />
          </div>
        </div>
      </section>

      {/* Thứ tự khối chạy theo cấu hình ở /admin/trang-chu; khối cuối chừa thêm lề dưới */}
      <div className="mx-auto max-w-[71.25rem] px-6">
        {layout.map((section, index) => {
          const last = index === layout.length - 1 ? 'pb-20' : ''

          if (section.key === HOME_SECTION.QUICK) {
            if (quick.length === 0) return null
            return (
              <Section key={section.key} title={section.title} className={last}>
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {quick.map((node, i) => (
                    <Link
                      key={node.id}
                      to={pathOf(node.id)}
                      style={{ background: gradientCss(quickSkins[i]?.gradient, i) }}
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
                        src={illustrationUrl(quickSkins[i]?.background_image, i)}
                        alt=""
                        aria-hidden
                        className="pointer-events-none absolute -bottom-5 -right-2.5 z-[1] size-[11.25rem] object-contain"
                      />
                    </Link>
                  ))}
                </div>
              </Section>
            )
          }

          if (section.key === HOME_SECTION.CATEGORIES) {
            return (
              <Section key={section.key} title={section.title} className={last}>
                {categories.length > 0 ? (
                  <HelpCategoryTiles nodes={categories} />
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
            )
          }

          if (section.key === HOME_SECTION.FAQ) {
            const questions = configured(HOME_SECTION.FAQ)
            return (
              <Section key={section.key} title={section.title} className={last}>
                {/* Chưa chọn câu hỏi nào -> chỉ một thẻ dẫn sang trang Câu hỏi thường gặp */}
                <div className="mx-auto grid max-w-2xl gap-3">
                  {questions.length === 0 ? (
                    <FaqCard
                      title="Câu hỏi thường gặp"
                      desc="Giải đáp nhanh những thắc mắc hay gặp nhất khi dùng hệ thống."
                    />
                  ) : (
                    questions.map((item) => (
                      <FaqCard key={item.id} title={item.faq_question || 'Câu hỏi'} />
                    ))
                  )}
                </div>
              </Section>
            )
          }

          const tips = configured(HOME_SECTION.TIPS)
          return (
            <Section key={section.key} title={section.title} className={last}>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                {tips.length === 0
                  ? TIPS.map(({ Icon, title, desc }) => (
                      <TipCard key={title} Icon={Icon} title={title} desc={desc} />
                    ))
                  : tips.map((item, i) => (
                      <TipCard
                        key={item.id}
                        Icon={resolveHelpIcon(item.icon, i)}
                        title={item.title || ''}
                        desc={item.description || ''}
                      />
                    ))}
              </div>
            </Section>
          )
        })}
      </div>
    </div>
  )
}

/** Thẻ dẫn sang trang Câu hỏi thường gặp — dùng cho cả thẻ mặc định lẫn từng câu hỏi đã chọn. */
function FaqCard({ title, desc }: { title: string; desc?: string }) {
  return (
    <Link
      to="/cau-hoi-thuong-gap"
      className="flex items-center gap-4 rounded-xl bg-surface-soft p-6 shadow-[0_4px_12px_rgba(0,0,0,0.03)] transition-all hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(0,0,0,0.07)]"
    >
      <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-primary/8 text-primary">
        <MessageCircleQuestion className="size-6" strokeWidth={1.75} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-base font-semibold text-ink">{title}</span>
        {desc && (
          <span className="mt-1 block text-sm leading-relaxed text-ink-muted">{desc}</span>
        )}
      </span>
      <ChevronRight className="size-5 shrink-0 text-ink-muted" />
    </Link>
  )
}

/** Thẻ mẹo tra cứu. */
function TipCard({
  Icon, title, desc,
}: {
  Icon: LucideIcon
  title: string
  desc: string
}) {
  return (
    <div className="rounded-xl bg-surface-soft p-6 shadow-[0_4px_12px_rgba(0,0,0,0.03)]">
      <span className="mb-3 grid size-12 place-items-center rounded-xl bg-primary/8 text-primary">
        <Icon className="size-6" strokeWidth={1.75} />
      </span>
      <strong className="block text-base font-semibold text-ink">{title}</strong>
      {desc && <span className="mt-1 block text-sm leading-relaxed text-ink-muted">{desc}</span>}
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

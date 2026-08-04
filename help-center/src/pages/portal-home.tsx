import { Link, useOutletContext } from 'react-router-dom'
import { ArrowRight, BookOpen, Images, MessageCircleQuestion, Search } from 'lucide-react'

import HelpCategoryTiles, { iconOf } from '@/components/help-category-tiles'
import HelpSearchBox from '@/components/help-search-box'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import type { HelpNode } from '@/lib/help-tree'

// Trang chủ khu người dùng — tông tài liệu kỹ thuật: hero phẳng, khối thông tin viền mảnh,
// tiêu đề canh trái, một accent teal duy nhất.

const QUICK_COUNT = 3

/** Duyệt cây theo chiều sâu, lấy các bài viết lá đầu tiên làm lối tắt "bắt đầu nhanh". */
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

  return (
    <>
      {/* Hero phẳng, không gradient rực, không vòm cong */}
      <section className="border-b bg-navy-deep px-6 py-14">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="mb-2 text-[1.75rem] font-bold tracking-tight text-white md:text-[2rem]">
            Trung tâm Hướng dẫn Sử dụng
          </h1>
          <p className="mx-auto mb-7 max-w-xl text-sm text-white/65">
            Nhập tên nghiệp vụ hoặc tính năng của phần mềm để tìm kiếm
          </p>
          <HelpSearchBox size="lg" placeholder="Nhập nội dung tìm kiếm..." />
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-6">
        {/* Lối tắt bắt đầu nhanh */}
        {quick.length > 0 && (
          <Section title="Bắt đầu nhanh" desc="Những bài hay được tra cứu nhất.">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {quick.map((node, i) => {
                const Icon = iconOf(i)
                return (
                  <Link
                    key={node.id}
                    to={`/${node.id}`}
                    className="group flex items-center gap-3 rounded-md border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-secondary"
                  >
                    <span className="grid size-9 shrink-0 place-items-center rounded-md border bg-secondary text-primary">
                      <Icon className="size-[1.125rem]" strokeWidth={1.75} />
                    </span>
                    <span className="min-w-0 flex-1 text-sm font-medium leading-snug text-navy">
                      {node.title}
                    </span>
                    <ArrowRight className="size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                  </Link>
                )
              })}
            </div>
          </Section>
        )}

        {/* Hướng dẫn theo nghiệp vụ */}
        <Section title="Hướng dẫn theo nghiệp vụ" desc="Chọn nhóm nghiệp vụ để xem tài liệu chi tiết.">
          {tree.length > 0 ? (
            <HelpCategoryTiles nodes={tree} />
          ) : (
            <div className="rounded-md border border-dashed px-6 py-12 text-center">
              <BookOpen className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
              <strong className="block text-navy">Chưa có tài liệu nào</strong>
              <span className="text-sm text-muted-foreground">
                Quản trị viên chưa đăng tài liệu hướng dẫn. Vui lòng quay lại sau.
              </span>
            </div>
          )}
        </Section>

        {/* Câu hỏi thường gặp */}
        <Section title="Không tìm thấy điều bạn cần?">
          <Link
            to="/cau-hoi-thuong-gap"
            className="group flex items-center gap-3.5 rounded-md border bg-card p-5 transition-colors hover:border-primary/50 hover:bg-secondary"
          >
            <span className="grid size-9 shrink-0 place-items-center rounded-md border bg-secondary text-primary">
              <MessageCircleQuestion className="size-[1.125rem]" strokeWidth={1.75} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[0.9375rem] font-semibold text-navy">Câu hỏi thường gặp</span>
              <span className="mt-0.5 block text-[0.8125rem] text-muted-foreground">
                Giải đáp nhanh những thắc mắc hay gặp nhất khi dùng hệ thống.
              </span>
            </span>
            <ArrowRight className="size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
          </Link>
        </Section>

        {/* Mẹo tra cứu */}
        <Section title="Mẹo tra cứu" className="pb-16">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {TIPS.map(({ Icon, title, desc }) => (
              <div key={title} className="rounded-md border bg-card p-5">
                <Icon className="mb-2.5 size-[1.125rem] text-primary" strokeWidth={1.75} />
                <strong className="block text-[0.9375rem] font-semibold text-navy">{title}</strong>
                <span className="mt-1 block text-[0.8125rem] leading-relaxed text-muted-foreground">
                  {desc}
                </span>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </>
  )
}

/** Khối nội dung: tiêu đề canh trái + mô tả ngắn, không trang trí. */
function Section({
  title, desc, className = '', children,
}: {
  title: string
  desc?: string
  className?: string
  children: React.ReactNode
}) {
  return (
    <section className={`py-10 ${className}`}>
      <h2 className="text-lg font-bold text-navy">{title}</h2>
      {desc && <p className="mb-5 mt-1 text-sm text-muted-foreground">{desc}</p>}
      {!desc && <div className="mb-5" />}
      {children}
    </section>
  )
}

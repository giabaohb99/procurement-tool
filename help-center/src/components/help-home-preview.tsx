import { BookOpen, Images, MessageCircleQuestion, Search } from 'lucide-react'

import { HOME_SECTION, type HelpHomeSection } from '@/lib/help-home-api'
import { gradientCss, illustrationUrl } from '@/lib/help-home-skins'
import { resolveHelpIcon } from '@/lib/help-icons'
import { findNode, firstLeaves, type HelpNode } from '@/lib/help-tree'

// Bản xem trước trang chủ ở khu quản trị — dựng lại đúng thứ tự khối / tiêu đề / bài viết đang
// cấu hình, thu nhỏ lại cho vừa một cột. CHỈ để nhìn: không link, không cuộn theo trang thật.
//
// Cố ý dựng lại bằng markup rút gọn chứ không tái dùng PortalHome: trang thật cần tree, router,
// slug, trích đoạn nội dung... kéo cả bộ đó vào khu quản trị chỉ để xem trước là quá nặng.
// Đánh đổi: sửa giao diện trang chủ thì phải sửa cả ở đây cho khớp.

const TIP_ICONS = [Search, BookOpen, Images]

export default function HelpHomePreview({
  sections, tree,
}: {
  sections: HelpHomeSection[]
  tree: HelpNode[]
}) {
  const visible = sections.filter((s) => s.is_visible)

  const picked = (key: string) => {
    const section = sections.find((s) => s.key === key)
    return (section?.items ?? [])
      .map((item) => ({ item, node: findNode(tree, item.article_id) }))
      .filter((x): x is { item: (typeof section.items)[number]; node: HelpNode } => !!x.node)
  }

  const quick = picked(HOME_SECTION.QUICK)
  const categories = picked(HOME_SECTION.CATEGORIES)
  const quickNodes = quick.length > 0 ? quick : firstLeaves(tree, 3).map((node) => ({ item: null, node }))
  const categoryNodes = categories.length > 0 ? categories.map((c) => c.node) : tree

  return (
    <div className="overflow-hidden rounded-lg border bg-[linear-gradient(#f0f4ff_0%,#ffffff_120px,#ffffff_100%)]">
      {/* Hero thu nhỏ */}
      <div className="px-4 py-5 text-center">
        <div className="mx-auto mb-3 h-3 w-3/5 rounded-full bg-ink/80" />
        <div className="mx-auto flex h-7 max-w-[15rem] items-center gap-1.5 rounded-full border bg-card px-3">
          <Search className="size-3 text-muted-foreground" />
          <span className="text-[0.625rem] text-muted-foreground">Tìm kiếm tài liệu…</span>
        </div>
      </div>

      <div className="space-y-5 px-4 pb-5">
        {visible.length === 0 && (
          <p className="py-6 text-center text-xs text-muted-foreground">
            Đang ẩn hết các khung — trang chủ sẽ chỉ còn ô tìm kiếm.
          </p>
        )}

        {visible.map((section) => (
          <section key={section.id}>
            <h4 className="mb-2 text-center text-[0.6875rem] font-bold text-ink">{section.title}</h4>

            {section.key === HOME_SECTION.QUICK && (
              // Hiện HẾT, thừa thì tự xuống hàng — cắt bớt ở đây thì xem trước sai với trang thật
              <div className="grid grid-cols-3 gap-1.5">
                {quickNodes.map(({ item, node }, i) => (
                  <div
                    key={node.id}
                    style={{ background: gradientCss(item?.gradient, i) }}
                    className="relative h-16 overflow-hidden rounded-md p-1.5"
                  >
                    <span className="line-clamp-2 text-[0.5625rem] font-semibold leading-tight text-ink">
                      {node.title}
                    </span>
                    <img
                      src={illustrationUrl(item?.background_image, i)}
                      alt="" aria-hidden
                      className="absolute -bottom-1 -right-1 size-8 object-contain"
                    />
                  </div>
                ))}
              </div>
            )}

            {section.key === HOME_SECTION.CATEGORIES && (
              <div className="grid grid-cols-3 gap-1.5">
                {categoryNodes.map((node) => (
                  <div key={node.id} className="rounded-md bg-surface-soft p-1.5">
                    <span className="line-clamp-2 text-[0.5625rem] leading-tight text-ink">
                      {node.title}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {section.key === HOME_SECTION.FAQ && (
              <div className="mx-auto grid max-w-[80%] gap-1">
                {(section.items.length > 0
                  ? section.items.map((i) => i.faq_question || 'Câu hỏi')
                  : ['Câu hỏi thường gặp']
                ).map((label, i) => (
                  <div key={i} className="flex items-center gap-1.5 rounded-md bg-surface-soft p-1.5">
                    <MessageCircleQuestion className="size-3.5 shrink-0 text-primary" strokeWidth={1.75} />
                    <span className="line-clamp-1 text-[0.5625rem] leading-tight text-ink">{label}</span>
                  </div>
                ))}
              </div>
            )}

            {section.key === HOME_SECTION.TIPS && (
              <div className="grid grid-cols-3 gap-1.5">
                {section.items.length > 0
                  ? section.items.map((item, i) => {
                      const Icon = resolveHelpIcon(item.icon, i)
                      return (
                        <div key={item.id} className="rounded-md bg-surface-soft p-1.5">
                          <Icon className="mb-1 size-3.5 text-primary" strokeWidth={1.75} />
                          <span className="line-clamp-2 text-[0.5625rem] leading-tight text-ink">
                            {item.title}
                          </span>
                        </div>
                      )
                    })
                  : TIP_ICONS.map((Icon, i) => (
                      <div key={i} className="rounded-md bg-surface-soft p-1.5">
                        <Icon className="mb-1 size-3.5 text-primary" strokeWidth={1.75} />
                        <span className="block h-1 w-4/5 rounded-full bg-ink/25" />
                      </div>
                    ))}
              </div>
            )}
          </section>
        ))}
      </div>
    </div>
  )
}

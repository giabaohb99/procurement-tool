import { scrollToHeading, type TocItem } from '@/hooks/use-heading-toc'
import { cn } from '@/lib/utils'

// Mục lục bài viết ở cột phải — danh sách thoáng, một đường kẻ dọc chạy dọc mục lục,
// mục đang đọc tô primary kèm vạch đậm (không dùng khung/nền như thẻ).

export default function HelpArticleToc({
  items,
  activeId,
  title = 'Trong bài viết này',
}: {
  items: TocItem[]
  activeId?: string
  title?: string
}) {
  if (items.length === 0) return null

  return (
    <nav aria-label="Mục lục bài viết">
      <h4 className="mb-3 pl-4 text-xs font-bold uppercase tracking-wide text-ink">{title}</h4>
      <ul className="border-l border-hairline">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              onClick={(e) => scrollToHeading(e, item.id)}
              style={{ paddingLeft: (item.level - 1) * 14 + 16 }}
              className={cn(
                '-ml-px block border-l-2 py-2 pr-3 text-sm leading-snug transition-colors',
                item.id === activeId
                  ? 'border-primary font-semibold text-primary'
                  : 'border-transparent text-ink-muted hover:text-primary',
              )}
            >
              {item.text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

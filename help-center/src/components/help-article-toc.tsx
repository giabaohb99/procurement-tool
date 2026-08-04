import { scrollToHeading, type TocItem } from '@/hooks/use-heading-toc'
import { cn } from '@/lib/utils'

// Mục lục bài viết ở cột phải — mục đang đọc tô nền primary.

export default function HelpArticleToc({
  items,
  activeId,
  title = 'Nội dung',
}: {
  items: TocItem[]
  activeId?: string
  title?: string
}) {
  if (items.length === 0) return null

  return (
    <nav aria-label="Mục lục bài viết" className="rounded-md border bg-secondary p-4">
      <h4 className="mb-3 text-sm font-bold text-navy">{title}</h4>
      <ul className="space-y-0.5">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              onClick={(e) => scrollToHeading(e, item.id)}
              style={{ paddingLeft: (item.level - 1) * 14 + 12 }}
              className={cn(
                'block border-l-2 py-1.5 pr-3 text-sm leading-snug transition-colors',
                item.id === activeId
                  ? 'border-primary bg-accent font-semibold text-navy'
                  : 'border-transparent text-slate-600 hover:border-border hover:text-navy',
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
